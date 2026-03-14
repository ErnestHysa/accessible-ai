/** API client for AccessibleAI backend. */

import axios, { AxiosError } from 'axios';
import type { User, TokenResponse, Website, Scan, Issue, Subscription, SubscriptionTierInfo, Usage } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post<TokenResponse>(
            `${API_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken }
          );
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);
          // Retry original request
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
            return api.request(error.config);
          }
        } catch {
          // Refresh failed, logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (email: string, password: string, name?: string) => {
    const response = await api.post<TokenResponse>('/api/v1/auth/register', {
      email,
      password,
      name,
    });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post<TokenResponse>('/api/v1/auth/login', { email, password });
    return response.data;
  },

  logout: async () => {
    await api.post('/api/v1/auth/logout');
  },

  getMe: async () => {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },
};

// Websites API
export const websitesApi = {
  list: async () => {
    const response = await api.get<Website[]>('/api/v1/websites');
    return response.data;
  },

  create: async (url: string, name?: string, platform: string = 'generic') => {
    const response = await api.post<Website>('/api/v1/websites', { url, name, platform });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<Website>(`/api/v1/websites/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Website>) => {
    const response = await api.put<Website>(`/api/v1/websites/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/api/v1/websites/${id}`);
  },

  triggerScan: async (id: string, fullScan = false) => {
    const response = await api.post<{ scan_id: string; status: string; message: string }>(
      `/api/v1/websites/${id}/scan`,
      { full_scan: fullScan }
    );
    return response.data;
  },
};

// Scans API
export const scansApi = {
  list: async (websiteId?: string) => {
    const params = websiteId ? { website_id: websiteId } : {};
    const response = await api.get<Scan[]>('/api/v1/scans', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<Scan>(`/api/v1/scans/${id}`);
    return response.data;
  },

  getIssues: async (id: string, severity?: string, isFixed?: boolean) => {
    const params: any = {};
    if (severity) params.severity = severity;
    if (isFixed !== undefined) params.is_fixed = isFixed;

    const response = await api.get<Issue[]>(`/api/v1/scans/${id}/issues`, { params });
    return response.data;
  },

  getIssue: async (id: string) => {
    const response = await api.get<Issue>(`/api/v1/scans/issues/${id}`);
    return response.data;
  },

  applyFix: async (id: string, autoApply = false) => {
    const response = await api.post<{
      success: boolean;
      message: string;
      fix_applied: boolean;
      fix_code?: string;
    }>(`/api/v1/scans/issues/${id}/fix`, { auto_apply: autoApply });
    return response.data;
  },
};

// Subscription API
export const subscriptionApi = {
  getTiers: async () => {
    const response = await api.get<SubscriptionTierInfo[]>('/api/v1/tiers');
    return response.data;
  },

  getSubscription: async () => {
    const response = await api.get<Subscription>('/api/v1/subscription');
    return response.data;
  },

  checkout: async (tier: string) => {
    const response = await api.post<{ checkout_url: string; session_id: string }>(
      '/api/v1/checkout',
      { tier }
    );
    return response.data;
  },

  portal: async () => {
    const response = await api.post<{ portal_url: string }>('/api/v1/portal');
    return response.data;
  },

  getUsage: async () => {
    const response = await api.get<Usage>('/api/v1/usage');
    return response.data;
  },
};

export default api;
