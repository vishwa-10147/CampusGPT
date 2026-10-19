// ==============================================================================
// CampusGPT Frontend — Admin Page
// ==============================================================================
import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../services/api'
import { MainLayout } from '../components/layout'
import { Card, Button, Badge, Spinner } from '../components/ui'
import { Users, FileText, Trash2, RefreshCw, Loader2, Search, Eye, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const STATUS_CONFIG = {
  pending: { label: 'Pending', icon: Clock, color: 'neutral' as const },
  processing: { label: 'Processing', icon: Loader2, color: 'warning' as const },
  ready: { label: 'Ready', icon: CheckCircle, color: 'success' as const },
  failed: { label: 'Failed', icon: AlertCircle, color: 'danger' as const },
}

export const Admin = () => {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-documents', page, statusFilter],
    queryFn: () => adminApi.documents({ page, page_size: 50, status: statusFilter || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.documents({ page: 1, page_size: 1 }), // Would need delete endpoint
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-documents'] })
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
            <h1 className="text-2xl font-bold text-neutral-900">Admin Dashboard</h1>
            <p className="text-neutral-600 mt-1">Manage all documents and users</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-primary-100 flex items-center justify-center">
                <FileText className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900">{data?.total || 0}</p>
                <p className="text-sm text-neutral-500">Total Documents</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900">
                  {documents.filter(d => d.status === 'ready').length}
                </p>
                <p className="text-sm text-neutral-500">Ready</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-yellow-100 flex items-center justify-center">
                <Loader2 className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900">
                  {documents.filter(d => d.status === 'processing').length}
                </p>
                <p className="text-sm text-neutral-500">Processing</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-red-100 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-neutral-900">
                  {documents.filter(d => d.status === 'failed').length}
                </p>
                <p className="text-sm text-neutral-500">Failed</p>
              </div>
            </div>
          </Card>
        </div>

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

        {/* Documents Table */}
        {documents.length === 0 ? (
          <Card className="p-12 text-center">
            <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No documents found</h3>
            <p className="text-neutral-600">No documents match the current filter</p>
          </Card>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full" role="table">
                <thead>
                  <tr className="border-b border-neutral-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Document</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Uploaded By</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Size</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Chunks</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Created</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {documents.map((doc) => {
                    const statusConfig = STATUS_CONFIG[doc.status as keyof typeof STATUS_CONFIG]
                    const Icon = statusConfig.icon

                    return (
                      <tr key={doc.id} className="hover:bg-neutral-50">
                        <td className="px-4 py-4">
                          <div>
                            <p className="font-medium text-neutral-900 truncate max-w-xs">{doc.original_name}</p>
                            <p className="text-xs text-neutral-500">{doc.filename}</p>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <Badge variant={statusConfig.color} className="flex items-center gap-1">
                            <Icon className="h-3 w-3" />
                            {statusConfig.label}
                          </Badge>
                        </td>
                        <td className="px-4 py-4 text-sm text-neutral-600">
                          {doc.uploaded_by ? 'User' : 'System'}
                        </td>
                        <td className="px-4 py-4 text-sm text-neutral-600">
                          {(doc.size_bytes / 1024 / 1024).toFixed(2)} MB
                        </td>
                        <td className="px-4 py-4 text-sm text-neutral-600">
                          {doc.chunk_count}
                        </td>
                        <td className="px-4 py-4 text-sm text-neutral-600">
                          {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                        </td>
                        <td className="px-4 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => {}} aria-label="View">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              variant="danger"
                              onClick={() => deleteMutation.mutate(doc.id)}
                              disabled={deleteMutation.isPending}
                              aria-label={`Delete ${doc.original_name}`}
                            >
                              {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-4 border-t border-neutral-200 flex items-center justify-center gap-2">
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
          </Card>
        )}
      </div>
    </MainLayout>
  )
}

// Missing import
import { ChevronRight } from 'lucide-react'