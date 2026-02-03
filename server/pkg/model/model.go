package model

import (
	"fmt"
	"log"
	"os"
	"pixcorp-swe-ai/pkg/common"
	"strings"
	"sync"
	"time"

	"github.com/glebarez/sqlite"
	"gorm.io/driver/mysql"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var (
	DB   *gorm.DB
	once sync.Once
)

type Model struct {
	ID        uint      `gorm:"primarykey" json:"id"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

func InitDB() {
	dsn := common.DBDSN

	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             time.Second,
			LogLevel:                  logger.Info,
			IgnoreRecordNotFoundError: true,
			Colorful:                  false,
		},
	)

	var err error
	once.Do(func() {
		cfg := &gorm.Config{
			Logger: newLogger,
		}

		switch common.DBType {
		case "sqlite":
			DB, err = gorm.Open(sqlite.Open(dsn), cfg)
		case "mysql":
			mysqlDSN := strings.TrimPrefix(dsn, "mysql://")
			if !strings.Contains(mysqlDSN, "parseTime=") {
				separator := "?"
				if strings.Contains(mysqlDSN, "?") {
					separator = "&"
				}
				mysqlDSN = mysqlDSN + separator + "parseTime=true"
			}
			DB, err = gorm.Open(mysql.Open(mysqlDSN), cfg)
		case "postgres":
			DB, err = gorm.Open(postgres.Open(dsn), cfg)
		default:
			err = fmt.Errorf("unsupported database type: %s", common.DBType)
		}

		if err != nil {
			panic("failed to connect database: " + err.Error())
		}
	})

	if DB == nil {
		panic("database connection is nil, check your DB_TYPE and DB_DSN settings")
	}

	if common.DBType == "sqlite" {
		if err := DB.Exec("PRAGMA foreign_keys = ON").Error; err != nil {
			panic("failed to enable sqlite foreign keys: " + err.Error())
		}
	}
}

func AutoMigrate() error {
	err := DB.AutoMigrate(
		&App{},
		&AppConfig{},
		&User{},
		&UserIdentity{},
		&GitProvider{},
		&Repository{},
		&RepositoryAccess{},
		&AIProfile{},
		&UserAIPreference{},
		&Session{},
	)
	if err != nil {
		return err
	}

	// Create default admin user if none exists
	var count int64
	DB.Model(&User{}).Count(&count)
	if count == 0 {
		hashedPassword, err := HashPassword("admin")
		if err != nil {
			return fmt.Errorf("failed to hash default password: %w", err)
		}

		admin := User{
			Username: "admin",
			Password: hashedPassword,
			IsAdmin:  true,
			Enabled:  true,
		}

		if err := DB.Create(&admin).Error; err != nil {
			return fmt.Errorf("failed to create default admin: %w", err)
		}
		fmt.Println("Created default admin user (admin/admin)")
	}

	// Create default git providers if none exist
	var gpCount int64
	DB.Model(&GitProvider{}).Count(&gpCount)
	if gpCount == 0 {
		providers := []GitProvider{
			{
				Name:        common.GitProviderGitHub,
				DisplayName: "GitHub",
				Driver:      common.GitProviderGitHub,
				AuthType:    common.AuthTypeGitHubApp, // GitHub uses App authentication
				AuthURL:     "https://github.com/login/oauth/authorize",
				TokenURL:    "https://github.com/login/oauth/access_token",
				UserInfoURL: "https://api.github.com/user",
				Scopes:      "repo,user:email",
			},
			{
				Name:        common.GitProviderGitLab,
				DisplayName: "GitLab",
				Driver:      common.GitProviderGitLab,
				AuthType:    common.AuthTypeOAuth, // GitLab uses OAuth
				AuthURL:     "https://gitlab.com/oauth/authorize",
				TokenURL:    "https://gitlab.com/oauth/token",
				UserInfoURL: "https://gitlab.com/api/v4/user",
				Scopes:      "api,read_user,read_repository,write_repository",
			},
			{
				Name:        common.GitProviderBitbucket,
				DisplayName: "Bitbucket",
				Driver:      common.GitProviderBitbucket,
				AuthType:    common.AuthTypeOAuth, // Bitbucket uses OAuth
				AuthURL:     "https://bitbucket.org/site/oauth2/authorize",
				TokenURL:    "https://bitbucket.org/site/oauth2/access_token",
				UserInfoURL: "https://api.bitbucket.org/2.0/user",
				Scopes:      "account,repository",
			},
		}

		for _, p := range providers {
			DB.Create(&p)
		}
		fmt.Println("Created default Git providers (GitHub, GitLab, Bitbucket)")
	}

	// Update existing GitProvider redirect URLs if they are wrong/missing
	var allProviders []GitProvider
	if err := DB.Find(&allProviders).Error; err == nil {
		for _, p := range allProviders {
			correctURL := p.ComputeRedirectURL()
			if p.RedirectURL != correctURL && correctURL != "" {
				DB.Model(&p).Update("redirect_url", correctURL)
				fmt.Printf("Updated redirect URL for provider %s: %s\n", p.Name, correctURL)
			}
		}
	}

	// Create default AI profiles if none exist
	if err := SeedInitialAIProfiles(); err != nil {
		fmt.Printf("Warning: failed to seed default AI profiles: %v\n", err)
	}

	return nil
}
