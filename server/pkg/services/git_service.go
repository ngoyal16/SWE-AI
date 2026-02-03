package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"pixcorp-swe-ai/pkg/common"
	"pixcorp-swe-ai/pkg/model"
	"strings"
)

type PullRequestInput struct {
	Title string `json:"title"`
	Body  string `json:"body"`
	Head  string `json:"head"`
	Base  string `json:"base"`
}

type PullRequestResponse struct {
	URL    string `json:"url"`
	Status string `json:"status"` // "created" or "existed"
}

// CreatePullRequest creates a PR for the given session.
// It is idempotent: if a PR already exists for the head->base, it returns the existing one.
func CreatePullRequest(sessionID string, input PullRequestInput) (*PullRequestResponse, error) {
	log.Printf("[GitService] Requesting PR for session %s: %s -> %s", sessionID, input.Head, input.Base)

	creds, err := GetCredentialsForSession(sessionID)
	if err != nil {
		return nil, err
	}

	repoFullName, providerDriver, providerBaseURL, err := fetchRepoDetails(sessionID)
	if err != nil {
		return nil, err
	}

	switch providerDriver {
	case common.GitProviderGitHub:
		return createGitHubPR(creds.Token, repoFullName, input)
	case common.GitProviderGitLab:
		// Basic GitLab stub or error
		if providerBaseURL == "" {
			providerBaseURL = "https://gitlab.com"
		}
		return nil, fmt.Errorf("GitLab PR creation not yet implemented")
	default:
		return nil, fmt.Errorf("git provider driver '%s' not yet supported for PR creation", providerDriver)
	}
}

func fetchRepoDetails(sessionID string) (fullName string, driver string, baseURL string, err error) {
	var session model.Session
	// We need Repository and its Provider
	if err := model.DB.
		Preload("Repository.Provider").
		Where("session_id = ?", sessionID).
		First(&session).Error; err != nil {
		return "", "", "", fmt.Errorf("session not found: %w", err)
	}

	if session.RepositoryID == 0 {
		return "", "", "", fmt.Errorf("session has no repository")
	}

	return session.Repository.FullName, session.Repository.Provider.Driver, session.Repository.Provider.BaseURL, nil
}


// --- GitHub Implementation ---

type githubPR struct {
	HTMLURL string `json:"html_url"`
	Number  int    `json:"number"`
}

func createGitHubPR(token, repoFullName string, input PullRequestInput) (*PullRequestResponse, error) {
	// 1. Check if PR exists
	apiBase := "https://api.github.com"

	// Prepare head string. For same repo, "owner:branch".
	parts := strings.Split(repoFullName, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid repo name: %s", repoFullName)
	}
	owner := parts[0]
	headQuery := fmt.Sprintf("%s:%s", owner, input.Head)

	checkURL := fmt.Sprintf("%s/repos/%s/pulls?head=%s&base=%s&state=open", apiBase, repoFullName, headQuery, input.Base)

	req, _ := http.NewRequest("GET", checkURL, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github.v3+json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to check existing PRs: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("GitHub check failed: %s", string(body))
	}

	var existingPRs []githubPR
	if err := json.NewDecoder(resp.Body).Decode(&existingPRs); err != nil {
		return nil, err
	}

	if len(existingPRs) > 0 {
		log.Printf("[GitService] Found existing PR: %s", existingPRs[0].HTMLURL)
		return &PullRequestResponse{
			URL:    existingPRs[0].HTMLURL,
			Status: "existed",
		}, nil
	}

	// 2. Create PR
	createURL := fmt.Sprintf("%s/repos/%s/pulls", apiBase, repoFullName)

	reqBody := map[string]string{
		"title": input.Title,
		"body":  input.Body,
		"head":  input.Head,
		"base":  input.Base,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ = http.NewRequest("POST", createURL, bytes.NewBuffer(jsonBody))
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/vnd.github.v3+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err = client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to create PR: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("GitHub create PR failed (%d): %s", resp.StatusCode, string(body))
	}

	var newPR githubPR
	if err := json.NewDecoder(resp.Body).Decode(&newPR); err != nil {
		return nil, err
	}

	log.Printf("[GitService] Created new PR: %s", newPR.HTMLURL)
	return &PullRequestResponse{
		URL:    newPR.HTMLURL,
		Status: "created",
	}, nil
}
