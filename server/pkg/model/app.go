package model

import (
	"sync"
	"time"

	"github.com/rs/zerolog/log"
)

type App struct {
	Model
	Name    string `json:"name" gorm:"uniqueIndex;not null"`
	Enabled bool   `json:"enabled" gorm:"default:true"`

	Configs []AppConfig `json:"configs,omitempty" gorm:"foreignKey:AppID"`
}

type AppConfig struct {
	Model
	AppID uint   `json:"app_id" gorm:"not null;index"`
	Key   string `json:"key" gorm:"type:varchar(100);not null;uniqueIndex:idx_app_config_key"`
	Value string `json:"value" gorm:"type:text"`

	App App `json:"app" gorm:"foreignKey:AppID;constraint:OnUpdate:CASCADE,OnDelete:CASCADE;"`
}

var (
	configCache = make(map[string]string)
	cacheMutex  sync.RWMutex
)

func StartAppConfigRefresher() {
	RefreshCache()
	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		for range ticker.C {
			RefreshCache()
		}
	}()
}

func RefreshCache() {
	var configs []AppConfig
	if err := DB.Find(&configs).Error; err != nil {
		log.Error().Err(err).Msg("Failed to refresh app config cache")
		return
	}

	newCache := make(map[string]string)
	for _, cfg := range configs {
		newCache[cfg.Key] = cfg.Value
	}

	cacheMutex.Lock()
	configCache = newCache
	cacheMutex.Unlock()
	log.Debug().Msg("App config cache refreshed")
}

func GetAppConfig(key string) (string, bool) {
	cacheMutex.RLock()
	val, ok := configCache[key]
	cacheMutex.RUnlock()
	return val, ok
}

func SetAppConfig(appID uint, key, value string) error {
	var config AppConfig
	err := DB.Where("app_id = ? AND key = ?", appID, key).First(&config).Error
	if err == nil {
		config.Value = value
		err = DB.Save(&config).Error
	} else {
		config = AppConfig{
			AppID: appID,
			Key:   key,
			Value: value,
		}
		err = DB.Create(&config).Error
	}

	if err == nil {
		cacheMutex.Lock()
		configCache[key] = value
		cacheMutex.Unlock()
	}
	return err
}
