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

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          // Try to refresh the token
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: new_refresh_token } = response.data;

          // Save new tokens
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', new_refresh_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
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

  refresh: (refreshToken: string) =>
    apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),

  getProfile: () => apiClient.get('/api/v1/brokers/me'),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  },
};

// Listings API
export const listingsApi = {
  getListings: (params?: {
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => apiClient.get('/api/v1/listings', { params }),

  getListing: (id: string) =>
    apiClient.get(`/api/v1/listings/${id}`),

  createListing: (data: {
    code: string;
    title: string;
    status: string;
    asking_price?: number;
    revenue?: number;
    sde?: number;
    location_region?: string;
    confidentiality_level: string;
    short_description?: string;
    notes?: string;
  }) => apiClient.post('/api/v1/listings', data),

  updateListing: (id: string, data: Partial<{
    title: string;
    status: string;
    asking_price: number;
    revenue: number;
    sde: number;
    location_region: string;
    confidentiality_level: string;
    short_description: string;
    notes: string;
  }>) => apiClient.patch(`/api/v1/listings/${id}`, data),

  deleteListing: (id: string) =>
    apiClient.delete(`/api/v1/listings/${id}`),

  uploadDocument: (listingId: string, file: File, documentType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    return apiClient.post(`/api/v1/listings/${listingId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getDocuments: (listingId: string) =>
    apiClient.get(`/api/v1/listings/${listingId}/documents`),
};

export default apiClient;
