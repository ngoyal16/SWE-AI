package cmd

import (
	"context"
	"pixcorp-swe-ai/pkg/sync"

	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
)

var syncReposCmd = &cobra.Command{
	Use:   "repo:sync",
	Short: "Sync repositories from Git providers",
	Run: func(cmd *cobra.Command, args []string) {
		log.Info().Msg("Running repository sync command...")
		ctx := context.Background()
		if err := sync.SyncAllRepositories(ctx); err != nil {
			log.Fatal().Err(err).Msg("Repository sync failed")
		}
		log.Info().Msg("Repository sync completed successfully")
	},
}

func init() {
	rootCmd.AddCommand(syncReposCmd)
}
