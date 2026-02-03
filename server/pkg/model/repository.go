package model

import (
	"time"
)

// Repository represents a Git repository from any provider
type Repository struct {
	Model
	ProviderID    uint   `json:"provider_id" gorm:"not null;index"` // Link to GitProvider
	Name          string `json:"name" gorm:"type:varchar(255);not null"`
	FullName      string `json:"full_name" gorm:"type:varchar(255);not null;uniqueIndex:idx_provider_repo"`
	URL           string `json:"url" gorm:"type:varchar(500)"`
	SSHURL        string `json:"ssh_url" gorm:"type:varchar(500)"`
	CloneURL      string `json:"clone_url" gorm:"type:varchar(500)"`
	DefaultBranch string `json:"default_branch" gorm:"type:varchar(100);default:'main'"`
	Language      string `json:"language" gorm:"type:varchar(100)"`
	Stars         int    `json:"stars" gorm:"default:0"`
	Private       bool   `json:"private" gorm:"default:false"`
	ExternalID    string `json:"external_id" gorm:"type:varchar(255);uniqueIndex:idx_provider_repo"`

	Provider GitProvider `json:"provider" gorm:"foreignKey:ProviderID"`
}

// RepositoryAccess manages which users have access to which repositories
// and through which of their linked identities.
type RepositoryAccess struct {
	Model
	UserID       uint      `json:"user_id" gorm:"not null;index"`
	RepositoryID uint      `json:"repository_id" gorm:"not null;index"`
	IdentityID   uint      `json:"identity_id" gorm:"not null;index"`  // Which linked account provides access
	Permission   string    `json:"permission" gorm:"type:varchar(50)"` // read, write, admin
	SyncedAt     time.Time `json:"synced_at" gorm:"index"`

	User       User         `json:"-" gorm:"foreignKey:UserID"`
	Repository Repository   `json:"-" gorm:"foreignKey:RepositoryID"`
	Identity   UserIdentity `json:"-" gorm:"foreignKey:IdentityID"`
}
