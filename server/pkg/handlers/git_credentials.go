package handlers

import (
	"log"
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"pixcorp-swe-ai/pkg/services"
	"strings"

	"github.com/gin-gonic/gin"
)

// GetGitCredentials returns Git credentials for a session
// GET /api/v1/internal/sessions/:session_id/git-credentials
// This is an internal endpoint for the agent worker, authenticated via worker token
func GetGitCredentials(c *gin.Context) {
	sessionID := c.Param("session_id")
	log.Printf("[GitCredentials] Request received for session: %s", sessionID)

	// Validate worker token from Authorization header
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" {
		log.Printf("[GitCredentials] Missing Authorization header for session: %s", sessionID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
		return
	}

	// Expect "Bearer <token>" format
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		log.Printf("[GitCredentials] Invalid authorization format for session: %s", sessionID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
		return
	}
	workerToken := parts[1]

	// Verify the token matches the session's worker token
	var session model.Session
	if err := model.DB.Where("session_id = ? AND worker_token = ?", sessionID, workerToken).First(&session).Error; err != nil {
		log.Printf("[GitCredentials] Invalid worker token for session: %s - error: %v", sessionID, err)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid worker token"})
		return
	}

	log.Printf("[GitCredentials] Worker token validated for session: %s", sessionID)

	credentials, err := services.GetCredentialsForSession(sessionID)
	if err != nil {
		log.Printf("[GitCredentials] Failed to get credentials for session %s: %v", sessionID, err)
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	log.Printf("[GitCredentials] Successfully returning credentials for session: %s", sessionID)
	c.JSON(http.StatusOK, credentials)
}
