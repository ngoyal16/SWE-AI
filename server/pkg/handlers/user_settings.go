package handlers

import (
	"net/http"
	"pixcorp-swe-ai/pkg/model"

	"github.com/gin-gonic/gin"
)

type UserAIPreferenceInput struct {
	AIProfileID uint `json:"ai_profile_id" binding:"required"`
}

func GetUserAIPreference(c *gin.Context) {
	userIDVal, _ := c.Get("user_id")
	userID := userIDVal.(uint)

	var preference model.UserAIPreference
	err := model.DB.Preload("AIProfile").Where("user_id = ?", userID).First(&preference).Error
	if err != nil {
		// If not found, return empty or default
		c.JSON(http.StatusOK, gin.H{"ai_profile_id": 0})
		return
	}

	c.JSON(http.StatusOK, preference)
}

func UpsertUserAIPreference(c *gin.Context) {
	userIDVal, _ := c.Get("user_id")
	userID := userIDVal.(uint)

	var input UserAIPreferenceInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Verify profile exists and is enabled
	var profile model.AIProfile
	if err := model.DB.First(&profile, input.AIProfileID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "AI profile not found"})
		return
	}
	if !profile.IsEnabled {
		c.JSON(http.StatusBadRequest, gin.H{"error": "AI profile is disabled"})
		return
	}

	var preference model.UserAIPreference
	err := model.DB.Where("user_id = ?", userID).First(&preference).Error

	preference.UserID = userID
	preference.AIProfileID = input.AIProfileID

	if err != nil {
		// Create new
		if err := model.DB.Create(&preference).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save preference"})
			return
		}
	} else {
		// Update existing
		if err := model.DB.Save(&preference).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update preference"})
			return
		}
	}

	c.JSON(http.StatusOK, preference)
}
