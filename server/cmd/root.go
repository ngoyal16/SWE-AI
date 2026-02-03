package cmd

import (
	"fmt"
	"os"
	"pixcorp-swe-ai/pkg/common"
	"pixcorp-swe-ai/pkg/logger"
	"pixcorp-swe-ai/pkg/model"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "swe-ai",
	Short: "SWE-AI Backend Server and CLI tools",
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		// Initialize configurations and logger
		common.LoadEnvs()
		logger.Setup()

		// Initialize Databases
		model.InitRedis()
		model.InitDB()
		if err := model.AutoMigrate(); err != nil {
			fmt.Printf("Failed to run migrations: %v\n", err)
			os.Exit(1)
		}
	},
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
