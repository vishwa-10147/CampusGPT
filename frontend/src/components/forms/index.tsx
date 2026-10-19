// ==============================================================================
// CampusGPT Frontend — Form Components
// ==============================================================================
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { cn } from '../ui'
import { Button, Input, Card, Spinner } from '../ui'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

// Login Form
interface LoginFormProps {
  onSubmit: (data: { email: string; password: string }) => Promise<void>
  isLoading?: boolean
  error?: string
}

export const LoginForm = ({ onSubmit, isLoading, error }: LoginFormProps) => {
  const [showPassword, setShowPassword] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<{ email: string; password: string }>()

  return (
    <Card className="w-full max-w-md mx-auto">
      <div className="p-6 sm:p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-neutral-900">Welcome back</h1>
          <p className="text-neutral-600 mt-1">Sign in to your CampusGPT account</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <Input
            label="Email"
            type="email"
            placeholder="you@college.edu"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            })}
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              autoComplete="current-password"
              error={errors.password?.message}
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters',
                },
              })}
            />
            <button
              type="button"
              className="absolute right-3 top-[38px] text-neutral-400 hover:text-neutral-600"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            size="lg"
            loading={isLoading}
          >
            Sign In
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-neutral-600">
          Don't have an account?{' '}
          <a href="/register" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign up
          </a>
        </p>
      </div>
    </Card>
  )
}

// Register Form
interface RegisterFormProps {
  onSubmit: (data: { email: string; password: string; password_confirm: string; full_name: string }) => Promise<void>
  isLoading?: boolean
  error?: string
}

export const RegisterForm = ({ onSubmit, isLoading, error }: RegisterFormProps) => {
  const [showPassword, setShowPassword] = useState(false)
  const { register, handleSubmit, watch, formState: { errors } } = useForm<{
    email: string
    password: string
    password_confirm: string
    full_name: string
  }>()

  const password = watch('password')

  return (
    <Card className="w-full max-w-md mx-auto">
      <div className="p-6 sm:p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-neutral-900">Create an account</h1>
          <p className="text-neutral-600 mt-1">Join CampusGPT to start chatting</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <Input
            label="Full Name"
            type="text"
            placeholder="John Doe"
            autoComplete="name"
            error={errors.full_name?.message}
            {...register('full_name', { required: 'Full name is required' })}
          />

          <Input
            label="Email"
            type="email"
            placeholder="you@college.edu"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            })}
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              autoComplete="new-password"
              error={errors.password?.message}
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters',
                },
              })}
            />
            <button
              type="button"
              className="absolute right-3 top-[38px] text-neutral-400 hover:text-neutral-600"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>

          <Input
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="new-password"
            error={errors.password_confirm?.message}
            {...register('password_confirm', {
              required: 'Please confirm your password',
              validate: (value) => value === password || 'Passwords do not match',
            })}
          />

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            size="lg"
            loading={isLoading}
          >
            Create Account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-neutral-600">
          Already have an account?{' '}
          <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign in
          </a>
        </p>
      </div>
    </Card>
  )
}

// Document Upload Form
interface UploadFormProps {
  onUpload: (file: File) => Promise<void>
  isUploading?: boolean
  progress?: number
  error?: string
}

export const UploadForm = ({ onUpload, isUploading, progress, error }: UploadFormProps) => {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedFile) {
      await onUpload(selectedFile)
    }
  }

  const allowedTypes = ['application/pdf', 'text/plain', 'text/markdown']
  const maxSize = 10 * 1024 * 1024 // 10MB

  const validateFile = (file: File) => {
    if (!allowedTypes.includes(file.type)) {
      return 'File type not allowed. Please upload PDF, TXT, or MD files.'
    }
    if (file.size > maxSize) {
      return 'File too large. Maximum size is 10MB.'
    }
    return null
  }

  const validationError = selectedFile ? validateFile(selectedFile) : null

  return (
    <Card className={cn(dragActive && 'border-primary-500 bg-primary-50')}>
      <form onSubmit={handleSubmit} className="p-6">
        <div
          className={cn(
            'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
            dragActive ? 'border-primary-500 bg-primary-50' : 'border-neutral-300'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".pdf,.txt,.md"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="mx-auto h-12 w-12 text-neutral-400 mb-4">
              <Loader2 className="h-full w-full" />
            </div>
            <p className="text-lg font-medium text-neutral-900 mb-1">
              Drag & drop a document here, or click to browse
            </p>
            <p className="text-sm text-neutral-500">
              PDF, TXT, MD • Max 10MB
            </p>
          </label>
        </div>

        {selectedFile && (
          <div className="mt-4 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
                  <Loader2 className="h-5 w-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900 truncate max-w-[200px]">{selectedFile.name}</p>
                  <p className="text-sm text-neutral-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFile(null)}
                className="text-neutral-400 hover:text-neutral-600"
                aria-label="Remove file"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {validationError && (
              <p className="mt-2 text-sm text-red-600" role="alert">{validationError}</p>
            )}

            {progress !== undefined && (
              <div className="mt-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-neutral-600">Uploading...</span>
                  <span className="font-medium">{progress}%</span>
                </div>
                <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-600 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {!isUploading && !validationError && (
              <Button type="submit" variant="primary" className="mt-4 w-full" disabled={isUploading}>
                Upload Document
              </Button>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {error}
          </div>
        )}
      </form>
    </Card>
  )
}

// Missing imports
import { X } from 'lucide-react'