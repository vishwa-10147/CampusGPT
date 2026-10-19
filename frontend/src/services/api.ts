// ==============================================================================
// CampusGPT Frontend — API Client
// ==============================================================================
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { ApiError } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  withCredentials: true, // Important for HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Tokens are sent via cookies automatically with withCredentials: true
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config

    // Handle 401 - try to refresh token
    if (error.response?.status === 401 && originalRequest && !originalRequest.url?.includes('/auth/')) {
      try {
        await api.post('/auth/refresh')
        // Retry original request
        return api(originalRequest)
      } catch {
        // Refresh failed, redirect to login
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  register: (data: { email: string; password: string; password_confirm: string; full_name: string }) =>
    api.post('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  logout: () =>
    api.post('/auth/logout'),

  me: () =>
    api.get('/auth/me'),

  refresh: () =>
    api.post('/auth/refresh'),
}

// Conversation API
export const conversationApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/conversations', { params }),

  create: (data: { title?: string }) =>
    api.post('/conversations', data),

  get: (id: string) =>
    api.get(`/conversations/${id}`),

  update: (id: string, data: { title: string }) =>
    api.patch(`/conversations/${id}`, data),

  delete: (id: string) =>
    api.delete(`/conversations/${id}`),
}

// Message API
export const messageApi = {
  send: (conversationId: string, data: { content: string; stream: boolean }) =>
    api.post(`/conversations/${conversationId}/messages`, data, {
      responseType: data.stream ? 'stream' : 'json',
    }),

  retry: (conversationId: string, messageId: string) =>
    api.post(`/conversations/${conversationId}/messages/${messageId}/retry`),
}

// Document API
export const documentApi = {
  upload: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)

    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
        }
      },
    })
  },

  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get('/documents', { params }),

  get: (id: string) =>
    api.get(`/documents/${id}`),

  delete: (id: string) =>
    api.delete(`/documents/${id}`),
}

// Admin API
export const adminApi = {
  documents: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get('/admin/documents', { params }),

  stats: () =>
    api.get('/admin/stats'),
}

export default api