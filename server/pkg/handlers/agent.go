package handlers

import (
	"fmt"
	"math/rand"
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"pixcorp-swe-ai/pkg/services"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

type SessionRequest struct {
	Goal         string  `json:"goal" binding:"required"`
	RepoURL      string  `json:"repo_url"`
	RepositoryID uint    `json:"repository_id"`
	BaseBranch   *string `json:"base_branch"`
	Mode         string  `json:"mode"` // "auto" or "review"
}

type InputRequest struct {
	Message string `json:"message" binding:"required"`
}

func CreateSession(c *gin.Context) {
	var req SessionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID := c.GetUint("user_id")

	if req.Mode == "" {
		req.Mode = "auto"
	}

	// Generate session ID (18-19 digits)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	sessionID := fmt.Sprintf("%d", r.Int63n(9223372036854775807-100000000000000000)+100000000000000000)

	// Store in DB
	baseBranch := ""
	if req.BaseBranch != nil {
		baseBranch = *req.BaseBranch
	}

	// Generate title from goal
	title := req.Goal
	if len(title) > 50 {
		title = title[:47] + "..."
	}

	session := model.Session{
		UserID:       userID,
		SessionID:    sessionID,
		Title:        title,
		RepositoryID: req.RepositoryID,
		BaseBranch:   baseBranch,
		Goal:         req.Goal,
		Status:       "QUEUED",
	}

	if err := model.DB.Create(&session).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create session record"})
		return
	}

	err := services.SetSessionStatus(sessionID, "QUEUED")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to set status"})
		return
	}

	err = services.EnqueueTask(services.TaskPayload{
		SessionID:   sessionID,
		Goal:        req.Goal,
		RepoURL:     req.RepoURL,
		BaseBranch:  req.BaseBranch,
		Mode:        req.Mode,
		WorkerToken: session.WorkerToken,
	})

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to enqueue task"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"session_id": sessionID})
}

func ApproveSession(c *gin.Context) {
	sessionID := c.Param("session_id")
	state, err := services.GetState(sessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Session not found"})
		return
	}

	if status, ok := state["status"].(string); !ok || status != "WAITING_FOR_USER" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Session cannot be resumed"})
		return
	}

	// Update status
	if nextStatus, ok := state["next_status"].(string); ok {
		state["status"] = nextStatus
		delete(state, "next_status")
	} else {
		state["status"] = "CODING"
	}

	err = services.SaveState(sessionID, state)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save state"})
		return
	}

	services.SetSessionStatus(sessionID, "QUEUED")

	// Fetch session to get worker token
	var session model.Session
	if err := model.DB.Where("session_id = ?", sessionID).First(&session).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Session not found in database"})
		return
	}

	// Re-enqueue (co-author info is now fetched dynamically by the worker)
	goal, _ := state["goal"].(string)
	repoURL, _ := state["repo_url"].(string)
	mode, _ := state["mode"].(string)

	var baseBranch *string
	if bb, ok := state["base_branch"].(string); ok {
		baseBranch = &bb
	}

	services.EnqueueTask(services.TaskPayload{
		SessionID:   sessionID,
		Goal:        goal,
		RepoURL:     repoURL,
		BaseBranch:  baseBranch,
		Mode:        mode,
		WorkerToken: session.WorkerToken,
	})

	c.JSON(http.StatusOK, gin.H{"status": "resumed"})
}

func AddSessionInput(c *gin.Context) {
	sessionID := c.Param("session_id")
	var req InputRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	state, err := services.GetState(sessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Session not found"})
		return
	}

	// Initialize pending_inputs
	var pendingInputs []string
	if pi, ok := state["pending_inputs"].([]interface{}); ok {
		for _, v := range pi {
			if s, ok := v.(string); ok {
				pendingInputs = append(pendingInputs, s)
			}
		}
	}
	pendingInputs = append(pendingInputs, req.Message)
	state["pending_inputs"] = pendingInputs

	status, _ := state["status"].(string)
	if status == "WAITING_FOR_USER" || status == "COMPLETED" {
		userInput := fmt.Sprintf("\n\n[User Input]: %s", req.Message)
		goal, _ := state["goal"].(string)
		state["goal"] = goal + userInput
		state["status"] = "PLANNING"
		state["pending_inputs"] = []string{}

		services.SaveState(sessionID, state)
		services.SetSessionStatus(sessionID, "QUEUED")

		// Fetch session to get worker token
		var session model.Session
		if err := model.DB.Where("session_id = ?", sessionID).First(&session).Error; err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Session not found in database"})
			return
		}

		repoURL, _ := state["repo_url"].(string)
		mode, _ := state["mode"].(string)
		var baseBranch *string
		if bb, ok := state["base_branch"].(string); ok {
			baseBranch = &bb
		}

		services.EnqueueTask(services.TaskPayload{
			SessionID:   sessionID,
			Goal:        state["goal"].(string),
			RepoURL:     repoURL,
			BaseBranch:  baseBranch,
			Mode:        mode,
			WorkerToken: session.WorkerToken,
		})
	} else {
		services.SaveState(sessionID, state)
	}

	c.JSON(http.StatusOK, gin.H{"status": "input_added"})
}

func GetSessionStatus(c *gin.Context) {
	sessionID := c.Param("session_id")
	status, err := services.GetSessionStatus(sessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Session not found"})
		return
	}

	logs, _ := services.GetLogs(sessionID)
	result, _ := services.GetResult(sessionID)
	state, _ := services.GetState(sessionID)

	// Lazy sync to DB to ensure persistent record matches Redis
	services.SyncSessionToDB(sessionID, status, state)

	c.JSON(http.StatusOK, gin.H{
		"id":     sessionID,
		"status": status,
		"logs":   logs,
		"result": result,
		"state":  state,
	})
}

func ListUserSessions(c *gin.Context) {
	userIDVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}
	userID := userIDVal.(uint)

	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	perPage, _ := strconv.Atoi(c.DefaultQuery("per_page", "20"))
	status := c.Query("status")

	if page < 1 {
		page = 1
	}
	if perPage < 1 || perPage > 100 {
		perPage = 20
	}
	offset := (page - 1) * perPage

	query := model.DB.Model(&model.Session{}).
		Preload("Repository").
		Where("user_id = ?", userID)

	if status != "" {
		query = query.Where("status = ?", status)
	}

	var total int64
	query.Count(&total)

	var sessions []model.Session
	err := query.
		Limit(perPage).
		Offset(offset).
		Order("updated_at DESC").
		Find(&sessions).Error

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch sessions"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data": sessions,
		"meta": gin.H{
			"total":    total,
			"page":     page,
			"per_page": perPage,
		},
	})
}

func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}
