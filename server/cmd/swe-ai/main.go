package main

import (
	"embed"
	"pixcorp-swe-ai/cmd"
)

//go:embed ui/dist
var content embed.FS

func main() {
	// Pass the embedded UI content to the command package
	cmd.UIContent = content

	// Execute the root command
	cmd.Execute()
}
