package model

import "fmt"

type AIProfile struct {
	Model
	Name         string `json:"name" gorm:"type:varchar(100);not null"`
	Provider     string `json:"provider" gorm:"type:varchar(50);not null"` // gemini, openai, anthropic, azure, etc.
	APIKey       string `json:"-" gorm:"type:text"`                        // Secret, encrypted
	BaseURL      string `json:"base_url" gorm:"type:varchar(255)"`
	DefaultModel string `json:"default_model" gorm:"type:varchar(100)"`
	IsEnabled    bool   `json:"is_enabled" gorm:"default:true"`
	IsDefault    bool   `json:"is_default" gorm:"default:false"` // System-wide default
}

func (AIProfile) TableName() string {
	return "ai_profiles"
}

type UserAIPreference struct {
	Model
	UserID      uint `json:"user_id" gorm:"uniqueIndex"`
	AIProfileID uint `json:"ai_profile_id"`

	User      User      `json:"-" gorm:"foreignKey:UserID"`
	AIProfile AIProfile `json:"ai_profile" gorm:"foreignKey:AIProfileID"`
}

func (UserAIPreference) TableName() string {
	return "user_ai_preferences"
}

// SeedInitialAIProfiles creates default AI profiles if they don't exist
func SeedInitialAIProfiles() error {
	var count int64
	DB.Model(&AIProfile{}).Count(&count)
	if count > 0 {
		return nil
	}

	profiles := []AIProfile{
		{
			Name:         "Gemini 1.5 Pro (Default)",
			Provider:     "gemini",
			DefaultModel: "gemini-1.5-pro",
			IsEnabled:    true,
			IsDefault:    true,
		},
		{
			Name:         "Gemini 1.5 Flash",
			Provider:     "gemini",
			DefaultModel: "gemini-1.5-flash",
			IsEnabled:    true,
			IsDefault:    false,
		},
	}

	for _, p := range profiles {
		if err := DB.Create(&p).Error; err != nil {
			return fmt.Errorf("failed to create default AI profile %s: %w", p.Name, err)
		}
	}

	return nil
}
