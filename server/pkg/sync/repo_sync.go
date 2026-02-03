package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"time"

	"github.com/rs/zerolog/log"
)

// SyncAllRepositories synchronizes repositories for all users who have linked identities
func SyncAllRepositories(ctx context.Context) error {
	var identities []model.UserIdentity
	if err := model.DB.Preload("User").Find(&identities).Error; err != nil {
		return fmt.Errorf("failed to fetch user identities: %w", err)
	}

	log.Info().Int("count", len(identities)).Msg("Starting repository sync for all identities")

	for _, identity := range identities {
		log.Info().
			Str("user", identity.User.Username).
			Str("provider", identity.Provider).
			Msg("Syncing repositories for identity")

		if err := SyncIdentityRepositories(ctx, &identity); err != nil {
			log.Error().
				Err(err).
				Str("user", identity.User.Username).
				Str("provider", identity.Provider).
				Msg("Failed to sync repositories for identity")
			continue
		}
	}

	return nil
}

// SyncIdentityRepositories synchronizes repositories for a specific user identity
func SyncIdentityRepositories(ctx context.Context, identity *model.UserIdentity) error {
	var provider model.GitProvider
	if err := model.DB.Where("name = ? AND enabled = ?", identity.Provider, true).First(&provider).Error; err != nil {
		return fmt.Errorf("provider %s not found or disabled: %w", identity.Provider, err)
	}

	repos, err := fetchRepositories(ctx, &provider, identity.Token)
	if err != nil {
		return fmt.Errorf("failed to fetch repositories: %w", err)
	}

	return syncReposToDB(ctx, identity, &provider, repos)
}

func syncReposToDB(ctx context.Context, identity *model.UserIdentity, provider *model.GitProvider, repos []remoteRepo) error {
	var activeAccessIDs []uint

	for _, r := range repos {
		// 1. Create or Update Repository
		repo := model.Repository{
			ProviderID:    provider.ID,
			Name:          r.Name,
			FullName:      r.FullName,
			URL:           r.URL,
			SSHURL:        r.SSHURL,
			CloneURL:      r.CloneURL,
			DefaultBranch: r.DefaultBranch,
			Language:      r.Language,
			Stars:         r.Stars,
			Private:       r.Private,
			ExternalID:    r.ExternalID,
		}

		// Use Upsert logic (find by provider and external_id)
		var existingRepo model.Repository
		err := model.DB.Where("provider_id = ? AND external_id = ?", provider.ID, r.ExternalID).First(&existingRepo).Error
		if err == nil {
			repo.ID = existingRepo.ID
			if err := model.DB.Save(&repo).Error; err != nil {
				log.Error().Err(err).Str("repo", repo.FullName).Msg("Failed to update repository")
				continue
			}
		} else {
			if err := model.DB.Create(&repo).Error; err != nil {
				log.Error().Err(err).Str("repo", repo.FullName).Msg("Failed to create repository")
				continue
			}
		}

		// 2. Create or Update Repository Access
		access := model.RepositoryAccess{
			UserID:       identity.UserID,
			RepositoryID: repo.ID,
			IdentityID:   identity.ID,
			Permission:   r.Permission,
			SyncedAt:     time.Now(),
		}

		var existingAccess model.RepositoryAccess
		err = model.DB.Where("user_id = ? AND repository_id = ? AND identity_id = ?", identity.UserID, repo.ID, identity.ID).First(&existingAccess).Error
		if err == nil {
			access.ID = existingAccess.ID
			if err := model.DB.Save(&access).Error; err != nil {
				log.Error().Err(err).Str("repo", repo.FullName).Msg("Failed to update repository access")
				continue
			}
		} else {
			if err := model.DB.Create(&access).Error; err != nil {
				log.Error().Err(err).Str("repo", repo.FullName).Msg("Failed to create repository access")
				continue
			}
		}
		activeAccessIDs = append(activeAccessIDs, access.ID)
	}

	// Clean up access records that were not synced in this run (meaning access was lost)
	query := model.DB.Where("identity_id = ?", identity.ID)
	if len(activeAccessIDs) > 0 {
		query = query.Where("id NOT IN ?", activeAccessIDs)
	}

	if err := query.Delete(&model.RepositoryAccess{}).Error; err != nil {
		log.Error().Err(err).Uint("identity_id", identity.ID).Msg("Failed to clean up stale repository access records")
		return fmt.Errorf("failed to cleanup stale access: %w", err)
	}

	return nil
}

type remoteRepo struct {
	Name          string
	FullName      string
	URL           string
	SSHURL        string
	CloneURL      string
	DefaultBranch string
	Language      string
	Stars         int
	Private       bool
	ExternalID    string
	Permission    string
}

func fetchRepositories(ctx context.Context, provider *model.GitProvider, token string) ([]remoteRepo, error) {
	switch provider.Driver {
	case "github":
		return fetchGitHubRepos(ctx, provider, token)
	case "gitlab":
		return fetchGitLabRepos(ctx, provider, token)
	case "bitbucket":
		return fetchBitbucketRepos(ctx, provider, token)
	default:
		return nil, fmt.Errorf("unsupported provider driver: %s", provider.Driver)
	}
}

func fetchGitHubRepos(ctx context.Context, provider *model.GitProvider, token string) ([]remoteRepo, error) {
	var allRepos []remoteRepo
	page := 1
	client := &http.Client{Timeout: 30 * time.Second}

	for {
		url := fmt.Sprintf("%s/user/repos?per_page=100&page=%d", provider.GetAPIBaseURL(), page)

		req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Accept", "application/vnd.github+json")

		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			return nil, fmt.Errorf("github api error: %s - %s", resp.Status, string(body))
		}

		var ghRepos []struct {
			ID            int64  `json:"id"`
			Name          string `json:"name"`
			FullName      string `json:"full_name"`
			HTMLURL       string `json:"html_url"`
			SSHURL        string `json:"ssh_url"`
			CloneURL      string `json:"clone_url"`
			DefaultBranch string `json:"default_branch"`
			Language      string `json:"language"`
			Stargazers    int    `json:"stargazers_count"`
			Private       bool   `json:"private"`
			Permissions   struct {
				Admin bool `json:"admin"`
				Push  bool `json:"push"`
				Pull  bool `json:"pull"`
			} `json:"permissions"`
		}

		if err := json.NewDecoder(resp.Body).Decode(&ghRepos); err != nil {
			return nil, err
		}

		if len(ghRepos) == 0 {
			break
		}

		for _, r := range ghRepos {
			permission := "pull"
			if r.Permissions.Admin {
				permission = "admin"
			} else if r.Permissions.Push {
				permission = "push"
			}

			allRepos = append(allRepos, remoteRepo{
				Name:          r.Name,
				FullName:      r.FullName,
				URL:           r.HTMLURL,
				SSHURL:        r.SSHURL,
				CloneURL:      r.CloneURL,
				DefaultBranch: r.DefaultBranch,
				Language:      r.Language,
				Stars:         r.Stargazers,
				Private:       r.Private,
				ExternalID:    fmt.Sprintf("%d", r.ID),
				Permission:    permission,
			})
		}

		if len(ghRepos) < 100 {
			break
		}
		page++
	}
	return allRepos, nil
}

func fetchGitLabRepos(ctx context.Context, provider *model.GitProvider, token string) ([]remoteRepo, error) {
	var allRepos []remoteRepo
	page := 1
	client := &http.Client{Timeout: 30 * time.Second}

	for {
		url := fmt.Sprintf("%s/projects?membership=true&min_access_level=20&per_page=100&page=%d", provider.GetAPIBaseURL(), page)

		req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(resp.Body)
			return nil, fmt.Errorf("gitlab api error: %s - %s", resp.Status, string(body))
		}

		var glRepos []struct {
			ID                int64  `json:"id"`
			Name              string `json:"name"`
			PathWithNamespace string `json:"path_with_namespace"`
			WebURL            string `json:"web_url"`
			SSHURL            string `json:"ssh_url_to_repo"`
			HTTPURL           string `json:"http_url_to_repo"`
			DefaultBranch     string `json:"default_branch"`
			Visibility        string `json:"visibility"`
			StarCount         int    `json:"star_count"`
		}

		if err := json.NewDecoder(resp.Body).Decode(&glRepos); err != nil {
			return nil, err
		}

		if len(glRepos) == 0 {
			break
		}

		for _, r := range glRepos {
			allRepos = append(allRepos, remoteRepo{
				Name:          r.Name,
				FullName:      r.PathWithNamespace,
				URL:           r.WebURL,
				SSHURL:        r.SSHURL,
				CloneURL:      r.HTTPURL,
				DefaultBranch: r.DefaultBranch,
				Language:      "", // GitLab requires separate call or different endpoint for language
				Stars:         r.StarCount,
				Private:       r.Visibility != "public",
				ExternalID:    fmt.Sprintf("%d", r.ID),
				Permission:    "developer", // Simplified, min_access_level=20 is Reporter
			})
		}

		if len(glRepos) < 100 {
			break
		}
		page++
	}
	return allRepos, nil
}

func fetchBitbucketRepos(ctx context.Context, provider *model.GitProvider, token string) ([]remoteRepo, error) {
	// Bitbucket implementation would go here
	// For now return empty to avoid errors
	return []remoteRepo{}, nil
}
