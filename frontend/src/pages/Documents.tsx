// ==============================================================================
// CampusGPT Frontend — Documents Page
// ==============================================================================
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentApi } from '../services/api'
import { MainLayout } from '../components/layout'
import { Button, Card, Badge, Spinner } from '../components/ui'
import { UploadForm } from '../components/forms'
import { useAuth } from '../features/auth/AuthContext'
import { FileText, Trash2, RefreshCw, Loader2, Eye, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const STATUS_CONFIG = {
  pending: { label: 'Pending', icon: Clock, color: 'neutral' as const },
  processing: { label: 'Processing', icon: Loader2, color: 'warning' as const },
  ready: { label: 'Ready', icon: CheckCircle, color: 'success' as const },
  failed: { label: 'Failed', icon: AlertCircle, color: 'danger' as const },
}

export const Documents = () => {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const { user } = useAuth()
  const [shareWithEveryone, setShareWithEveryone] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['documents', page, statusFilter],
    queryFn: () => documentApi.list({ page, page_size: 20, status: statusFilter || undefined }).then(r => r.data),
    // Poll while any document is still being processed
    refetchInterval: (query) =>
      query.state.data?.documents.some(d => d.status === 'pending' || d.status === 'processing') ? 3000 : false,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentApi.upload(file, { shareWithEveryone }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const reprocessMutation = useMutation({
    mutationFn: (id: string) => documentApi.reprocess(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const documents = data?.documents || []
  const totalPages = data?.total_pages || 1

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Documents</h1>
            <p className="text-neutral-600 mt-1">Manage your uploaded documents</p>
          </div>
        </div>

        {/* Upload Form */}
        <Card>
          <div className="p-6 border-b border-neutral-200">
            <h2 className="text-lg font-semibold text-neutral-900 mb-2">Upload New Document</h2>
            <p className="text-sm text-neutral-600">
              Supported: PDF, TXT, MD • Max 10MB • Only you can search your uploads
            </p>
          </div>
          <div className="p-6 space-y-4">
            {user?.is_admin && (
              <label className="flex items-start gap-2 text-sm text-neutral-700">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={shareWithEveryone}
                  onChange={e => setShareWithEveryone(e.target.checked)}
                />
                <span>
                  Share with everyone: add this document to the campus knowledge base so every user's
                  answers can use it.
                </span>
              </label>
            )}
            <UploadForm
              onUpload={async (file) => { await uploadMutation.mutateAsync(file) }}
              isUploading={uploadMutation.isPending}
              error={
                uploadMutation.error
                  ? (uploadMutation.error as any).response?.data?.detail || 'Upload failed. Please try again.'
                  : undefined
              }
            />
          </div>
        </Card>

        {/* Filters */}
        <Card>
          <div className="p-4 border-b border-neutral-200">
            <div className="flex flex-wrap gap-2">
              {[
                null,
                'pending',
                'processing',
                'ready',
                'failed',
              ].map((status) => (
                <Button
                  key={status || 'all'}
                  variant={statusFilter === status ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => { setStatusFilter(status); setPage(1); }}
                >
                  {status ? STATUS_CONFIG[status as keyof typeof STATUS_CONFIG].label : 'All'}
                </Button>
              ))}
            </div>
          </div>
        </Card>

        {/* Documents List */}
        {isLoading ? (
          <div className="flex justify-center p-12">
            <Spinner size="lg" />
          </div>
        ) : documents.length === 0 ? (
          <Card className="p-12 text-center">
            <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No documents yet</h3>
            <p className="text-neutral-600">Upload a document to get started</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const statusConfig = STATUS_CONFIG[doc.status as keyof typeof STATUS_CONFIG]
              const Icon = statusConfig.icon

              return (
                <Card key={doc.id} hover className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
                        <FileText className="h-6 w-6 text-primary-600" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-neutral-900 truncate">{doc.original_name}</h3>
                          <Badge variant={statusConfig.color}>
                            <Icon className="h-3 w-3 mr-1 inline" />
                            {statusConfig.label}
                          </Badge>
                          <Badge variant={doc.visibility === 'public' ? 'primary' : 'neutral'}>
                            {doc.visibility === 'public' ? 'Shared' : 'Private'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-neutral-500">
                          <span>{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                          <span>{doc.chunk_count} chunks</span>
                          <span>{formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {doc.status === 'ready' && (
                        <Button variant="ghost" size="sm" onClick={() => {}} aria-label="View document">
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                      {doc.status === 'failed' && (
                        <Button variant="ghost" size="sm" onClick={() => reprocessMutation.mutate(doc.id)} aria-label="Retry processing">
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => deleteMutation.mutate(doc.id)}
                        disabled={deleteMutation.isPending}
                        aria-label={`Delete ${doc.original_name}`}
                      >
                        {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </Card>
              )
            })}

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

// Missing import
import { ChevronRight } from 'lucide-react'