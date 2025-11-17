import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh or redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Analytics API
export const analyticsApi = {
  getOverview: (period: '7d' | '30d' | '90d' | 'all' = '7d') =>
    apiClient.get(`/api/v1/analytics/overview?period=${period}`),

  getEmails: (params: {
    start_date?: string;
    end_date?: string;
    listing_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => apiClient.get('/api/v1/analytics/emails', { params }),

  getTrends: (period: '7d' | '30d' | '90d' | 'all' = '30d') =>
    apiClient.get(`/api/v1/analytics/trends?period=${period}`),
};

// Review Queue API
export const reviewQueueApi = {
  getQueue: () => apiClient.get('/api/v1/review-queue'),

  approve: (threadId: string, edits?: string) =>
    apiClient.post(`/api/v1/review-queue/${threadId}/approve`, { edits }),

  manualReply: (threadId: string, bodyText: string) =>
    apiClient.post(`/api/v1/review-queue/${threadId}/manual-reply`, { body_text: bodyText }),

  markResolved: (threadId: string) =>
    apiClient.post(`/api/v1/review-queue/${threadId}/mark-resolved`),
};

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post('/api/v1/auth/login', { email, password }),

  logout: () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },
};

export default apiClient;
