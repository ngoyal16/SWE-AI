package handlers

import (
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"strconv"

	"github.com/gin-gonic/gin"
)

type AIProfileInput struct {
	Name         string `json:"name" binding:"required"`
	Provider     string `json:"provider" binding:"required"`
	APIKey       string `json:"api_key"` // Optional if already set
	BaseURL      string `json:"base_url"`
	DefaultModel string `json:"default_model"`
	IsEnabled    bool   `json:"is_enabled"`
}

func ListAIProfiles(c *gin.Context) {
	var profiles []model.AIProfile
	if err := model.DB.Find(&profiles).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch AI profiles"})
		return
	}
	c.JSON(http.StatusOK, profiles)
}

func GetAIProfile(c *gin.Context) {
	id := c.Param("id")
	var profile model.AIProfile
	if err := model.DB.First(&profile, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "AI profile not found"})
		return
	}
	c.JSON(http.StatusOK, profile)
}

func CreateAIProfile(c *gin.Context) {
	var input AIProfileInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	profile := model.AIProfile{
		Name:         input.Name,
		Provider:     input.Provider,
		APIKey:       input.APIKey, // Note: In a real app, encrypt this
		BaseURL:      input.BaseURL,
		DefaultModel: input.DefaultModel,
		IsEnabled:    input.IsEnabled,
	}

	if err := model.DB.Create(&profile).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create AI profile"})
		return
	}

	c.JSON(http.StatusCreated, profile)
}

func UpdateAIProfile(c *gin.Context) {
	idStr := c.Param("id")
	id, _ := strconv.Atoi(idStr)

	var input AIProfileInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var profile model.AIProfile
	if err := model.DB.First(&profile, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "AI profile not found"})
		return
	}

	profile.Name = input.Name
	profile.Provider = input.Provider
	if input.APIKey != "" {
		profile.APIKey = input.APIKey
	}
	profile.BaseURL = input.BaseURL
	profile.DefaultModel = input.DefaultModel
	profile.IsEnabled = input.IsEnabled

	if err := model.DB.Save(&profile).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update AI profile"})
		return
	}

	c.JSON(http.StatusOK, profile)
}

func ToggleAIProfile(c *gin.Context) {
	id := c.Param("id")
	var profile model.AIProfile
	if err := model.DB.First(&profile, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "AI profile not found"})
		return
	}

	profile.IsEnabled = !profile.IsEnabled
	if err := model.DB.Save(&profile).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to toggle AI profile"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      profile.ID,
		"enabled": profile.IsEnabled,
		"message": "AI profile status updated",
	})
}

func DeleteAIProfile(c *gin.Context) {
	id := c.Param("id")
	if err := model.DB.Delete(&model.AIProfile{}, id).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete AI profile"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "AI profile deleted"})
}
