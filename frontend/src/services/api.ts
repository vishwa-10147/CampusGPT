// ==============================================================================
// CampusGPT Frontend — API Client
// ==============================================================================
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { ApiError, ConversationListResponse, DocumentListResponse } from '../types'

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
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const isAuthEndpoint = /\/auth\/(login|register|refresh|logout)/.test(originalRequest?.url ?? '')

    // Handle 401 - refresh the access token once, then retry
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      try {
        await api.post('/auth/refresh')
        return api(originalRequest)
      } catch {
        // Refresh failed, redirect to login
        if (!['/login', '/register'].includes(window.location.pathname)) {
          window.location.href = '/login'
        }
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
    api.get<ConversationListResponse>('/conversations', { params }),

  create: (data: { title?: string }) =>
    api.post('/conversations', data),

  get: (id: string) =>
    api.get(`/conversations/${id}`),

  update: (id: string, data: { title: string }) =>
    api.patch(`/conversations/${id}`, data),

  delete: (id: string) =>
    api.delete(`/conversations/${id}`),
}

export interface StreamEvent {
  event: string
  data: any
}

// Axios can't stream response bodies in the browser, so SSE goes through fetch
async function* streamMessage(conversationId: string, content: string): AsyncGenerator<StreamEvent> {
  const send = () =>
    fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ content, stream: true }),
    })

  let response = await send()
  if (response.status === 401) {
    await api.post('/auth/refresh')
    response = await send()
  }
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // Events are separated by a blank line; keep any partial event in the buffer
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      let event = 'message'
      const dataLines: string[] = []
      for (const line of part.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7).trim()
        else if (line.startsWith('data: ')) dataLines.push(line.slice(6))
      }
      if (dataLines.length) yield { event, data: JSON.parse(dataLines.join('\n')) }
    }
  }
}

// Message API
export const messageApi = {
  send: (conversationId: string, data: { content: string }) =>
    api.post(`/conversations/${conversationId}/messages`, { ...data, stream: false }),

  stream: streamMessage,

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
    api.get<DocumentListResponse>('/documents', { params }),

  get: (id: string) =>
    api.get(`/documents/${id}`),

  delete: (id: string) =>
    api.delete(`/documents/${id}`),

  reprocess: (id: string) =>
    api.post(`/documents/${id}/reprocess`),
}

// Admin API
export const adminApi = {
  documents: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get<DocumentListResponse>('/admin/documents', { params }),

  stats: () =>
    api.get('/admin/stats'),
}

export default api