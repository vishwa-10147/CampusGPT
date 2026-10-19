// ==============================================================================
// CampusGPT Frontend — Login Page
// ==============================================================================
import { useState } from 'react'
import { useAuth } from '../features/auth/AuthContext'
import { ResendVerificationButton } from '../features/auth/ResendVerificationButton'
import { LoginForm } from '../components/forms'
import { AuthPageShell } from '../components/layout'

export const Login = () => {
  const { login } = useAuth()
  const [error, setError] = useState('')
  const [unverifiedEmail, setUnverifiedEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: { email: string; password: string }) => {
    setError('')
    setUnverifiedEmail('')
    setIsLoading(true)
    try {
      await login(data.email, data.password)
    } catch (err: any) {
      // 403 means the password was right but the email isn't confirmed yet
      if (err.response?.status === 403) setUnverifiedEmail(data.email)
      setError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthPageShell>
      <LoginForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
      {unverifiedEmail && (
        <div className="w-full max-w-md mx-auto mt-4">
          <ResendVerificationButton email={unverifiedEmail} />
        </div>
      )}
    </AuthPageShell>
  )
}
