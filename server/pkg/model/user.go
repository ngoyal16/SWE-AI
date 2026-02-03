package model

import (
	"time"

	"golang.org/x/crypto/bcrypt"
)

type User struct {
	Model
	Username    string     `json:"username" gorm:"type:varchar(100);uniqueIndex;not null"`
	Email       string     `json:"email" gorm:"type:varchar(100);uniqueIndex"`
	Password    string     `json:"-" gorm:"type:varchar(255)"`
	Name        string     `json:"name,omitempty" gorm:"type:varchar(100)"`
	AvatarURL   string     `json:"avatar_url,omitempty" gorm:"type:varchar(500)"`
	LastLoginAt *time.Time `json:"last_login_at,omitempty" gorm:"index"`
	Enabled     bool       `json:"enabled" gorm:"default:true"`
	IsAdmin     bool       `json:"is_admin" gorm:"default:false"`

	Identities []UserIdentity `json:"identities,omitempty" gorm:"foreignKey:UserID"`
}

type UserIdentity struct {
	Model
	UserID     uint   `json:"user_id" gorm:"not null;index"`
	Provider   string `json:"provider" gorm:"type:varchar(50);not null;uniqueIndex:idx_provider_sub"`
	ProviderID string `json:"provider_id" gorm:"type:varchar(255);not null;uniqueIndex:idx_provider_sub"` // sub or provider internal id
	Username   string `json:"username" gorm:"type:varchar(100)"`                                          // Provider username (e.g., GitHub username)
	Name       string `json:"name" gorm:"type:varchar(255)"`                                              // Display name from provider
	Email      string `json:"email" gorm:"type:varchar(100)"`
	Token      string `json:"-" gorm:"type:text"` // Encrypted

	User User `json:"-" gorm:"foreignKey:UserID"`
}

func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), 14)
	return string(bytes), err
}

func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}
