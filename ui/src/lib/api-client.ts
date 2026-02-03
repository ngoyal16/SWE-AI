
interface ExtendedRequestInit extends RequestInit {
    params?: Record<string, string | number | boolean | undefined>;
}

class ApiClient {
    private baseUrl: string = '';

    constructor(baseUrl: string = '') {
        this.baseUrl = baseUrl;
    }

    private async makeRequest<T>(
        url: string,
        options: ExtendedRequestInit = {}
    ): Promise<T> {
        let fullUrl = this.baseUrl + url;

        if (options.params) {
            const queryParams = new URLSearchParams();
            Object.entries(options.params).forEach(([key, value]) => {
                if (value !== undefined) {
                    queryParams.append(key, String(value));
                }
            });
            const queryString = queryParams.toString();
            if (queryString) {
                fullUrl += (fullUrl.includes('?') ? '&' : '?') + queryString;
            }
        }

        const headers: Record<string, string> = {
            ...(options.headers as Record<string, string>),
        };

        if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const defaultOptions: RequestInit = {
            credentials: 'include',
            headers,
            ...options,
        };

        // Remove params from options before passing to fetch
        delete (defaultOptions as any).params;

        try {
            const response = await fetch(fullUrl, defaultOptions);

            if (response.status === 401) {
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
                throw new Error('Authentication failed');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData.error || `HTTP error! status: ${response.status}`;
                throw new Error(message);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return (await response.text()) as T;
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get<T>(url: string, options?: ExtendedRequestInit): Promise<T> {
        return this.makeRequest<T>(url, { ...options, method: 'GET' });
    }

    async post<T>(
        url: string,
        data?: unknown,
        options?: ExtendedRequestInit
    ): Promise<T> {
        const isFormData = data instanceof FormData;
        return this.makeRequest<T>(url, {
            ...options,
            method: 'POST',
            body: isFormData
                ? (data as BodyInit)
                : data
                    ? JSON.stringify(data)
                    : undefined,
        });
    }

    async put<T>(url: string, data?: unknown, options?: ExtendedRequestInit): Promise<T> {
        const isFormData = data instanceof FormData;
        return this.makeRequest<T>(url, {
            ...options,
            method: 'PUT',
            body: isFormData
                ? (data as BodyInit)
                : data
                    ? JSON.stringify(data)
                    : undefined,
        });
    }

    async delete<T>(url: string, options?: ExtendedRequestInit): Promise<T> {
        return this.makeRequest<T>(url, { ...options, method: 'DELETE' });
    }

    async patch<T>(
        url: string,
        data?: unknown,
        options?: ExtendedRequestInit
    ): Promise<T> {
        const isFormData = data instanceof FormData;
        return this.makeRequest<T>(url, {
            ...options,
            method: 'PATCH',
            body: isFormData
                ? (data as BodyInit)
                : data
                    ? JSON.stringify(data)
                    : undefined,
        });
    }
}

export const API_BASE_URL = '/api';

// Create a singleton instance
export const apiClient = new ApiClient(API_BASE_URL);

export default apiClient;
