// ==============================================================================
// CampusGPT Frontend — Type Definitions
// ==============================================================================

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  message_count: number
  last_message_preview: string | null
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources: SourceCitation[] | null
  tokens_used: number | null
  created_at: string
}

export interface SourceCitation {
  document_id: string
  filename: string
  original_name: string
  chunk_index: number
  page_number: number | null
  similarity_score: number
  text_snippet: string
}

export interface Document {
  id: string
  filename: string
  original_name: string
  mime_type: string
  size_bytes: number
  uploaded_by: string | null
  status: 'pending' | 'processing' | 'ready' | 'failed'
  created_at: string
  updated_at: string
  completed_at: string | null
  chunk_count: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
}

export interface StreamingToken {
  token: string
  message_id?: string
  done: boolean
  sources?: SourceCitation[]
  tokens_used?: number
  error?: string
}
export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
