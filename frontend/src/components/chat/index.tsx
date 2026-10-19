// ==============================================================================
// CampusGPT Frontend — Chat Components
// ==============================================================================
import React, { useRef, useEffect, useState } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { cn } from '../ui'
import { Button, Badge, Spinner, Avatar } from '../ui'
import { Copy, FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import type { Message, SourceCitation } from '../../types'
import { formatDistanceToNow } from 'date-fns'

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

// Message Bubble
interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
  onCopy?: (content: string) => void
  onRetry?: () => void
}

export const MessageBubble = ({ message, isStreaming, onCopy, onRetry }: MessageBubbleProps) => {
  const [showSources, setShowSources] = useState(false)
  const [copied, setCopied] = useState(false)

  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  const renderContent = () => {
    if (isUser) {
      return <p className="whitespace-pre-wrap">{message.content}</p>
    }

    // Render markdown for assistant messages
    const html = DOMPurify.sanitize(marked.parse(message.content || ''))
    return <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: html }} />
  }

  const handleCopy = () => {
    if (onCopy) {
      onCopy(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div
      className={cn(
        'flex gap-3 animate-in',
        isUser && 'flex-row-reverse',
        isStreaming && 'animate-pulse-soft'
      )}
      role={isAssistant ? 'status' : undefined}
      aria-live={isStreaming ? 'polite' : 'off'}
    >
      {!isUser && (
        <Avatar name="CampusGPT" size="sm" className="flex-shrink-0 mt-1" />
      )}

      <div
        className={cn(
          'max-w-[75%] lg:max-w-[60%]',
          isUser ? 'text-right' : 'text-left'
        )}
      >
        <div
          className={cn(
            'inline-block px-4 py-2.5 rounded-2xl',
            isUser
              ? 'bg-primary-600 text-white rounded-tr-sm'
              : 'bg-neutral-100 text-neutral-900 rounded-tl-sm'
          )}
        >
          {renderContent()}

          {/* Streaming cursor */}
          {isStreaming && isAssistant && (
            <span className="relative inline-block ml-1">
              <span className="animate-pulse bg-current w-0.5 h-4" aria-hidden="true" />
            </span>
          )}
        </div>

        {/* Message metadata */}
        <div className="flex items-center gap-2 mt-1.5" style={{ justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
          <time
            className="text-xs text-neutral-500"
            dateTime={message.created_at}
          >
            {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
          </time>

          {isAssistant && !isStreaming && (
            <>
              {message.tokens_used && (
                <Badge variant="neutral" className="text-xs">
                  {message.tokens_used} tokens
                </Badge>
              )}

              {/* Copy button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleCopy}
                aria-label={copied ? 'Copied' : 'Copy message'}
              >
                {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
              </Button>

              {/* Sources toggle */}
              {message.sources && message.sources.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setShowSources(!showSources)}
                  aria-label={showSources ? 'Hide sources' : 'Show sources'}
                  aria-expanded={showSources}
                >
                  {showSources ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </Button>
              )}

              {/* Retry button for failed messages */}
              {isStreaming && onRetry && (
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onRetry}>
                  <RotateCcw className="h-4 w-4" />
                </Button>
              )}
            </>
          )}
        </div>

        {/* Sources panel */}
        {showSources && message.sources && message.sources.length > 0 && (
          <SourcesPanel sources={message.sources} />
        )}
      </div>

      {isUser && <Avatar name="You" size="sm" className="flex-shrink-0 mt-1" />}
    </div>
  )
}

// Sources Panel
interface SourcesPanelProps {
  sources: SourceCitation[]
}

const SourcesPanel = ({ sources }: SourcesPanelProps) => (
  <div className="mt-3 p-3 bg-neutral-50 rounded-lg border border-neutral-200 animate-in">
    <div className="flex items-center justify-between mb-2">
      <h4 className="text-sm font-medium text-neutral-700">Sources ({sources.length})</h4>
    </div>
    <div className="space-y-2">
      {sources.map((source, index) => (
        <SourceCitationCard key={source.document_id + index} source={source} index={index + 1} />
      ))}
    </div>
  </div>
)

// Source Citation Card
const SourceCitationCard = ({ source, index }: { source: SourceCitation; index: number }) => (
  <div className="p-3 bg-white rounded border border-neutral-200">
    <div className="flex items-start gap-2">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary-100 text-primary-700 text-xs font-medium flex items-center justify-center">
        {index}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <FileText className="h-3.5 w-3.5 text-neutral-400 flex-shrink-0" aria-hidden="true" />
          <span className="text-sm font-medium text-neutral-900 truncate">{source.original_name}</span>
          {source.page_number && (
            <Badge variant="neutral" className="text-xs">
              Page {source.page_number}
            </Badge>
          )}
          <Badge variant="primary" className="text-xs">
            {Math.round(source.similarity_score * 100)}%
          </Badge>
        </div>
        <p className="text-sm text-neutral-600 line-clamp-2">{source.text_snippet}</p>
      </div>
    </div>
  </div>
)

// Chat Composer
interface ChatComposerProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

export const ChatComposer = ({ onSend, disabled, placeholder = 'Ask CampusGPT...' }: ChatComposerProps) => {
  const [content, setContent] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (content.trim() && !disabled) {
      onSend(content.trim())
      setContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [content])

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="input w-full min-h-[52px] max-h-[200px] pr-16 py-3 resize-none"
          rows={1}
          aria-label="Message input"
        />
        <div className="absolute right-3 bottom-3 flex items-center gap-1">
          <Button
            type="submit"
            variant="primary"
            size="sm"
            disabled={disabled || !content.trim()}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <p className="text-xs text-neutral-500 mt-1.5 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  )
}

// Welcome/Empty State
export const WelcomeScreen = () => (
  <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
    <div className="h-16 w-16 rounded-2xl bg-primary-100 flex items-center justify-center mb-6">
      <Bot className="h-8 w-8 text-primary-600" />
    </div>
    <h1 className="text-3xl font-bold text-neutral-900 mb-2">Welcome to CampusGPT</h1>
    <p className="text-neutral-600 mb-8 max-w-md">
      Your institutional AI assistant. Ask questions about college policies, courses, documents, and more.
    </p>
    <div className="w-full max-w-md space-y-3">
      <ExamplePrompt prompt="What's the academic calendar for 2024-25?" />
      <ExamplePrompt prompt="How do I register for courses?" />
      <ExamplePrompt prompt="Find the computer science syllabus" />
      <ExamplePrompt prompt="What are the library hours?" />
    </div>
    <p className="mt-6 text-sm text-neutral-500">
      Responses are grounded in uploaded college documents. Upload documents to expand the knowledge base.
    </p>
  </div>
)

const ExamplePrompt = ({ prompt }: { prompt: string }) => (
  <Button
    variant="secondary"
    className="w-full justify-start text-left gap-2"
    onClick={() => {}}
  >
    <MessageSquare className="h-4 w-4 text-neutral-400" />
    <span className="truncate">{prompt}</span>
  </Button>
)

// Loading State
export const ChatLoading = () => (
  <div className="flex-1 flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <Spinner size="lg" />
      <p className="text-neutral-600">CampusGPT is thinking...</p>
    </div>
  </div>
)

// Error State
interface ChatErrorProps {
  message: string
  onRetry: () => void
}

export const ChatError = ({ message, onRetry }: ChatErrorProps) => (
  <div className="flex-1 flex items-center justify-center">
    <div className="text-center px-8">
      <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-neutral-900 mb-2">Something went wrong</h3>
      <p className="text-neutral-600 mb-4">{message}</p>
      <Button variant="primary" onClick={onRetry}>
        Try Again
      </Button>
    </div>
  </div>
)

// Missing imports
import { Send, Check, RotateCcw, AlertCircle } from 'lucide-react'