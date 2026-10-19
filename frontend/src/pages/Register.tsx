// ==============================================================================
// CampusGPT Frontend — Register Page
// ==============================================================================
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MailCheck } from 'lucide-react'
import { useAuth } from '../features/auth/AuthContext'
import { ResendVerificationButton } from '../features/auth/ResendVerificationButton'
import { RegisterForm } from '../components/forms'
import { AuthPageShell } from '../components/layout'
import { Card } from '../components/ui'

export const Register = () => {
  const { register } = useAuth()
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pendingEmail, setPendingEmail] = useState('')

  const handleSubmit = async (data: { email: string; password: string; password_confirm: string; full_name: string }) => {
    setError('')
    setIsLoading(true)
    try {
      const { verificationRequired } = await register(data)
      if (verificationRequired) setPendingEmail(data.email)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthPageShell>
      {pendingEmail ? (
        <Card className="w-full max-w-md mx-auto">
          <div className="p-6 sm:p-8 text-center space-y-4">
            <MailCheck className="h-10 w-10 text-primary-600 mx-auto" />
            <h1 className="text-2xl font-bold text-neutral-900">Check your email</h1>
            <p className="text-neutral-600">
              We sent a confirmation link to <strong>{pendingEmail}</strong>. Open it to activate your account.
            </p>
            <ResendVerificationButton email={pendingEmail} />
            <p className="text-sm text-neutral-600">
              Already confirmed? <Link to="/login" className="text-primary-600 font-medium hover:underline">Sign in</Link>
            </p>
          </div>
        </Card>
      ) : (
        <RegisterForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
      )}
    </AuthPageShell>
  )
}
