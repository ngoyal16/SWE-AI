package handlers

import (
	"log"
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"pixcorp-swe-ai/pkg/services"
	"strings"

	"github.com/gin-gonic/gin"
)

// CreatePullRequest creates a PR for the session
// POST /api/v1/internal/sessions/:session_id/pr
func CreatePullRequest(c *gin.Context) {
	sessionID := c.Param("session_id")
	log.Printf("[PR] Request received for session: %s", sessionID)

	// Validate worker token
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
		return
	}
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
		return
	}
	workerToken := parts[1]

	var session model.Session
	if err := model.DB.Where("session_id = ? AND worker_token = ?", sessionID, workerToken).First(&session).Error; err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid worker token"})
		return
	}

	var input services.PullRequestInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body: " + err.Error()})
		return
	}

	// Validate input
	if input.Title == "" || input.Head == "" || input.Base == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required fields (title, head, base)"})
		return
	}

	resp, err := services.CreatePullRequest(sessionID, input)
	if err != nil {
		log.Printf("[PR] Failed to create PR: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, resp)
}
