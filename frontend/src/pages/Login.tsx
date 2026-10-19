// ==============================================================================
// CampusGPT Frontend — Login Page
// ==============================================================================
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import { LoginForm } from '../components/forms'
import { Bot } from 'lucide-react'

export const Login = () => {
  const { login } = useAuth()
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: { email: string; password: string }) => {
    setError('')
    setIsLoading(true)
    try {
      await login(data.email, data.password)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password')
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

        <LoginForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
      </div>
    </div>
  )
}