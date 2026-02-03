package sync

import (
	"context"
	"testing"
	"time"

	"pixcorp-swe-ai/pkg/model"

	"github.com/glebarez/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// setupTestDB initializes an in-memory SQLite database for testing
func setupTestDB(t testing.TB) {
	// Use in-memory SQLite
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		t.Fatalf("Failed to connect to test database: %v", err)
	}

	model.DB = db

	// Ensure single connection for in-memory SQLite to avoid "no such table" errors in concurrent tests
	sqlDB, err := db.DB()
	if err != nil {
		t.Fatalf("Failed to get sql.DB: %v", err)
	}
	sqlDB.SetMaxOpenConns(1)

	// AutoMigrate all models
	err = model.DB.AutoMigrate(
		&model.User{},
		&model.UserIdentity{},
		&model.GitProvider{},
		&model.Repository{},
		&model.RepositoryAccess{},
	)
	if err != nil {
		t.Fatalf("Failed to migrate test database: %v", err)
	}
}

func TestSyncReposToDB_Cleanup(t *testing.T) {
	setupTestDB(t)

	// 1. Setup Data
	user := model.User{Username: "testuser"}
	model.DB.Create(&user)

	provider := model.GitProvider{Name: "github", Driver: "github"}
	model.DB.Create(&provider)

	identity := model.UserIdentity{
		UserID:     user.ID,
		Provider:   "github",
		ProviderID: "gh_123",
		User:       user,
	}
	model.DB.Create(&identity)

	// Create some initial repositories and access
	repo1 := model.Repository{
		ProviderID: provider.ID,
		Name:       "repo1",
		FullName:   "testuser/repo1",
		ExternalID: "101",
	}
	model.DB.Create(&repo1)

	access1 := model.RepositoryAccess{
		UserID:       user.ID,
		RepositoryID: repo1.ID,
		IdentityID:   identity.ID,
		Permission:   "admin",
		SyncedAt:     time.Now().Add(-1 * time.Hour), // Old sync time
	}
	model.DB.Create(&access1)

	repo2 := model.Repository{
		ProviderID: provider.ID,
		Name:       "repo2",
		FullName:   "testuser/repo2",
		ExternalID: "102",
	}
	model.DB.Create(&repo2)

	access2 := model.RepositoryAccess{
		UserID:       user.ID,
		RepositoryID: repo2.ID,
		IdentityID:   identity.ID,
		Permission:   "read",
		SyncedAt:     time.Now().Add(-1 * time.Hour),
	}
	model.DB.Create(&access2)

	// 2. Prepare Sync Data
	// repo1 is still present
	// repo2 is REMOVED (access lost)
	// repo3 is NEW
	reposToSync := []remoteRepo{
		{
			Name:       "repo1",
			FullName:   "testuser/repo1",
			ExternalID: "101",
			Permission: "admin",
		},
		{
			Name:       "repo3",
			FullName:   "testuser/repo3",
			ExternalID: "103",
			Permission: "write",
		},
	}

	// 3. Run Sync
	ctx := context.Background()
	err := syncReposToDB(ctx, &identity, &provider, reposToSync)
	if err != nil {
		t.Fatalf("syncReposToDB failed: %v", err)
	}

	// 4. Verify Results

	// Verify access1 is still there
	var checkAccess1 model.RepositoryAccess
	if err := model.DB.First(&checkAccess1, access1.ID).Error; err != nil {
		t.Errorf("Access1 should still exist, but got error: %v", err)
	}

	// Verify access2 is DELETED
	var checkAccess2 model.RepositoryAccess
	if err := model.DB.First(&checkAccess2, access2.ID).Error; err != gorm.ErrRecordNotFound {
		t.Errorf("Access2 should have been deleted, but got error: %v", err)
	}

	// Verify access3 is CREATED
	var checkAccess3 model.RepositoryAccess
	// We need to find the repo3 ID first
	var repo3 model.Repository
	model.DB.Where("external_id = ?", "103").First(&repo3)

	if err := model.DB.Where("repository_id = ?", repo3.ID).First(&checkAccess3).Error; err != nil {
		t.Errorf("Access3 should exist, but got error: %v", err)
	}
	if checkAccess3.Permission != "write" {
		t.Errorf("Access3 permission mismatch. Want write, got %s", checkAccess3.Permission)
	}
}

func TestSyncReposToDB_FullCleanup(t *testing.T) {
	setupTestDB(t)

	// Setup Data
	user := model.User{Username: "testuser"}
	model.DB.Create(&user)
	provider := model.GitProvider{Name: "github", Driver: "github"}
	model.DB.Create(&provider)
	identity := model.UserIdentity{UserID: user.ID, Provider: "github", ProviderID: "gh_123"}
	model.DB.Create(&identity)

	repo1 := model.Repository{ProviderID: provider.ID, Name: "repo1", FullName: "testuser/repo1", ExternalID: "101"}
	model.DB.Create(&repo1)
	model.DB.Create(&model.RepositoryAccess{UserID: user.ID, RepositoryID: repo1.ID, IdentityID: identity.ID, Permission: "admin"})

	// Run Sync with empty list
	ctx := context.Background()
	err := syncReposToDB(ctx, &identity, &provider, []remoteRepo{})
	if err != nil {
		t.Fatalf("syncReposToDB failed: %v", err)
	}

	// Verify all access is gone
	var count int64
	model.DB.Model(&model.RepositoryAccess{}).Where("identity_id = ?", identity.ID).Count(&count)
	if count != 0 {
		t.Errorf("Expected 0 access records, got %d", count)
	}
}

func TestSyncReposToDB_Isolation(t *testing.T) {
	setupTestDB(t)

	// Identity A
	userA := model.User{Username: "userA"}
	model.DB.Create(&userA)
	identityA := model.UserIdentity{UserID: userA.ID, Provider: "github", ProviderID: "gh_A"}
	model.DB.Create(&identityA)

	// Identity B
	userB := model.User{Username: "userB"}
	model.DB.Create(&userB)
	identityB := model.UserIdentity{UserID: userB.ID, Provider: "github", ProviderID: "gh_B"}
	model.DB.Create(&identityB)

	provider := model.GitProvider{Name: "github", Driver: "github"}
	model.DB.Create(&provider)

	repo := model.Repository{ProviderID: provider.ID, Name: "repo", FullName: "shared/repo", ExternalID: "999"}
	model.DB.Create(&repo)

	// Access for A (to be kept)
	accessA := model.RepositoryAccess{UserID: userA.ID, RepositoryID: repo.ID, IdentityID: identityA.ID}
	model.DB.Create(&accessA)

	// Access for B (to be kept, even if we sync A and remove A's access)
	accessB := model.RepositoryAccess{UserID: userB.ID, RepositoryID: repo.ID, IdentityID: identityB.ID}
	model.DB.Create(&accessB)

	// Sync A with empty list -> Should remove accessA but NOT accessB
	err := syncReposToDB(context.Background(), &identityA, &provider, []remoteRepo{})
	if err != nil {
		t.Fatalf("syncReposToDB failed: %v", err)
	}

	var checkA model.RepositoryAccess
	if err := model.DB.First(&checkA, accessA.ID).Error; err != gorm.ErrRecordNotFound {
		t.Errorf("AccessA should be deleted")
	}

	var checkB model.RepositoryAccess
	if err := model.DB.First(&checkB, accessB.ID).Error; err != nil {
		t.Errorf("AccessB should still exist: %v", err)
	}
}

func BenchmarkSyncAllRepositories(b *testing.B) {
	// Save original function and restore after benchmark
	originalFetch := fetchRepositoriesFunc
	defer func() { fetchRepositoriesFunc = originalFetch }()

	// Mock fetchRepositories to simulate latency
	fetchRepositoriesFunc = func(ctx context.Context, provider *model.GitProvider, token string) ([]remoteRepo, error) {
		time.Sleep(50 * time.Millisecond) // Simulate network latency
		return []remoteRepo{
			{
				Name:       "bench-repo",
				FullName:   "bench/repo",
				ExternalID: "bench-1",
				Permission: "read",
			},
		}, nil
	}

	setupTestDB(b)

	// Create 50 identities to process
	provider := model.GitProvider{Name: "github", Driver: "github", Enabled: true}
	model.DB.Create(&provider)

	for i := 0; i < 50; i++ {
		user := model.User{Username: "user" + string(rune(i))}
		model.DB.Create(&user)
		identity := model.UserIdentity{
			UserID:     user.ID,
			Provider:   "github",
			ProviderID: "gh_" + string(rune(i)),
			User:       user,
			Token:      "token",
		}
		model.DB.Create(&identity)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// We use a fresh context for each run
		err := SyncAllRepositories(context.Background())
		if err != nil {
			b.Fatalf("SyncAllRepositories failed: %v", err)
		}
	}
}
