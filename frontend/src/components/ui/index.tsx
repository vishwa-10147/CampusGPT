// ==============================================================================
// CampusGPT Frontend — UI Components
// ==============================================================================
import React from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

type ClassValue = string | number | boolean | undefined | null | { [key: string]: boolean } | ClassValue[]

// Button
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none'

    const variantClasses = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500',
      secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus-visible:ring-neutral-500',
      ghost: 'bg-transparent text-neutral-700 hover:bg-neutral-100 focus-visible:ring-neutral-500',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
    }

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
    }

    return (
      <button
        ref={ref}
        className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'

// Input
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && <label htmlFor={inputId} className="label">{label}</label>}
        <input
          ref={ref}
          id={inputId}
          className={cn('input', error && 'input-error', className)}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && <p id={`${inputId}-error`} className="mt-1.5 text-sm text-red-600" role="alert">{error}</p>}
        {helperText && !error && <p id={`${inputId}-helper`} className="mt-1.5 text-sm text-neutral-500">{helperText}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'

// Textarea
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && <label htmlFor={inputId} className="label">{label}</label>}
        <textarea
          ref={ref}
          id={inputId}
          className={cn('input min-h-[100px] resize-y', error && 'input-error', className)}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && <p id={`${inputId}-error`} className="mt-1.5 text-sm text-red-600" role="alert">{error}</p>}
        {helperText && !error && <p id={`${inputId}-helper`} className="mt-1.5 text-sm text-neutral-500">{helperText}</p>}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'

// Label
export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, children, ...props }, ref) => (
    <label ref={ref} className={cn('label', className)} {...props}>
      {children}
    </label>
  )
)
Label.displayName = 'Label'

// Card
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('card', hover && 'card-hover', className)}
      {...props}
    >
      {children}
    </div>
  )
)
Card.displayName = 'Card'

// Badge
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'neutral', children, ...props }, ref) => {
    const variantClasses = {
      primary: 'bg-primary-100 text-primary-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      danger: 'bg-red-100 text-red-800',
      neutral: 'bg-neutral-100 text-neutral-800',
    }

    return (
      <span
        ref={ref}
        className={cn('badge', variantClasses[variant], className)}
        {...props}
      >
        {children}
      </span>
    )
  }
)
Badge.displayName = 'Badge'

// Avatar
interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  name?: string
  src?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, name, src, size = 'md', ...props }, ref) => {
    const sizeClasses = {
      sm: 'h-8 w-8 text-xs',
      md: 'h-10 w-10 text-sm',
      lg: 'h-12 w-12 text-base',
      xl: 'h-16 w-16 text-lg',
    }

    const getInitials = (name: string) => {
      return name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }

    const bgColors = [
      'bg-primary-100 text-primary-700',
      'bg-green-100 text-green-700',
      'bg-yellow-100 text-yellow-700',
      'bg-red-100 text-red-700',
      'bg-purple-100 text-purple-700',
      'bg-pink-100 text-pink-700',
    ]

    const getColor = (name: string) => {
      let hash = 0
      for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash)
      }
      return bgColors[Math.abs(hash) % bgColors.length]
    }

    if (src) {
      return (
        <img
          ref={ref}
          src={src}
          alt={name || 'Avatar'}
          className={cn('rounded-full object-cover', sizeClasses[size], className)}
          {...props}
        />
      )
    }

    return (
      <div
        ref={ref}
        className={cn('rounded-full flex items-center justify-center font-medium', sizeClasses[size], className, getColor(name || ''))}
        {...props}
      >
        {name ? getInitials(name) : '?'}
      </div>
    )
  }
)
Avatar.displayName = 'Avatar'

// Separator
export const Separator = ({ className, ...props }: React.HTMLAttributes<HTMLHRElement>) => (
  <hr className={cn('border-neutral-200', className)} {...props} />
)

// Spinner
interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
}

export const Spinner = ({ className, size = 'md', ...props }: SpinnerProps) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div
      className={cn('animate-spin text-primary-600', sizeClasses[size], className)}
      {...props}
      role="status"
      aria-label="Loading"
    >
      <svg className="h-full w-full" viewBox="0 0 24 24" fill="none">
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
    </div>
  )
}