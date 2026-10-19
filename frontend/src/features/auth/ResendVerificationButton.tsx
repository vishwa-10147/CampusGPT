// ==============================================================================
// CampusGPT Frontend — Resend Verification Email
// ==============================================================================
import { useState } from 'react'
import { authApi } from '../../services/api'
import { Button } from '../../components/ui'

export const ResendVerificationButton = ({ email }: { email: string }) => {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

  const resend = async () => {
    setState('sending')
    try {
      await authApi.resendVerification(email)
      setState('sent')
    } catch {
      setState('error')
    }
  }

  if (state === 'sent') {
    return <p className="text-sm text-green-700">A new confirmation link is on its way to {email}.</p>
  }

  return (
    <div className="space-y-2">
      <Button variant="secondary" className="w-full" onClick={resend} disabled={state === 'sending' || !email}>
        {state === 'sending' ? 'Sending…' : 'Resend confirmation email'}
      </Button>
      {state === 'error' && <p className="text-sm text-red-600">Couldn't send the email. Try again in a minute.</p>}
    </div>
  )
}
