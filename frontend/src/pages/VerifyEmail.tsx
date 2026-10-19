// ==============================================================================
// CampusGPT Frontend — Email Confirmation Page
// ==============================================================================
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle, XCircle } from 'lucide-react'
import { authApi } from '../services/api'
import { AuthPageShell } from '../components/layout'
import { Card, Spinner } from '../components/ui'

export const VerifyEmail = () => {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [state, setState] = useState<'checking' | 'done' | 'failed'>('checking')
  const [message, setMessage] = useState('')
  const requested = useRef(false)

  useEffect(() => {
    // StrictMode mounts effects twice in development; confirm only once
    if (requested.current) return
    requested.current = true
    if (!token) {
      setState('failed')
      setMessage('This link is missing its confirmation token.')
      return
    }
    authApi
      .verifyEmail(token)
      .then(() => setState('done'))
      .catch((err: any) => {
        setState('failed')
        setMessage(err.response?.data?.detail || 'This link is invalid or has expired.')
      })
  }, [token])

  return (
    <AuthPageShell>
      <Card className="w-full max-w-md mx-auto">
        <div className="p-6 sm:p-8 text-center space-y-4">
          {state === 'checking' && (
            <>
              <Spinner size="lg" />
              <p className="text-neutral-600">Confirming your email…</p>
            </>
          )}
          {state === 'done' && (
            <>
              <CheckCircle className="h-10 w-10 text-green-600 mx-auto" />
              <h1 className="text-2xl font-bold text-neutral-900">Email confirmed</h1>
              <p className="text-neutral-600">Your account is ready.</p>
              <Link to="/login" className="inline-block text-primary-600 font-medium hover:underline">Sign in</Link>
            </>
          )}
          {state === 'failed' && (
            <>
              <XCircle className="h-10 w-10 text-red-600 mx-auto" />
              <h1 className="text-2xl font-bold text-neutral-900">Couldn't confirm your email</h1>
              <p className="text-neutral-600">{message}</p>
              <p className="text-sm text-neutral-600">
                Sign in to request a new link: <Link to="/login" className="text-primary-600 font-medium hover:underline">Sign in</Link>
              </p>
            </>
          )}
        </div>
      </Card>
    </AuthPageShell>
  )
}
