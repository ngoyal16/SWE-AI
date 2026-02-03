import { apiClient } from '@/lib/api-client';

export interface User {
    id: string;
    email: string;
    name?: string;
    avatar_url?: string;
    is_admin?: boolean;
}

export const authApi = {
    me: () => apiClient.get<User>('/auth/me'),
    login: (provider: string, config?: any) => apiClient.post(`/auth/login/${provider}`, config),
    logout: () => apiClient.post('/auth/logout'),
};
