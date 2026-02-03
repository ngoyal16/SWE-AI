package common

import (
	"os"
	"strconv"
)

var (
	RedisURL             string
	StorageType          string
	Port                 string
	SecretsEncryptionKey string
	DBType               string
	DBDSN                string
	AppName              string
	JWTSecret            string
	JWTExpirationSeconds int
	AppURL               string
)

func LoadEnvs() {
	RedisURL = getEnv("REDIS_URL", "redis://localhost:6379/0")
	StorageType = getEnv("STORAGE_TYPE", "redis")
	Port = getEnv("PORT", "8000")
	SecretsEncryptionKey = getEnv("SECRETS_ENCRYPTION_KEY", "")
	DBType = getEnv("DB_TYPE", "sqlite")
	DBDSN = getEnv("DB_DSN", "swe-ai.db")
	AppName = getEnv("APP_NAME", "pixcorp-swe-ai")
	JWTSecret = getEnv("JWT_SECRET", "super-secret-key")
	JWTExpirationSeconds = getEnvInt("JWT_EXPIRATION_SECONDS", 86400)
	AppURL = getEnv("APP_URL", "http://localhost:8000")
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if value, ok := os.LookupEnv(key); ok {
		if val, err := strconv.Atoi(value); err == nil {
			return val
		}
	}
	return fallback
}
