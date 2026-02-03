package handlers

import (
	"net/http"
	"pixcorp-swe-ai/pkg/model"
	"strconv"

	"github.com/gin-gonic/gin"
)

// ListUserRepositories returns repositories the current user has access to
// GET /api/v1/user/repositories?q=searchterm&page=1&per_page=20
func ListUserRepositories(c *gin.Context) {
	userIDVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}
	userID := userIDVal.(uint)

	q := c.Query("q")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	perPage, _ := strconv.Atoi(c.DefaultQuery("per_page", "20"))

	if page < 1 {
		page = 1
	}
	if perPage < 1 || perPage > 100 {
		perPage = 20
	}

	offset := (page - 1) * perPage

	query := model.DB.
		Table("repositories").
		Joins("JOIN repository_accesses ON repository_accesses.repository_id = repositories.id").
		Where("repository_accesses.user_id = ?", userID)

	if q != "" {
		query = query.Where("repositories.full_name LIKE ?", "%"+q+"%")
	}

	var total int64
	query.Count(&total)

	var repositories []model.Repository
	err := query.
		Preload("Provider").
		Limit(perPage).
		Offset(offset).
		Order("repositories.full_name ASC").
		Find(&repositories).Error

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch repositories"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data": repositories,
		"meta": gin.H{
			"total":    total,
			"page":     page,
			"per_page": perPage,
		},
	})
}
