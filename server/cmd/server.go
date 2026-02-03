package cmd

import (
	"embed"
	"io/fs"
	"net/http"
	"pixcorp-swe-ai/pkg/auth"
	"pixcorp-swe-ai/pkg/common"
	"pixcorp-swe-ai/pkg/handlers"
	"pixcorp-swe-ai/pkg/model"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
)

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Start the SWE-AI backend server",
	Run: func(cmd *cobra.Command, args []string) {
		startServer()
	},
}

// UI Content from main.go
var UIContent embed.FS

func init() {
	rootCmd.AddCommand(serverCmd)
}

func startServer() {
	model.StartAppConfigRefresher()

	// Setup Gin
	r := gin.New()
	r.Use(gin.Recovery())

	// CORS middleware (basic)
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// API Routes
	r.GET("/health", handlers.HealthCheck)

	authHandler := auth.NewAuthHandler()
	oauthHandler := auth.NewOAuthHandler()

	authGroup := r.Group("/api/auth")
	{
		// Traditional login
		authGroup.POST("/login", authHandler.Login)
		authGroup.POST("/logout", authHandler.Logout)

		// Public endpoints
		authGroup.GET("/providers", oauthHandler.GetProviders)
		// OAuth callback must be public (browser redirects here after provider auth)
		authGroup.GET("/oauth/:provider/callback", oauthHandler.HandleOAuthCallback)
	}

	// Protected auth routes (require authentication)
	authProtected := r.Group("/api/auth")
	authProtected.Use(authHandler.RequireAuth())
	{
		authProtected.GET("/me", authHandler.Me)
		// OAuth initiation requires auth (users link providers from Settings)
		authProtected.GET("/oauth/:provider", oauthHandler.InitiateOAuth)
		// User identities (linked Git providers)
		authProtected.GET("/identities", oauthHandler.GetUserIdentities)
		authProtected.DELETE("/identities/:provider", oauthHandler.UnlinkProvider)

		// User AI preferences
		authProtected.GET("/ai-preference", handlers.GetUserAIPreference)
		authProtected.POST("/ai-preference", handlers.UpsertUserAIPreference)
	}

	// Internal routes for worker (worker token authenticated, not user JWT)
	internalGroup := r.Group("/api/v1/internal")
	{
		internalGroup.GET("/sessions/:session_id/git-credentials", handlers.GetGitCredentials)
		internalGroup.GET("/sessions/:session_id/ai-credentials", handlers.GetAICredentials)
	}

	v1 := r.Group("/api/v1")
	v1.Use(authHandler.RequireAuth())
	{
		// User routes
		v1.GET("/user/repositories", handlers.ListUserRepositories)
		v1.GET("/user/sessions", handlers.ListUserSessions)

		// Agent routes (user-authenticated)
		agentGroup := v1.Group("/agent")
		{
			agentGroup.POST("/sessions", handlers.CreateSession)
			agentGroup.GET("/sessions/:session_id", handlers.GetSessionStatus)
			agentGroup.POST("/sessions/:session_id/approve", handlers.ApproveSession)
			agentGroup.POST("/sessions/:session_id/input", handlers.AddSessionInput)
		}

		// Admin routes for Git Providers
		adminGroup := v1.Group("/admin")
		{
			gitProvidersGroup := adminGroup.Group("/git-providers")
			{
				gitProvidersGroup.GET("", handlers.ListGitProviders)
				gitProvidersGroup.GET("/:id", handlers.GetGitProvider)
				gitProvidersGroup.POST("", handlers.CreateGitProvider)
				gitProvidersGroup.PUT("/:id", handlers.UpdateGitProvider)
				gitProvidersGroup.DELETE("/:id", handlers.DeleteGitProvider)
				gitProvidersGroup.PATCH("/:id/toggle", handlers.ToggleGitProvider)
			}

			aiProfilesGroup := adminGroup.Group("/ai-profiles")
			{
				aiProfilesGroup.GET("", handlers.ListAIProfiles)
				aiProfilesGroup.GET("/:id", handlers.GetAIProfile)
				aiProfilesGroup.POST("", handlers.CreateAIProfile)
				aiProfilesGroup.PUT("/:id", handlers.UpdateAIProfile)
				aiProfilesGroup.DELETE("/:id", handlers.DeleteAIProfile)
				aiProfilesGroup.PATCH("/:id/toggle", handlers.ToggleAIProfile)
			}
		}
	}

	// Serve Static UI
	setupStatic(r)

	log.Info().Str("port", common.Port).Msg("Go Server starting")
	if err := r.Run(":" + common.Port); err != nil {
		log.Fatal().Err(err).Msg("Server failed to start")
	}
}

func setupStatic(r *gin.Engine) {
	// Create a sub-filesystem for the frontend build
	uiSub, err := fs.Sub(UIContent, "ui/dist")
	if err != nil {
		log.Error().Err(err).Msg("failed to create sub filesystem for UI")
		return
	}

	// Read index.html into memory for SPA fallback
	indexContent, err := fs.ReadFile(uiSub, "index.html")
	if err != nil {
		log.Error().Err(err).Msg("failed to read index.html")
		return
	}

	// Serve static files and handle SPA fallback
	r.NoRoute(func(c *gin.Context) {
		path := c.Request.URL.Path

		// Try to open the file
		fPath := path[1:] // trim leading slash
		if fPath == "" {
			fPath = "index.html"
		}

		f, err := uiSub.Open(fPath)
		if err == nil {
			f.Close()
			c.FileFromFS(path, http.FS(uiSub))
			return
		}

		// Fallback to index.html for SPA handling
		c.Data(http.StatusOK, "text/html; charset=utf-8", indexContent)
	})
}
