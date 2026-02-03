package services

import (
	"fmt"
	"log"
	"pixcorp-swe-ai/pkg/model"
)

// AICredentials contains the credentials needed for AI operations
type AICredentials struct {
	Provider string `json:"provider"`
	Model    string `json:"model"`
	APIKey   string `json:"api_key"`
	BaseURL  string `json:"base_url,omitempty"`
}

// GetAICredentialsForSession fetches AI credentials for a session
// Looks up session -> user -> user_ai_preference -> ai_profile
func GetAICredentialsForSession(sessionID string) (*AICredentials, error) {
	log.Printf("[AICredentials] Fetching credentials for session: %s", sessionID)

	var session model.Session
	err := model.DB.
		Where("session_id = ?", sessionID).
		First(&session).Error
	if err != nil {
		log.Printf("[AICredentials] Session not found: %s - error: %v", sessionID, err)
		return nil, fmt.Errorf("session not found: %w", err)
	}

	// Fetch User AI Preference
	var userAIPreference model.UserAIPreference
	err = model.DB.
		Preload("AIProfile").
		Where("user_id = ?", session.UserID).
		First(&userAIPreference).Error

	var aiProfile model.AIProfile

	if err == nil {
		aiProfile = userAIPreference.AIProfile
		log.Printf("[AICredentials] Found user preference: %s (%s)", aiProfile.Name, aiProfile.Provider)
	} else {
		// Fallback to default system profile
		log.Printf("[AICredentials] No user preference found, looking for default profile")
		err = model.DB.Where("is_default = ? AND is_enabled = ?", true, true).First(&aiProfile).Error
		if err != nil {
			log.Printf("[AICredentials] No default profile found: %v", err)
			return nil, fmt.Errorf("no AI profile configured")
		}
		log.Printf("[AICredentials] Using default profile: %s (%s)", aiProfile.Name, aiProfile.Provider)
	}

	// TODO: Decrypt API Key if encrypted
	return &AICredentials{
		Provider: aiProfile.Provider,
		Model:    aiProfile.DefaultModel,
		APIKey:   aiProfile.APIKey,
		BaseURL:  aiProfile.BaseURL,
	}, nil
}
