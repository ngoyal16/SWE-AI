package handlers

import (
	"log"
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"pixcorp-swe-ai/pkg/services"
	"strings"

	"github.com/gin-gonic/gin"
)

// GetAICredentials returns AI credentials for a session
// GET /api/v1/internal/sessions/:session_id/ai-credentials
// This is an internal endpoint for the agent worker, authenticated via worker token
func GetAICredentials(c *gin.Context) {
	sessionID := c.Param("session_id")
	log.Printf("[AICredentials] Request received for session: %s", sessionID)

	// Validate worker token from Authorization header
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" {
		log.Printf("[AICredentials] Missing Authorization header for session: %s", sessionID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
		return
	}

	// Expect "Bearer <token>" format
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		log.Printf("[AICredentials] Invalid authorization format for session: %s", sessionID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
		return
	}
	workerToken := parts[1]

	// Verify the token matches the session's worker token
	var session model.Session
	if err := model.DB.Where("session_id = ? AND worker_token = ?", sessionID, workerToken).First(&session).Error; err != nil {
		log.Printf("[AICredentials] Invalid worker token for session: %s - error: %v", sessionID, err)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid worker token"})
		return
	}

	log.Printf("[AICredentials] Worker token validated for session: %s", sessionID)

	credentials, err := services.GetAICredentialsForSession(sessionID)
	if err != nil {
		log.Printf("[AICredentials] Failed to get credentials for session %s: %v", sessionID, err)
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	log.Printf("[AICredentials] Successfully returning AI credentials for session: %s", sessionID)
	c.JSON(http.StatusOK, credentials)
}
