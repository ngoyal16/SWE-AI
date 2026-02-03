package model

import (
	"fmt"
	"pixcorp-swe-ai/pkg/common"
	"strings"

	"golang.org/x/oauth2"
)

// GitProvider represents a Git provider configuration (GitHub, GitLab, Bitbucket)
// It supports multiple authentication types:
//   - OAuth 2.0: Standard OAuth flow for user authentication
//   - GitHub App: GitHub-specific app authentication with installation tokens
type GitProvider struct {
	Model
	Name        string `json:"name" gorm:"type:varchar(50);uniqueIndex;not null"` // Programmable slug: github, gitlab, gitlab-internal
	DisplayName string `json:"display_name" gorm:"type:varchar(100)"`             // UI Name: GitHub, GitLab, Company GitLab
	Driver      string `json:"driver" gorm:"type:varchar(50);not null"`           // Logic driver: github, gitlab, bitbucket
	Enabled     bool   `json:"enabled" gorm:"default:false"`

	// Authentication Type: "oauth" or "github_app"
	AuthType string `json:"auth_type" gorm:"type:varchar(20);default:'oauth'"`

	// ============================================
	// OAuth 2.0 Configuration (all providers)
	// ============================================
	ClientID     string `json:"client_id" gorm:"type:varchar(255)"`
	ClientSecret string `json:"-" gorm:"type:varchar(255)"` // Encrypted, hidden from JSON
	AuthURL      string `json:"auth_url" gorm:"type:varchar(500)"`
	TokenURL     string `json:"token_url" gorm:"type:varchar(500)"`
	UserInfoURL  string `json:"user_info_url" gorm:"type:varchar(500)"`
	Scopes       string `json:"scopes" gorm:"type:varchar(500)"`
	RedirectURL  string `json:"redirect_url" gorm:"type:varchar(500)"`

	// ============================================
	// GitHub App Specific Configuration
	// ============================================
	// AppID is the GitHub App ID (found in GitHub App settings)
	AppID string `json:"app_id" gorm:"type:varchar(50)"`

	// AppName is the GitHub App name (must match exactly, no spaces)
	AppName string `json:"app_name" gorm:"type:varchar(100)"`

	// PrivateKey is the GitHub App private key (PEM format, encrypted)
	// Used to generate installation tokens
	PrivateKey string `json:"-" gorm:"type:text"` // Encrypted, hidden from JSON

	// WebhookSecret is the secret for validating GitHub webhooks
	WebhookSecret string `json:"-" gorm:"type:varchar(255)"` // Encrypted, hidden from JSON

	// ============================================
	// GitLab Specific Configuration (self-hosted support)
	// ============================================
	// BaseURL for self-hosted GitLab instances (e.g., https://gitlab.company.com)
	// Leave empty for gitlab.com
	BaseURL string `json:"base_url" gorm:"type:varchar(500)"`

	// AppUsername is the Service Account username (e.g. swe-bot)
	AppUsername string `json:"app_username" gorm:"type:varchar(100)"`

	// AppEmail is the Service Account email
	AppEmail string `json:"app_email" gorm:"type:varchar(100)"`

	// ProjectAccessToken for bot operations (optional, per-project)
	// This is typically stored per-installation, not here
	// Included for simple single-project setups
	ProjectAccessToken string `json:"-" gorm:"type:varchar(255)"` // Encrypted
}

// ComputeRedirectURL returns the expected OAuth redirect URL for this provider
func (gp *GitProvider) ComputeRedirectURL() string {
	if common.AppURL == "" {
		return ""
	}
	// Clean AppURL (remove trailing slash)
	baseURL := strings.TrimSuffix(common.AppURL, "/")
	return fmt.Sprintf("%s/api/auth/oauth/%s/callback", baseURL, gp.Name)
}

// IsGitHubApp returns true if this provider uses GitHub App authentication
func (gp *GitProvider) IsGitHubApp() bool {
	return gp.AuthType == common.AuthTypeGitHubApp
}

// IsOAuth returns true if this provider uses standard OAuth
func (gp *GitProvider) IsOAuth() bool {
	return gp.AuthType == common.AuthTypeOAuth || gp.AuthType == ""
}

// GetOAuthConfig returns an oauth2.Config for this provider
func (gp *GitProvider) GetOAuthConfig() *oauth2.Config {
	return &oauth2.Config{
		ClientID:     gp.ClientID,
		ClientSecret: gp.ClientSecret,
		RedirectURL:  gp.RedirectURL,
		Scopes:       splitScopes(gp.Scopes),
		Endpoint: oauth2.Endpoint{
			AuthURL:  gp.AuthURL,
			TokenURL: gp.TokenURL,
		},
	}
}

// GetAPIBaseURL returns the API base URL for this provider
func (gp *GitProvider) GetAPIBaseURL() string {
	switch gp.Driver {
	case common.GitProviderGitHub:
		return "https://api.github.com"
	case common.GitProviderGitLab:
		if gp.BaseURL != "" {
			return gp.BaseURL + "/api/v4"
		}
		return "https://gitlab.com/api/v4"
	case common.GitProviderBitbucket:
		return "https://api.bitbucket.org/2.0"
	default:
		return ""
	}
}

// splitScopes splits comma-separated scopes into a slice
func splitScopes(scopes string) []string {
	if scopes == "" {
		return nil
	}
	result := []string{}
	for _, s := range strings.Split(scopes, ",") {
		s = strings.TrimSpace(s)
		if s != "" {
			result = append(result, s)
		}
	}
	return result
}
