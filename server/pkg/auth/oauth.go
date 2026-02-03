package auth

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"pixcorp-swe-ai/pkg/model"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog/log"
)

// OAuthHandler handles OAuth authentication for Git providers
type OAuthHandler struct{}

// NewOAuthHandler creates a new OAuth handler
func NewOAuthHandler() *OAuthHandler {
	return &OAuthHandler{}
}

// OAuthState represents the state stored during OAuth flow
type OAuthState struct {
	Provider  string `json:"provider"`
	ReturnURL string `json:"return_url"`
	Nonce     string `json:"nonce"`
	UserID    uint   `json:"user_id,omitempty"` // Set when linking account (user already logged in)
}

// GitHubUser represents a GitHub user from the API
type GitHubUser struct {
	ID        int64  `json:"id"`
	Login     string `json:"login"`
	Name      string `json:"name"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatar_url"`
}

// GitLabUser represents a GitLab user from the API
type GitLabUser struct {
	ID        int64  `json:"id"`
	Username  string `json:"username"`
	Name      string `json:"name"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatar_url"`
}

// BitbucketUser represents a Bitbucket user from the API
type BitbucketUser struct {
	UUID        string `json:"uuid"`
	Username    string `json:"username"`
	DisplayName string `json:"display_name"`
	Links       struct {
		Avatar struct {
			Href string `json:"href"`
		} `json:"avatar"`
	} `json:"links"`
}

// generateState creates a secure random state for OAuth
func generateState(provider, returnURL string, userID uint) (string, error) {
	nonce := make([]byte, 32)
	if _, err := rand.Read(nonce); err != nil {
		return "", err
	}

	state := OAuthState{
		Provider:  provider,
		ReturnURL: returnURL,
		Nonce:     base64.URLEncoding.EncodeToString(nonce),
		UserID:    userID,
	}

	stateJSON, err := json.Marshal(state)
	if err != nil {
		return "", err
	}

	return base64.URLEncoding.EncodeToString(stateJSON), nil
}

// parseState decodes the OAuth state
func parseState(stateStr string) (*OAuthState, error) {
	stateJSON, err := base64.URLEncoding.DecodeString(stateStr)
	if err != nil {
		return nil, err
	}

	var state OAuthState
	if err := json.Unmarshal(stateJSON, &state); err != nil {
		return nil, err
	}

	return &state, nil
}

// InitiateOAuth starts the OAuth flow for a Git provider
// GET /api/auth/oauth/:provider
// This route is protected - user must be logged in to link accounts
func (h *OAuthHandler) InitiateOAuth(c *gin.Context) {
	providerName := c.Param("provider")
	returnURL := c.DefaultQuery("return_url", "/settings")

	// Get current logged-in user from context (set by RequireAuth middleware)
	userIDVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}
	userID := userIDVal.(uint)

	// Find the provider in database
	var provider model.GitProvider
	if err := model.DB.Where("name = ? AND enabled = ?", providerName, true).First(&provider).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not found or not enabled"})
		return
	}

	// Generate state with user ID
	state, err := generateState(providerName, returnURL, userID)
	if err != nil {
		log.Error().Err(err).Msg("Failed to generate OAuth state")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to initiate OAuth"})
		return
	}

	// Store state in Redis with 10 minute expiration
	if err := model.Rdb.Set(c.Request.Context(), "oauth_state:"+state, providerName, 10*time.Minute).Err(); err != nil {
		log.Error().Err(err).Msg("Failed to store OAuth state")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to initiate OAuth"})
		return
	}

	// Build OAuth URL
	oauth2Config := provider.GetOAuthConfig()
	authURL := oauth2Config.AuthCodeURL(state)

	c.Redirect(http.StatusTemporaryRedirect, authURL)
}

// HandleOAuthCallback handles the OAuth callback from providers
// GET /api/auth/oauth/:provider/callback
func (h *OAuthHandler) HandleOAuthCallback(c *gin.Context) {
	providerName := c.Param("provider")
	code := c.Query("code")
	stateStr := c.Query("state")

	if code == "" {
		errorDesc := c.Query("error_description")
		if errorDesc == "" {
			errorDesc = c.Query("error")
		}
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error="+errorDesc)
		return
	}

	// Validate state
	storedProvider, err := model.Rdb.Get(c.Request.Context(), "oauth_state:"+stateStr).Result()
	if err != nil {
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=Invalid or expired OAuth state")
		return
	}

	if storedProvider != providerName {
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=OAuth state mismatch")
		return
	}

	// Delete state after use
	model.Rdb.Del(c.Request.Context(), "oauth_state:"+stateStr)

	// Parse state for return URL and user ID
	state, err := parseState(stateStr)
	if err != nil {
		log.Warn().Err(err).Msg("Failed to parse OAuth state")
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=Invalid OAuth state")
		return
	}

	// Find the provider
	var provider model.GitProvider
	if err := model.DB.Where("name = ?", providerName).First(&provider).Error; err != nil {
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=Provider not found")
		return
	}

	// Exchange code for token
	oauth2Config := provider.GetOAuthConfig()
	token, err := oauth2Config.Exchange(c.Request.Context(), code)
	if err != nil {
		log.Error().Err(err).Msg("Failed to exchange OAuth code")
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=Failed to complete OAuth")
		return
	}

	// Fetch user info from provider
	userInfo, err := h.fetchUserInfo(c.Request.Context(), &provider, token.AccessToken)
	if err != nil {
		log.Error().Err(err).Msg("Failed to fetch user info")
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=Failed to fetch user info")
		return
	}

	// Link identity to logged-in user
	if state.UserID == 0 {
		// This shouldn't happen since InitiateOAuth is now protected
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error=User not authenticated")
		return
	}

	err = h.linkIdentityToUser(state.UserID, userInfo, &provider, token.AccessToken)
	if err != nil {
		log.Error().Err(err).Msg("Failed to link identity")
		c.Redirect(http.StatusTemporaryRedirect, "/settings?error="+err.Error())
		return
	}

	// Redirect back to settings
	c.Redirect(http.StatusTemporaryRedirect, state.ReturnURL+"?linked="+providerName)
}

// ProviderUserInfo holds normalized user info from any provider
type ProviderUserInfo struct {
	ProviderID string
	Username   string
	Email      string
	Name       string
	AvatarURL  string
}

// fetchUserInfo fetches user information from the Git provider
func (h *OAuthHandler) fetchUserInfo(ctx context.Context, provider *model.GitProvider, accessToken string) (*ProviderUserInfo, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", provider.UserInfoURL, nil)
	if err != nil {
		return nil, err
	}

	// Set appropriate auth header based on provider
	switch provider.Driver {
	case "github":
		req.Header.Set("Authorization", "Bearer "+accessToken)
		req.Header.Set("Accept", "application/vnd.github+json")
	case "gitlab":
		req.Header.Set("Authorization", "Bearer "+accessToken)
	case "bitbucket":
		req.Header.Set("Authorization", "Bearer "+accessToken)
	}

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to fetch user info: %s - %s", resp.Status, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	// Parse based on provider
	switch provider.Driver {
	case "github":
		var user GitHubUser
		if err := json.Unmarshal(body, &user); err != nil {
			return nil, err
		}
		return &ProviderUserInfo{
			ProviderID: fmt.Sprintf("%d", user.ID),
			Username:   user.Login,
			Email:      user.Email,
			Name:       user.Name,
			AvatarURL:  user.AvatarURL,
		}, nil

	case "gitlab":
		var user GitLabUser
		if err := json.Unmarshal(body, &user); err != nil {
			return nil, err
		}
		return &ProviderUserInfo{
			ProviderID: fmt.Sprintf("%d", user.ID),
			Username:   user.Username,
			Email:      user.Email,
			Name:       user.Name,
			AvatarURL:  user.AvatarURL,
		}, nil

	case "bitbucket":
		var user BitbucketUser
		if err := json.Unmarshal(body, &user); err != nil {
			return nil, err
		}
		return &ProviderUserInfo{
			ProviderID: user.UUID,
			Username:   user.Username,
			Email:      "", // Bitbucket requires separate API call for email
			Name:       user.DisplayName,
			AvatarURL:  user.Links.Avatar.Href,
		}, nil

	default:
		return nil, fmt.Errorf("unsupported provider driver: %s", provider.Driver)
	}
}

// linkIdentityToUser links a Git provider identity to an existing user
func (h *OAuthHandler) linkIdentityToUser(userID uint, info *ProviderUserInfo, provider *model.GitProvider, accessToken string) error {
	// Check if identity already exists for another user
	var existingIdentity model.UserIdentity
	err := model.DB.Where("provider = ? AND provider_id = ?", provider.Name, info.ProviderID).First(&existingIdentity).Error
	if err == nil {
		if existingIdentity.UserID != userID {
			return fmt.Errorf("this %s account is already linked to another user", provider.DisplayName)
		}
		// Identity already linked to this user, update token and info
		existingIdentity.Token = accessToken // TODO: Encrypt this
		existingIdentity.Email = info.Email
		existingIdentity.Username = info.Username
		existingIdentity.Name = info.Name
		return model.DB.Save(&existingIdentity).Error
	}

	// Check if user already has an identity for this provider
	var userExistingIdentity model.UserIdentity
	if err := model.DB.Where("user_id = ? AND provider = ?", userID, provider.Name).First(&userExistingIdentity).Error; err == nil {
		// User already has this provider linked, update it
		userExistingIdentity.ProviderID = info.ProviderID
		userExistingIdentity.Email = info.Email
		userExistingIdentity.Username = info.Username
		userExistingIdentity.Name = info.Name
		userExistingIdentity.Token = accessToken // TODO: Encrypt this
		return model.DB.Save(&userExistingIdentity).Error
	}

	// Create new identity
	identity := model.UserIdentity{
		UserID:     userID,
		Provider:   provider.Name,
		ProviderID: info.ProviderID,
		Username:   info.Username,
		Name:       info.Name,
		Email:      info.Email,
		Token:      accessToken, // TODO: Encrypt this
	}
	return model.DB.Create(&identity).Error
}

// GetProviders returns all enabled Git providers for the settings page
// GET /api/auth/providers
func (h *OAuthHandler) GetProviders(c *gin.Context) {
	var providers []model.GitProvider
	if err := model.DB.Where("enabled = ?", true).Find(&providers).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch providers"})
		return
	}

	// Return only necessary info (strip secrets)
	type ProviderInfo struct {
		Name        string `json:"name"`
		DisplayName string `json:"display_name"`
		Driver      string `json:"driver"`
		AuthType    string `json:"auth_type"`
	}

	result := make([]ProviderInfo, len(providers))
	for i, p := range providers {
		result[i] = ProviderInfo{
			Name:        p.Name,
			DisplayName: p.DisplayName,
			Driver:      p.Driver,
			AuthType:    p.AuthType,
		}
	}

	c.JSON(http.StatusOK, result)
}

// GetUserIdentities returns the current user's linked Git provider identities
// GET /api/auth/identities (protected)
func (h *OAuthHandler) GetUserIdentities(c *gin.Context) {
	userIDVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}
	userID := userIDVal.(uint)

	var identities []model.UserIdentity
	if err := model.DB.Where("user_id = ?", userID).Find(&identities).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch identities"})
		return
	}

	// Return safe info (strip tokens)
	type IdentityInfo struct {
		ID         uint   `json:"id"`
		Provider   string `json:"provider"`
		ProviderID string `json:"provider_id"`
		Email      string `json:"email"`
	}

	result := make([]IdentityInfo, len(identities))
	for i, id := range identities {
		result[i] = IdentityInfo{
			ID:         id.ID,
			Provider:   id.Provider,
			ProviderID: id.ProviderID,
			Email:      id.Email,
		}
	}

	c.JSON(http.StatusOK, result)
}

// UnlinkProvider removes a Git provider identity from the user
// DELETE /api/auth/identities/:provider (protected)
func (h *OAuthHandler) UnlinkProvider(c *gin.Context) {
	providerName := c.Param("provider")

	userIDVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}
	userID := userIDVal.(uint)

	result := model.DB.Where("user_id = ? AND provider = ?", userID, providerName).Delete(&model.UserIdentity{})
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to unlink provider"})
		return
	}

	if result.RowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Provider not linked"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Provider unlinked successfully"})
}
