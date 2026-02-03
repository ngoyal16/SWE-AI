package common

// Git Provider Drivers
const (
	GitProviderGitHub    = "github"
	GitProviderGitLab    = "gitlab"
	GitProviderBitbucket = "bitbucket"
)

// Authentication Types
const (
	AuthTypeOAuth     = "oauth"      // Standard OAuth 2.0 flow
	AuthTypeGitHubApp = "github_app" // GitHub App with installation tokens
)
