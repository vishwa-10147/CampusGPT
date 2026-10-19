// ==============================================================================
// CampusGPT Frontend — Chat Page
// ==============================================================================
import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationApi, messageApi } from '../services/api'
import { MessageBubble, ChatComposer, WelcomeScreen, ChatError } from '../components/chat'
import { MainLayout } from '../components/layout'
import { Button } from '../components/ui'
import { Plus, Trash2, Edit2 } from 'lucide-react'
import type { Conversation, Message } from '../types'
import { formatDistanceToNow } from 'date-fns'

export const Chat = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { conversationId } = useParams<{ conversationId: string }>()

  // State
  const [messages, setMessages] = useState<Message[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const createdHereRef = useRef<string | null>(null)

  // Fetch messages for current conversation
  useEffect(() => {
    if (conversationId && conversationId === createdHereRef.current) {
      // Just created by the first message; local state is already current
      createdHereRef.current = null
    } else if (conversationId) {
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
      navigate(`/chat/${newConv.id}`)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create conversation')
    },
  })

  // Send a message and stream the assistant reply
  const handleStreamResponse = useCallback(async (content: string) => {
    let conversationIdForSend = currentConversation?.id
    if (!conversationIdForSend) {
      // First message: create the conversation, titled after the question
      try {
        const { data: newConv } = await conversationApi.create({ title: content.slice(0, 60) })
        conversationIdForSend = newConv.id as string
        createdHereRef.current = newConv.id
        setCurrentConversation(newConv)
        navigate(`/chat/${newConv.id}`, { replace: true })
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create conversation')
        return
      }
    }
    const now = Date.now()
    const tempUserId = 'temp-' + now
    const tempId = 'temp-assistant-' + now

    setMessages(prev => [
      ...prev,
      {
        id: tempUserId,
        conversation_id: conversationIdForSend,
        role: 'user',
        content,
        sources: null,
        tokens_used: null,
        created_at: new Date().toISOString(),
      },
      {
        id: tempId,
        conversation_id: conversationIdForSend,
        role: 'assistant',
        content: '',
        sources: [],
        tokens_used: 0,
        created_at: new Date().toISOString(),
      },
    ])
    setIsLoading(true)
    setError(null)

    const updateAssistant = (patch: Partial<Message>) =>
      setMessages(prev => prev.map(m => (m.id === tempId ? { ...m, ...patch } : m)))

    let assistantContent = ''
    try {
      for await (const { event, data } of messageApi.stream(conversationIdForSend!, content)) {
        if (event === 'user_message') {
          setMessages(prev => prev.map(m => (m.id === tempUserId ? data : m)))
        } else if (event === 'token' && data.token) {
          assistantContent += data.token
          updateAssistant({ content: assistantContent })
        } else if (event === 'sources') {
          updateAssistant({ sources: Array.isArray(data) ? data : data.sources })
        } else if (event === 'done') {
          // Swap the temp id for the saved one so the message stays in the list
          updateAssistant({
            id: data.message_id ?? tempId,
            sources: data.sources ?? undefined,
            tokens_used: data.tokens_used ?? 0,
          })
        } else if (event === 'error') {
          throw new Error(data.error || 'The model failed to respond')
        }
      }
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Streaming error')
      setMessages(prev => prev.filter(m => m.id !== tempId))
    } finally {
      setIsLoading(false)
    }
  }, [currentConversation, queryClient, navigate])

  // Delete conversation
  const deleteConversation = useMutation({
    mutationFn: (id: string) => conversationApi.delete(id),
    onSuccess: (_, id) => {
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
                  <Button size="sm" variant="danger" onClick={() => deleteConversation.mutate(currentConversation.id)} aria-label="Delete conversation">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
              <Button variant="primary" onClick={handleNewChat}>
                <Plus className="h-4 w-4" />
                New Chat
              </Button>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {messages.length === 0 ? (
            <WelcomeScreen onPromptClick={isLoading ? undefined : handleStreamResponse} />
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
              {error && <ChatError message={error} onRetry={() => setError(null)} />}
              <div ref={messagesEndRef} />
            </div>
          )}
          {error && messages.length === 0 && <ChatError message={error} onRetry={() => setError(null)} />}

          {/* Composer */}
          <div className="border-t border-neutral-200 p-4 bg-white">
            <ChatComposer
              onSend={handleStreamResponse}
              disabled={isLoading}
              placeholder="Ask CampusGPT..."
            />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}