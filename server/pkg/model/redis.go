package model

import (
	"context"
	"pixcorp-swe-ai/pkg/common"

	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

var Rdb *redis.Client
var Ctx = context.Background()

func InitRedis() {
	opt, err := redis.ParseURL(common.RedisURL)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to parse Redis URL")
	}

	Rdb = redis.NewClient(opt)
	_, err = Rdb.Ping(Ctx).Result()
	if err != nil {
		log.Error().Err(err).Msg("Failed to connect to Redis")
	} else {
		log.Info().Msg("Connected to Redis")
	}
}
