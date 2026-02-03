package model

import (
	"crypto/rand"
	"encoding/hex"

	"gorm.io/gorm"
)

type Session struct {
	Model
	UserID            uint   `json:"user_id" gorm:"not null;index"`
	SessionID         string `json:"session_id" gorm:"type:varchar(255);not null;uniqueIndex"`
	Title             string `json:"title" gorm:"type:varchar(255)"`
	RepositoryID      uint   `json:"repository_id" gorm:"index"`
	BaseBranch        string `json:"base_branch" gorm:"type:varchar(255)"`
	FeatureBranchName string `json:"feature_branch_name" gorm:"type:varchar(255)"`
	Goal              string `json:"goal" gorm:"type:text"`
	Status            string `json:"status" gorm:"type:varchar(50)"`
	WorkerToken       string `json:"-" gorm:"type:varchar(64);index"` // Token for worker authentication

	User       User       `json:"-" gorm:"foreignKey:UserID"`
	Repository Repository `json:"repository" gorm:"foreignKey:RepositoryID"`
}

func (s *Session) BeforeCreate(tx *gorm.DB) (err error) {
	// Generate a secure random token for worker authentication
	if s.WorkerToken == "" {
		tokenBytes := make([]byte, 32)
		if _, err := rand.Read(tokenBytes); err != nil {
			return err
		}
		s.WorkerToken = hex.EncodeToString(tokenBytes)
	}
	return nil
}
