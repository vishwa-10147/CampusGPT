// ==============================================================================
// CampusGPT Frontend — Register Page
// ==============================================================================
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import { RegisterForm } from '../components/forms'
import { Bot } from 'lucide-react'

export const Register = () => {
  const { register } = useAuth()
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: { email: string; password: string; password_confirm: string; full_name: string }) => {
    setError('')
    setIsLoading(true)
    try {
      await register(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 px-4 py-12">
      <div className="w-full">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link to="/" className="flex items-center gap-2" aria-label="CampusGPT Home">
            <div className="h-10 w-10 rounded-xl bg-primary-600 flex items-center justify-center">
              <Bot className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-neutral-900">CampusGPT</span>
          </Link>
        </div>

        <RegisterForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
      </div>
    </div>
  )
}