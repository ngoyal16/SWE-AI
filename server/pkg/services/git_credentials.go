package services

import (
	"context"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"pixcorp-swe-ai/pkg/common"
	"pixcorp-swe-ai/pkg/model"

	"github.com/golang-jwt/jwt/v5"
)

// GitCredentials contains the credentials needed for Git operations
type GitCredentials struct {
	Token         string `json:"token"`
	Username      string `json:"username"`
	AuthorName    string `json:"author_name"`
	AuthorEmail   string `json:"author_email"`
	CoAuthorName  string `json:"co_author_name,omitempty"`
	CoAuthorEmail string `json:"co_author_email,omitempty"`
}

// GetCredentialsForSession fetches Git credentials for a session
// Looks up session -> repository -> provider and user identity
func GetCredentialsForSession(sessionID string) (*GitCredentials, error) {
	log.Printf("[GitCredentials] Fetching credentials for session: %s", sessionID)

	var session model.Session
	err := model.DB.
		Preload("Repository.Provider").
		Preload("User").
		Where("session_id = ?", sessionID).
		First(&session).Error
	if err != nil {
		log.Printf("[GitCredentials] Session not found: %s - error: %v", sessionID, err)
		return nil, fmt.Errorf("session not found: %w", err)
	}

	log.Printf("[GitCredentials] Session found - UserID: %d, RepositoryID: %d", session.UserID, session.RepositoryID)

	if session.RepositoryID == 0 {
		log.Printf("[GitCredentials] Session %s has no repository associated", sessionID)
		return nil, fmt.Errorf("session has no repository associated")
	}

	provider := session.Repository.Provider
	log.Printf("[GitCredentials] Repository: %s (ID: %d), Provider: %s (ID: %d, AuthType: %s)",
		session.Repository.FullName, session.Repository.ID,
		provider.Name, provider.ID, provider.AuthType)

	if provider.ID == 0 {
		log.Printf("[GitCredentials] Repository %s has no provider configured", session.Repository.FullName)
		return nil, fmt.Errorf("repository has no Git provider configured - please configure a provider in Admin panel")
	}

	// Get token based on auth type
	var token, username string

	// Check if Service Account Token (ProjectAccessToken) is configured
	if provider.ProjectAccessToken != "" {
		log.Printf("[GitCredentials] Using Service Account Token (ProjectAccessToken) for provider: %s", provider.Name)
		token = provider.ProjectAccessToken

		// Use AppUsername if configured, otherwise fallback
		if provider.AppUsername != "" {
			username = provider.AppUsername
		} else if provider.AppName != "" {
			username = strings.ReplaceAll(strings.ToLower(provider.AppName), " ", "-")
		} else {
			username = "swe-bot"
		}
	} else {
		// Fallback to existing auth types
		switch provider.AuthType {
		case common.AuthTypeGitHubApp:
			log.Printf("[GitCredentials] Using GitHub App authentication (AppID: %s)", provider.AppID)
			token, err = generateGitHubAppToken(&provider, session.Repository.FullName)
			if err != nil {
				log.Printf("[GitCredentials] Failed to generate GitHub App token: %v", err)
				return nil, fmt.Errorf("failed to generate GitHub App token: %w", err)
			}
			username = "x-access-token"
			log.Printf("[GitCredentials] GitHub App token generated successfully")
		default:
			log.Printf("[GitCredentials] Using OAuth authentication for provider: %s", provider.Name)
			token, err = getOAuthToken(session.UserID, provider.Name)
			if err != nil {
				log.Printf("[GitCredentials] Failed to get OAuth token for user %d, provider %s: %v",
					session.UserID, provider.Name, err)
				return nil, fmt.Errorf("failed to get OAuth token: %w", err)
			}
			username = "oauth2"
			log.Printf("[GitCredentials] OAuth token retrieved successfully")
		}
	}

	// Build author info from app name or provider defaults
	authorName := provider.AppName
	if authorName == "" {
		authorName = "swe-agent[bot]"
	}

	// Generate email based on driver
	var authorEmail string
	if provider.AppEmail != "" {
		authorEmail = provider.AppEmail
	} else {
		switch provider.Driver {
		case common.GitProviderGitHub:
			authorEmail = fmt.Sprintf("%s@users.noreply.github.com", strings.ReplaceAll(authorName, " ", "-"))
		case common.GitProviderGitLab:
			if provider.BaseURL != "" {
				// Self-hosted GitLab
				authorEmail = fmt.Sprintf("%s@noreply.gitlab.local", strings.ReplaceAll(authorName, " ", "-"))
			} else {
				authorEmail = fmt.Sprintf("%s@users.noreply.gitlab.com", strings.ReplaceAll(authorName, " ", "-"))
			}
		default:
			authorEmail = fmt.Sprintf("%s@noreply.git", strings.ReplaceAll(authorName, " ", "-"))
		}
	}

	// Co-author from UserIdentity (provider-specific info is more accurate for Git)
	var coAuthorName, coAuthorEmail string
	var identity model.UserIdentity
	if err := model.DB.Where("user_id = ? AND provider = ?", session.UserID, provider.Name).First(&identity).Error; err == nil {
		// Use identity info from the provider
		coAuthorName = identity.Name
		if coAuthorName == "" {
			coAuthorName = identity.Username
		}
		coAuthorEmail = identity.Email
		log.Printf("[GitCredentials] Using UserIdentity for co-author: %s <%s>", coAuthorName, coAuthorEmail)
	} else {
		log.Printf("[GitCredentials] UserIdentity not found for user %d, provider %s. Skipping co-author attribution.", session.UserID, provider.Name)
	}

	log.Printf("[GitCredentials] Credentials prepared - Author: %s <%s>, CoAuthor: %s <%s>",
		authorName, authorEmail, coAuthorName, coAuthorEmail)

	return &GitCredentials{
		Token:         token,
		Username:      username,
		AuthorName:    authorName,
		AuthorEmail:   authorEmail,
		CoAuthorName:  coAuthorName,
		CoAuthorEmail: coAuthorEmail,
	}, nil
}

// getOAuthToken retrieves the OAuth token for a user's identity
func getOAuthToken(userID uint, providerName string) (string, error) {
	log.Printf("[GitCredentials] Looking up OAuth token for user %d, provider %s", userID, providerName)

	var identity model.UserIdentity
	err := model.DB.
		Where("user_id = ? AND provider = ?", userID, providerName).
		First(&identity).Error
	if err != nil {
		log.Printf("[GitCredentials] UserIdentity not found for user %d, provider %s: %v", userID, providerName, err)
		return "", fmt.Errorf("user identity not found for provider %s: please link your account in Settings", providerName)
	}

	log.Printf("[GitCredentials] Found UserIdentity ID: %d for provider %s", identity.ID, providerName)
	// TODO: Decrypt token if encrypted
	return identity.Token, nil
}

// generateGitHubAppToken generates an installation access token for a GitHub App
func generateGitHubAppToken(provider *model.GitProvider, repoFullName string) (string, error) {
	if provider.AppID == "" || provider.PrivateKey == "" {
		return "", fmt.Errorf("GitHub App not configured: missing app_id or private_key")
	}

	// 1. Parse private key
	block, _ := pem.Decode([]byte(provider.PrivateKey))
	if block == nil {
		return "", fmt.Errorf("failed to parse private key PEM block")
	}

	var privateKey interface{}
	var err error

	// Try PKCS1 first (RSA PRIVATE KEY), then PKCS8 (PRIVATE KEY)
	privateKey, err = x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		privateKey, err = x509.ParsePKCS8PrivateKey(block.Bytes)
		if err != nil {
			return "", fmt.Errorf("failed to parse private key: %w", err)
		}
	}

	// 2. Create JWT
	now := time.Now()
	claims := jwt.MapClaims{
		"iat": now.Add(-60 * time.Second).Unix(),
		"exp": now.Add(10 * time.Minute).Unix(),
		"iss": provider.AppID,
	}

	jwtToken := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	signedJWT, err := jwtToken.SignedString(privateKey)
	if err != nil {
		return "", fmt.Errorf("failed to sign JWT: %w", err)
	}

	// 3. Get installation ID for the repository
	installationID, err := getInstallationIDForRepo(signedJWT, repoFullName)
	if err != nil {
		return "", fmt.Errorf("failed to get installation ID: %w", err)
	}

	// 4. Get installation access token
	accessToken, err := getInstallationAccessToken(signedJWT, installationID)
	if err != nil {
		return "", fmt.Errorf("failed to get installation access token: %w", err)
	}

	return accessToken, nil
}

// getInstallationIDForRepo finds the GitHub App installation ID for a repository
func getInstallationIDForRepo(jwt string, repoFullName string) (int64, error) {
	parts := strings.Split(repoFullName, "/")
	if len(parts) != 2 {
		return 0, fmt.Errorf("invalid repository full name: %s", repoFullName)
	}
	owner := parts[0]

	// Try to get installation for the owner (org or user)
	url := fmt.Sprintf("https://api.github.com/orgs/%s/installation", owner)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return 0, err
	}
	req.Header.Set("Authorization", "Bearer "+jwt)
	req.Header.Set("Accept", "application/vnd.github+json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	// If org installation fails, try user installation
	if resp.StatusCode == 404 {
		url = fmt.Sprintf("https://api.github.com/users/%s/installation", owner)
		req, err = http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			return 0, err
		}
		req.Header.Set("Authorization", "Bearer "+jwt)
		req.Header.Set("Accept", "application/vnd.github+json")

		resp, err = client.Do(req)
		if err != nil {
			return 0, err
		}
		defer resp.Body.Close()
	}

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return 0, fmt.Errorf("failed to get installation: %s - %s", resp.Status, string(body))
	}

	var result struct {
		ID int64 `json:"id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, fmt.Errorf("failed to decode installation response: %w", err)
	}

	return result.ID, nil
}

// getInstallationAccessToken exchanges a JWT for an installation access token
func getInstallationAccessToken(jwt string, installationID int64) (string, error) {
	url := fmt.Sprintf("https://api.github.com/app/installations/%d/access_tokens", installationID)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "POST", url, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+jwt)
	req.Header.Set("Accept", "application/vnd.github+json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("failed to get access token: %s - %s", resp.Status, string(body))
	}

	var result struct {
		Token string `json:"token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("failed to decode access token response: %w", err)
	}

	return result.Token, nil
}
