import { apiClient } from '@/lib/api-client';

export interface SessionRequest {
    goal: string;
    repo_url?: string;
    repository_id?: number;
    base_branch?: string;
    mode?: 'auto' | 'review';
    ai_profile_id?: number;
    git_co_author_name?: string;
    git_co_author_email?: string;
}

export interface SessionResponse {
    session_id: string;
}

export interface SessionStatus {
    id: string; // Database ID (kept for compat or replaced?) - Actually this is likely the `ID` uint from GORM mapped to string?
    // Wait, the backend model JSON tag `id` comes from gorm.Model.
    // The backend model JSON tag `session_id` comes from SessionID field.
    // So existing `id` is probably the PK.
    // I will add `session_id: string;`
    session_id: string;
    title?: string;
    status: string;
    logs: string[];
    result?: string;
    state?: Record<string, any>;
    repository?: {
        full_name: string;
        html_url: string;
    };
    created_at?: string;
    updated_at?: string;
}

export interface SessionsResponse {
    data: SessionStatus[];
    meta: {
        total: number;
        page: number;
        per_page: number;
    };
}

export const agentApi = {
    createSession: (data: SessionRequest) =>
        apiClient.post<SessionResponse>('/v1/agent/sessions', data),

    getSessionStatus: (sessionId: string) =>
        apiClient.get<SessionStatus>(`/v1/agent/sessions/${sessionId}`),

    listSessions: (params: { page?: number; per_page?: number; status?: string }) =>
        apiClient.get<SessionsResponse>('/v1/user/sessions', { params }),

    approveSession: (sessionId: string) =>
        apiClient.post(`/v1/agent/sessions/${sessionId}/approve`, {}),

    addInput: (sessionId: string, message: string) =>
        apiClient.post(`/v1/agent/sessions/${sessionId}/input`, { message }),
};
