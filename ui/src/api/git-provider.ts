import { apiClient } from '@/lib/api-client';

// Types for Git Providers
export interface GitProvider {
    id: number;
    name: string;
    display_name: string;
    driver: string;
    enabled: boolean;
    auth_type: string;
    client_id: string;
    has_client_secret: boolean;
    auth_url: string;
    token_url: string;
    user_info_url: string;
    scopes: string;
    redirect_url: string;
    app_id: string;
    app_name: string;
    has_private_key: boolean;
    has_webhook_secret: boolean;
    base_url: string;
    app_username: string;
    app_email: string;
    has_project_token: boolean;
}

export interface GitProviderInput {
    name: string;
    display_name: string;
    driver: string;
    enabled: boolean;
    auth_type: string;
    client_id?: string;
    client_secret?: string;
    auth_url?: string;
    token_url?: string;
    user_info_url?: string;
    scopes?: string;
    redirect_url?: string;
    app_id?: string;
    app_name?: string;
    app_username?: string;
    app_email?: string;
    private_key?: string;
    webhook_secret?: string;
    base_url?: string;
    project_access_token?: string;
}

export interface EnabledProvider {
    name: string;
    display_name: string;
    driver: string;
    auth_type: string;
}

export interface LinkedIdentity {
    id: number;
    provider: string;
    provider_id: string;
    email: string;
}

export interface Repository {
    id: number;
    provider_id: number;
    name: string;
    full_name: string;
    url: string;
    ssh_url: string;
    clone_url: string;
    default_branch: string;
    language: string;
    stars: number;
    private: boolean;
    external_id: string;
    provider?: {
        id: number;
        name: string;
        display_name: string;
        driver: string;
    };
}

export const gitProviderApi = {
    // Public endpoint (no auth required)
    getEnabledProviders: () =>
        apiClient.get<EnabledProvider[]>('/auth/providers'),

    // Admin endpoints (auth required)
    list: () =>
        apiClient.get<GitProvider[]>('/v1/admin/git-providers'),

    get: (id: number) =>
        apiClient.get<GitProvider>(`/v1/admin/git-providers/${id}`),

    create: (data: GitProviderInput) =>
        apiClient.post<GitProvider>('/v1/admin/git-providers', data),

    update: (id: number, data: GitProviderInput) =>
        apiClient.put<GitProvider>(`/v1/admin/git-providers/${id}`, data),

    delete: (id: number) =>
        apiClient.delete(`/v1/admin/git-providers/${id}`),

    toggle: (id: number) =>
        apiClient.patch<{ id: number; enabled: boolean; message: string }>(
            `/v1/admin/git-providers/${id}/toggle`
        ),

    // User identity endpoints (auth required)
    getIdentities: () =>
        apiClient.get<LinkedIdentity[]>('/auth/identities'),

    unlink: (provider: string) =>
        apiClient.delete<{ message: string }>(`/auth/identities/${provider}`),

    getUserRepositories: (params?: { q?: string; page?: number; per_page?: number }) =>
        apiClient.get<RepositoryResponse>('/v1/user/repositories', { params }),
};

export interface RepositoryResponse {
    data: Repository[];
    meta: {
        total: number;
        page: number;
        per_page: number;
    };
}

// Driver options for UI
export const GIT_DRIVERS = [
    { value: 'github', label: 'GitHub' },
    { value: 'gitlab', label: 'GitLab' },
    { value: 'bitbucket', label: 'Bitbucket' },
];

// Auth type options for UI
export const AUTH_TYPES = [
    { value: 'oauth', label: 'OAuth 2.0' },
    { value: 'github_app', label: 'GitHub App' },
];

// Default OAuth URLs for each driver
export const DEFAULT_PROVIDER_URLS: Record<string, {
    authUrl: string;
    tokenUrl: string;
    userInfoUrl: string;
    scopes: string;
}> = {
    github: {
        authUrl: 'https://github.com/login/oauth/authorize',
        tokenUrl: 'https://github.com/login/oauth/access_token',
        userInfoUrl: 'https://api.github.com/user',
        scopes: 'repo,user:email',
    },
    gitlab: {
        authUrl: 'https://gitlab.com/oauth/authorize',
        tokenUrl: 'https://gitlab.com/oauth/token',
        userInfoUrl: 'https://gitlab.com/api/v4/user',
        scopes: 'api,read_user,read_repository,write_repository',
    },
    bitbucket: {
        authUrl: 'https://bitbucket.org/site/oauth2/authorize',
        tokenUrl: 'https://bitbucket.org/site/oauth2/access_token',
        userInfoUrl: 'https://api.bitbucket.org/2.0/user',
        scopes: 'account,repository',
    },
};
