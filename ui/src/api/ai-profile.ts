import { apiClient } from '@/lib/api-client';

export interface AIProfile {
    id: number;
    name: string;
    provider: string; // gemini, openai, etc.
    api_key?: string;
    base_url?: string;
    default_model?: string;
    is_enabled: boolean;
    is_default: boolean;
}

export interface AIProfileInput {
    name: string;
    provider: string;
    api_key?: string;
    base_url?: string;
    default_model?: string;
    is_enabled: boolean;
}

export interface UserAIPreference {
    user_id: number;
    ai_profile_id: number;
    ai_profile?: AIProfile;
}

export const aiProfileApi = {
    // Admin endpoints
    list: () =>
        apiClient.get<AIProfile[]>('/v1/admin/ai-profiles'),

    get: (id: number) =>
        apiClient.get<AIProfile>(`/v1/admin/ai-profiles/${id}`),

    create: (data: AIProfileInput) =>
        apiClient.post<AIProfile>('/v1/admin/ai-profiles', data),

    update: (id: number, data: AIProfileInput) =>
        apiClient.put<AIProfile>(`/v1/admin/ai-profiles/${id}`, data),

    delete: (id: number) =>
        apiClient.delete(`/v1/admin/ai-profiles/${id}`),

    toggle: (id: number) =>
        apiClient.patch<{ id: number; enabled: boolean; message: string }>(
            `/v1/admin/ai-profiles/${id}/toggle`
        ),

    // User preference endpoints
    getUserPreference: () =>
        apiClient.get<UserAIPreference>('/auth/ai-preference'),

    updateUserPreference: (aiProfileId: number) =>
        apiClient.post<UserAIPreference>('/auth/ai-preference', { ai_profile_id: aiProfileId }),
};

export const AI_PROVIDERS = [
    { value: 'gemini', label: 'Google Gemini' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'azure', label: 'Azure OpenAI' },
    { value: 'custom', label: 'Custom (OpenAI Compatible)' },
];
