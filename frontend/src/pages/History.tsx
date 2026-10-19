// ==============================================================================
// CampusGPT Frontend — History Page
// ==============================================================================
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationApi } from '../services/api'
import { MainLayout } from '../components/layout'
import { Button, Card, Badge, Spinner } from '../components/ui'
import { Plus, Trash2, MessageSquare, ChevronRight, Search, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export const History = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['conversations', page, search],
    queryFn: () => conversationApi.list({ page, page_size: 20 }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => conversationApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const createMutation = useMutation({
    mutationFn: () => conversationApi.create({}),
    onSuccess: (response) => {
      const newConv = response.data
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      navigate(`/chat/${newConv.id}`)
    },
  })

  const conversations = data?.conversations || []
  const totalPages = data?.total_pages || 1

  if (isLoading && !data) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <Spinner size="lg" />
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Conversation History</h1>
            <p className="text-neutral-600 mt-1">Manage your past conversations</p>
          </div>
          <Button variant="primary" onClick={() => createMutation.mutate()}>
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
          <input
            type="search"
            placeholder="Search conversations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setPage(1)}
            className="input pl-10"
            aria-label="Search conversations"
          />
        </div>

        {/* Conversations List */}
        {conversations.length === 0 ? (
          <Card className="p-12 text-center">
            <MessageSquare className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No conversations yet</h3>
            <p className="text-neutral-600 mb-6">Start your first conversation with CampusGPT</p>
            <Button variant="primary" onClick={() => createMutation.mutate()}>
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </Card>
        ) : (
          <div className="space-y-3">
            {conversations.map((conv) => (
              <Card key={conv.id} hover className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <MessageSquare className="h-5 w-5 text-primary-600 flex-shrink-0" />
                      <h3 className="font-medium text-neutral-900 truncate">{conv.title || 'Untitled'}</h3>
                      <Badge variant="neutral" className="text-xs">{conv.message_count} messages</Badge>
                    </div>
                    <p className="text-sm text-neutral-500 truncate">
                      {conv.last_message_preview || 'No messages yet'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/chat/${conv.id}`)}
                      aria-label={`Open conversation: ${conv.title}`}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => deleteMutation.mutate(conv.id)}
                      disabled={deleteMutation.isPending}
                      aria-label={`Delete conversation: ${conv.title}`}
                    >
                      {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-neutral-100 flex items-center justify-between text-xs text-neutral-500">
                  <span>Created {formatDistanceToNow(new Date(conv.created_at), { addSuffix: true })}</span>
                  <span>Updated {formatDistanceToNow(new Date(conv.updated_at), { addSuffix: true })}</span>
                </div>
              </Card>
            ))}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  aria-label="Previous page"
                >
                  <ChevronRight className="h-4 w-4 rotate-180" />
                </Button>
                <span className="text-sm text-neutral-600 px-4">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}