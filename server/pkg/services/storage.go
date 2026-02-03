package services

import (
	"encoding/json"
	"fmt"
	"pixcorp-swe-ai/pkg/model"
	"time"
)

const SessionTTL = 7 * 24 * time.Hour

func SetSessionStatus(sessionID, status string) error {
	err := model.Rdb.Set(model.Ctx, fmt.Sprintf("session:%s:status", sessionID), status, SessionTTL).Err()
	if err == nil {
		SyncSessionToDB(sessionID, status, nil)
	}
	return err
}

func GetSessionStatus(sessionID string) (string, error) {
	val, err := model.Rdb.Get(model.Ctx, fmt.Sprintf("session:%s:status", sessionID)).Result()
	if err != nil {
		return "UNKNOWN", err
	}
	return val, nil
}

func GetLogs(sessionID string) ([]string, error) {
	return model.Rdb.LRange(model.Ctx, fmt.Sprintf("session:%s:logs", sessionID), 0, -1).Result()
}

func GetResult(sessionID string) (string, error) {
	val, err := model.Rdb.Get(model.Ctx, fmt.Sprintf("session:%s:result", sessionID)).Result()
	if err != nil {
		return "", nil // Not an error if just missing
	}
	return val, nil
}

func GetState(sessionID string) (map[string]interface{}, error) {
	val, err := model.Rdb.Get(model.Ctx, fmt.Sprintf("session:%s:state", sessionID)).Bytes()
	if err != nil {
		return nil, err
	}
	var state map[string]interface{}
	err = json.Unmarshal(val, &state)
	return state, err
}

func SaveState(sessionID string, state map[string]interface{}) error {
	data, err := json.Marshal(state)
	if err != nil {
		return err
	}
	err = model.Rdb.Set(model.Ctx, fmt.Sprintf("session:%s:state", sessionID), data, SessionTTL).Err()
	if err == nil {
		SyncSessionToDB(sessionID, "", state)
	}
	return err
}

func SyncSessionToDB(sessionID string, status string, state map[string]interface{}) {
	updates := make(map[string]interface{})
	if status != "" {
		updates["status"] = status
	}
	if state != nil {
		if branch, ok := state["branch_name"].(string); ok && branch != "" {
			updates["feature_branch_name"] = branch
		}
		if s, ok := state["status"].(string); ok && s != "" {
			updates["status"] = s
		}
	}

	if len(updates) > 0 {
		model.DB.Model(&model.Session{}).Where("session_id = ?", sessionID).Updates(updates)
	}
}
