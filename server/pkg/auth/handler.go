package auth

import (
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"strings"

	"github.com/gin-gonic/gin"
)

const (
	AuthCookieName = "auth_token"
	CookieMaxAge   = 7 * 24 * 60 * 60 // 7 days in seconds
)

type AuthHandler struct{}

func NewAuthHandler() *AuthHandler {
	return &AuthHandler{}
}

// setAuthCookie sets the JWT token as an httpOnly cookie
func setAuthCookie(c *gin.Context, token string) {
	// Set cookie with secure settings
	c.SetCookie(
		AuthCookieName, // name
		token,          // value
		CookieMaxAge,   // maxAge in seconds
		"/",            // path
		"",             // domain (empty = current domain)
		false,          // secure (set to true in production with HTTPS)
		true,           // httpOnly
	)
}

// clearAuthCookie removes the auth cookie
func clearAuthCookie(c *gin.Context) {
	c.SetCookie(
		AuthCookieName,
		"",
		-1, // negative maxAge deletes the cookie
		"/",
		"",
		false,
		true,
	)
}

func (h *AuthHandler) Login(c *gin.Context) {
	var input struct {
		Username string `json:"username" binding:"required"`
		Password string `json:"password" binding:"required"`
	}

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var user model.User
	if err := model.DB.Where("username = ?", input.Username).First(&user).Error; err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid username or password"})
		return
	}

	if !model.CheckPasswordHash(input.Password, user.Password) {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid username or password"})
		return
	}

	token, err := GenerateJWT(user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	// Set cookie instead of returning token
	setAuthCookie(c, token)

	c.JSON(http.StatusOK, gin.H{
		"message": "Login successful",
		"user":    user,
	})
}

// Logout clears the auth cookie
func (h *AuthHandler) Logout(c *gin.Context) {
	clearAuthCookie(c)
	c.JSON(http.StatusOK, gin.H{"message": "Logged out successfully"})
}

// Me returns the current authenticated user
func (h *AuthHandler) Me(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Not authenticated"})
		return
	}

	var user model.User
	if err := model.DB.First(&user, userID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	c.JSON(http.StatusOK, user)
}

func (h *AuthHandler) RequireAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		var token string

		// First, try to get token from cookie
		if cookieToken, err := c.Cookie(AuthCookieName); err == nil && cookieToken != "" {
			token = cookieToken
		} else {
			// Fallback to Authorization header
			authHeader := c.GetHeader("Authorization")
			if authHeader != "" {
				parts := strings.Split(authHeader, " ")
				if len(parts) == 2 && parts[0] == "Bearer" {
					token = parts[1]
				}
			}
		}

		if token == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
			c.Abort()
			return
		}

		claims, err := ValidateJWT(token)
		if err != nil {
			clearAuthCookie(c) // Clear invalid cookie
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("is_admin", claims.IsAdmin)
		c.Next()
	}
}
