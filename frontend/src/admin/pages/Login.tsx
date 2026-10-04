import { useState } from 'react'
import { toast } from 'sonner'

import { useLogin, useRequestPasswordReset } from '@/api/account'
import { errorMessage } from '@/lib/api'

export default function AdminLogin() {
  const login = useLogin('/auth/admin/login/')
  const reset = useRequestPasswordReset()
  const [mode, setMode] = useState<'login' | 'forgot' | 'sent'>('login')

  return (
    <div className="smoke flex min-h-screen items-center justify-center p-4">
      <title>Sign in | Suqilic</title>
      <meta name="robots" content="noindex, nofollow" />
      {mode === 'login' && (
      <form
        className="card w-full max-w-sm space-y-4 p-8"
        onSubmit={(e) => {
          e.preventDefault()
          const form = new FormData(e.currentTarget)
          login.mutate(
            { email: String(form.get('email')), password: String(form.get('password')) },
            { onError: (err) => toast.error(errorMessage(err, 'Invalid credentials.')) },
          )
        }}
      >
        <img src="/logo.png" alt="Suqilic" className="mx-auto mb-4 h-14" />
        <input name="email" type="email" required autoComplete="username" className="input" placeholder="Email" aria-label="Email" />
        <input
          name="password"
          type="password"
          required
          autoComplete="current-password"
          className="input"
          placeholder="Password"
          aria-label="Password"
        />
        <button className="btn-primary w-full" disabled={login.isPending}>
          {login.isPending ? 'Signing in…' : 'Sign in'}
        </button>
        <button type="button" className="block w-full text-center text-sm text-muted underline-offset-4 hover:underline" onClick={() => setMode('forgot')}>
          Forgot password?
        </button>
      </form>
      )}
      {mode !== 'login' && (
        <form
          className="card w-full max-w-sm space-y-4 p-8"
          onSubmit={(e) => {
            e.preventDefault()
            reset.mutate(String(new FormData(e.currentTarget).get('email')), {
              onSuccess: () => setMode('sent'),
              onError: (err) => toast.error(errorMessage(err, 'Could not send the reset email.')),
            })
          }}
        >
          <img src="/logo.png" alt="Suqilic" className="mx-auto mb-4 h-14" />
          {mode === 'sent' ? (
            <p className="text-center text-muted">If that email has an account, a password reset link is on its way. Check your inbox.</p>
          ) : (
            <>
              <p className="text-center text-muted">Enter your admin email and we'll send you a link to reset your password.</p>
              <input name="email" type="email" required autoComplete="username" className="input" placeholder="Email" aria-label="Email" />
              <button className="btn-primary w-full" disabled={reset.isPending}>
                {reset.isPending ? 'Sending…' : 'Send reset link'}
              </button>
            </>
          )}
          <button type="button" className="block w-full text-center text-sm text-muted underline-offset-4 hover:underline" onClick={() => setMode('login')}>
            Back to sign in
          </button>
        </form>
      )}
    </div>
  )
}
