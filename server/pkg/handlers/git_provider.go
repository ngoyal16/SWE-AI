package handlers

import (
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"strconv"

	"github.com/gin-gonic/gin"
)

// GitProviderInput is the request body for creating/updating a Git provider
type GitProviderInput struct {
	Name               string `json:"name" binding:"required"`
	DisplayName        string `json:"display_name" binding:"required"`
	Driver             string `json:"driver" binding:"required"`
	Enabled            bool   `json:"enabled"`
	AuthType           string `json:"auth_type"`
	ClientID           string `json:"client_id"`
	ClientSecret       string `json:"client_secret"`
	AuthURL            string `json:"auth_url"`
	TokenURL           string `json:"token_url"`
	UserInfoURL        string `json:"user_info_url"`
	Scopes             string `json:"scopes"`
	RedirectURL        string `json:"redirect_url"`
	AppID              string `json:"app_id"`
	AppName            string `json:"app_name"`
	PrivateKey         string `json:"private_key"`
	WebhookSecret      string `json:"webhook_secret"`
	BaseURL            string `json:"base_url"`
	AppUsername        string `json:"app_username"`
	AppEmail           string `json:"app_email"`
	ProjectAccessToken string `json:"project_access_token"`
}

// ListGitProviders returns all git providers
// GET /api/v1/admin/git-providers
func ListGitProviders(c *gin.Context) {
	var providers []model.GitProvider
	if err := model.DB.Find(&providers).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch providers"})
		return
	}

	// Build response with sensitive fields masked
	type ProviderResponse struct {
		ID               uint   `json:"id"`
		Name             string `json:"name"`
		DisplayName      string `json:"display_name"`
		Driver           string `json:"driver"`
		Enabled          bool   `json:"enabled"`
		AuthType         string `json:"auth_type"`
		ClientID         string `json:"client_id"`
		HasClientSecret  bool   `json:"has_client_secret"`
		AuthURL          string `json:"auth_url"`
		TokenURL         string `json:"token_url"`
		UserInfoURL      string `json:"user_info_url"`
		Scopes           string `json:"scopes"`
		RedirectURL      string `json:"redirect_url"`
		AppID            string `json:"app_id"`
		AppName          string `json:"app_name"`
		HasPrivateKey    bool   `json:"has_private_key"`
		HasWebhookSecret bool   `json:"has_webhook_secret"`
		BaseURL          string `json:"base_url"`
		AppUsername      string `json:"app_username"`
		AppEmail         string `json:"app_email"`
		HasProjectToken  bool   `json:"has_project_token"`
	}

	result := make([]ProviderResponse, len(providers))
	for i, p := range providers {
		result[i] = ProviderResponse{
			ID:               p.ID,
			Name:             p.Name,
			DisplayName:      p.DisplayName,
			Driver:           p.Driver,
			Enabled:          p.Enabled,
			AuthType:         p.AuthType,
			ClientID:         p.ClientID,
			HasClientSecret:  p.ClientSecret != "",
			AuthURL:          p.AuthURL,
			TokenURL:         p.TokenURL,
			UserInfoURL:      p.UserInfoURL,
			Scopes:           p.Scopes,
			RedirectURL:      p.RedirectURL,
			AppID:            p.AppID,
			AppName:          p.AppName,
			HasPrivateKey:    p.PrivateKey != "",
			HasWebhookSecret: p.WebhookSecret != "",
			BaseURL:          p.BaseURL,
			AppUsername:      p.AppUsername,
			AppEmail:         p.AppEmail,
			HasProjectToken:  p.ProjectAccessToken != "",
		}
	}

	c.JSON(http.StatusOK, result)
}

// GetGitProvider returns a single git provider by ID
// GET /api/v1/admin/git-providers/:id
func GetGitProvider(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var provider model.GitProvider
	if err := model.DB.First(&provider, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not found"})
		return
	}

	c.JSON(http.StatusOK, provider)
}

// CreateGitProvider creates a new git provider
// POST /api/v1/admin/git-providers
func CreateGitProvider(c *gin.Context) {
	var input GitProviderInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	provider := model.GitProvider{
		Name:               input.Name,
		DisplayName:        input.DisplayName,
		Driver:             input.Driver,
		Enabled:            input.Enabled,
		AuthType:           input.AuthType,
		ClientID:           input.ClientID,
		ClientSecret:       input.ClientSecret, // TODO: Encrypt
		AuthURL:            input.AuthURL,
		TokenURL:           input.TokenURL,
		UserInfoURL:        input.UserInfoURL,
		Scopes:             input.Scopes,
		RedirectURL:        input.RedirectURL,
		AppID:              input.AppID,
		AppName:            input.AppName,
		PrivateKey:         input.PrivateKey,    // TODO: Encrypt
		WebhookSecret:      input.WebhookSecret, // TODO: Encrypt
		BaseURL:            input.BaseURL,
		AppUsername:        input.AppUsername,
		AppEmail:           input.AppEmail,
		ProjectAccessToken: input.ProjectAccessToken, // TODO: Encrypt
	}

	// Auto-generate RedirectURL
	provider.RedirectURL = provider.ComputeRedirectURL()

	if err := model.DB.Create(&provider).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create provider"})
		return
	}

	c.JSON(http.StatusCreated, provider)
}

// UpdateGitProvider updates an existing git provider
// PUT /api/v1/admin/git-providers/:id
func UpdateGitProvider(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var provider model.GitProvider
	if err := model.DB.First(&provider, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not found"})
		return
	}

	var input GitProviderInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Update fields
	provider.Name = input.Name
	provider.DisplayName = input.DisplayName
	provider.Driver = input.Driver
	provider.Enabled = input.Enabled
	provider.AuthType = input.AuthType
	provider.ClientID = input.ClientID
	provider.AuthURL = input.AuthURL
	provider.TokenURL = input.TokenURL
	provider.UserInfoURL = input.UserInfoURL
	provider.Scopes = input.Scopes
	provider.AppID = input.AppID
	provider.AppName = input.AppName
	provider.BaseURL = input.BaseURL
	provider.AppUsername = input.AppUsername
	provider.AppEmail = input.AppEmail

	// Auto-generate RedirectURL
	provider.RedirectURL = provider.ComputeRedirectURL()

	// Only update secrets if provided (non-empty)
	if input.ClientSecret != "" {
		provider.ClientSecret = input.ClientSecret // TODO: Encrypt
	}
	if input.PrivateKey != "" {
		provider.PrivateKey = input.PrivateKey // TODO: Encrypt
	}
	if input.WebhookSecret != "" {
		provider.WebhookSecret = input.WebhookSecret // TODO: Encrypt
	}
	if input.ProjectAccessToken != "" {
		provider.ProjectAccessToken = input.ProjectAccessToken // TODO: Encrypt
	}

	if err := model.DB.Save(&provider).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update provider"})
		return
	}

	c.JSON(http.StatusOK, provider)
}

// DeleteGitProvider deletes a git provider
// DELETE /api/v1/admin/git-providers/:id
func DeleteGitProvider(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var provider model.GitProvider
	if err := model.DB.First(&provider, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not found"})
		return
	}

	if err := model.DB.Delete(&provider).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete provider"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Provider deleted successfully"})
}

// ToggleGitProvider enables or disables a git provider
// PATCH /api/v1/admin/git-providers/:id/toggle
func ToggleGitProvider(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}

	var provider model.GitProvider
	if err := model.DB.First(&provider, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not found"})
		return
	}

	provider.Enabled = !provider.Enabled
	if err := model.DB.Save(&provider).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to toggle provider"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      provider.ID,
		"enabled": provider.Enabled,
		"message": "Provider toggled successfully",
	})
}
