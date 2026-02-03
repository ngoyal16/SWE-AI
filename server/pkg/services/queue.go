package services

import (
	"encoding/json"
	"pixcorp-swe-ai/pkg/model"
)

type TaskPayload struct {
	SessionID   string  `json:"session_id"`
	Goal        string  `json:"goal"`
	RepoURL     string  `json:"repo_url"`
	BaseBranch  *string `json:"base_branch"`
	Mode        string  `json:"mode"`
	WorkerToken string  `json:"worker_token"`
}

func EnqueueTask(payload TaskPayload) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	return model.Rdb.RPush(model.Ctx, "swe_agent_tasks", data).Err()
}
