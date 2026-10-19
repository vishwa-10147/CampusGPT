// ==============================================================================
// CampusGPT Frontend — Chat Page
// ==============================================================================
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationApi, messageApi } from '../services/api'
import { MessageBubble, ChatComposer, WelcomeScreen, ChatLoading, ChatError } from '../components/chat'
import { Sidebar, MainLayout } from '../components/layout'
import { Button, Spinner } from '../components/ui'
import { Plus, Send, Trash2, Edit2, Loader2 } from 'lucide-react'
import type { Conversation, Message } from '../types'
import { formatDistanceToNow } from 'date-fns'

export const Chat = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { conversationId } = useParams<{ conversationId: string }>()

  // State
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch conversations
  const { data: conversationsData, isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationApi.list(),
  })

  useEffect(() => {
    if (conversationsData) {
      setConversations(conversationsData.conversations)
    }
  }, [conversationsData])

  // Fetch messages for current conversation
  useEffect(() => {
    if (conversationId) {
      fetchConversation(conversationId)
    } else {
      setCurrentConversation(null)
      setMessages([])
    }
  }, [conversationId])

  const fetchConversation = async (id: string) => {
    try {
      const response = await conversationApi.get(id)
      setCurrentConversation(response.data)
      setMessages(response.data.messages || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load conversation')
      navigate('/chat')
    }
  }

  // Create new conversation
  const createConversation = useMutation({
    mutationFn: () => conversationApi.create({}),
    onSuccess: (response) => {
      const newConv = response.data
      setConversations(prev => [newConv, ...prev])
      navigate(`/chat/${newConv.id}`)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create conversation')
    },
  })

  // Send message
  const sendMessage = useMutation({
    mutationFn: (content: string) => {
      if (!currentConversation) throw new Error('No conversation selected')
      return messageApi.send(currentConversation.id, { content, stream: true })
    },
    onMutate: async (content) => {
      // Optimistic update - add user message
      const tempUserMessage: Message = {
        id: 'temp-' + Date.now(),
        conversation_id: currentConversation!.id,
        role: 'user',
        content,
        sources: null,
        tokens_used: null,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, tempUserMessage])
      setIsLoading(true)
      setError(null)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to send message')
      setIsLoading(false)
    },
  })

  // Handle streaming response
  const handleStreamResponse = useCallback(async (content: string) => {
    if (!currentConversation) return

    sendMessage.mutate(content, {
      onSuccess: async (response) => {
        // Handle streaming response
        const reader = response.data.getReader()
        const decoder = new TextDecoder()
        let assistantContent = ''
        let sources: any[] = []
        let tokensUsed = 0
        let messageId: string | null = null

        // Add temporary assistant message
        const tempId = 'temp-assistant-' + Date.now()
        const tempAssistantMessage: Message = {
          id: tempId,
          conversation_id: currentConversation.id,
          role: 'assistant',
          content: '',
          sources: [],
          tokens_used: 0,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => [...prev, tempAssistantMessage])

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                const event = line.slice(7)
                const dataLine = lines[lines.indexOf(line) + 1]
                if (dataLine?.startsWith('data: ')) {
                  const data = JSON.parse(dataLine.slice(6))

                  if (event === 'token' && data.token) {
                    assistantContent += data.token
                    setMessages(prev => prev.map(m =>
                      m.id === tempId ? { ...m, content: assistantContent } : m
                    ))
                  } else if (event === 'sources') {
                    sources = data.sources
                    setMessages(prev => prev.map(m =>
                      m.id === tempId ? { ...m, sources } : m
                    ))
                  } else if (event === 'done') {
                    tokensUsed = data.tokens_used || 0
                    messageId = data.message_id
                  } else if (event === 'error') {
                    throw new Error(data.error)
                  }
                }
              }
            }
          }

          // Replace temp message with real one
          setMessages(prev => prev.filter(m => m.id !== tempId))
          queryClient.invalidateQueries({ queryKey: ['conversations'] })
          queryClient.invalidateQueries({ queryKey: ['conversation', currentConversation.id] })
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Streaming error')
          setMessages(prev => prev.filter(m => m.id !== tempId))
        } finally {
          setIsLoading(false)
        }
      },
      onError: () => {
        setIsLoading(false)
      },
    })
  }, [currentConversation, sendMessage, queryClient, navigate])

  // Delete conversation
  const deleteConversation = useMutation({
    mutationFn: (id: string) => conversationApi.delete(id),
    onSuccess: (_, id) => {
      setConversations(prev => prev.filter(c => c.id !== id))
      if (currentConversation?.id === id) {
        navigate('/chat')
      }
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to delete conversation')
    },
  })

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // Render
  const handleNewChat = () => {
    createConversation.mutate()
  }

  return (
    <MainLayout>
      <div className="h-full flex flex-col">
        {/* Chat Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">
                {currentConversation?.title || 'New Conversation'}
              </h1>
              <p className="text-sm text-neutral-500">
                {currentConversation
                  ? `${messages.length} messages • Updated ${formatDistanceToNow(new Date(currentConversation.updated_at), { addSuffix: true })}`
                  : 'Start a new conversation'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {currentConversation && (
                <>
                  <Button variant="ghost" size="sm" onClick={() => {}} aria-label="Edit title">
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" variant="danger" onClick={() => deleteConversation.mutate(currentConversation.id)} aria-label="Delete conversation">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
              <Button variant="primary" onClick={handleNewChat} className="lg:hidden">
                <Plus className="h-4 w-4" />
                New Chat
              </Button>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {currentConversation ? (
            <>
              {messages.length === 0 ? (
                <WelcomeScreen />
              ) : (
                <div
                  className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin"
                  role="log"
                  aria-live="polite"
                  aria-label="Conversation"
                >
                  {messages.map((message) => (
                    <MessageBubble
                      key={message.id}
                      message={message}
                      isStreaming={message.id.startsWith('temp-assistant') && isLoading}
                    />
                  ))}
                  {isLoading && <ChatLoading />}
                  {error && <ChatError message={error} onRetry={() => setError(null)} />}
                  <div ref={messagesEndRef} />
                </div>
              )}

              {/* Composer */}
              <div className="border-t border-neutral-200 p-4 bg-white">
                <ChatComposer
                  onSend={handleStreamResponse}
                  disabled={isLoading || !currentConversation}
                  placeholder={currentConversation ? 'Ask CampusGPT...' : 'Start a new conversation to chat'}
                />
              </div>
            </>
          ) : (
            <WelcomeScreen />
          )}
        </div>
      </div>
    </MainLayout>
  )
}