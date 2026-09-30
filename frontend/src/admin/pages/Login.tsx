import { toast } from 'sonner'

import { useLogin } from '@/api/account'
import { errorMessage } from '@/lib/api'

export default function AdminLogin() {
  const login = useLogin('/auth/admin/login/')

  return (
    <div className="smoke flex min-h-screen items-center justify-center p-4">
      <title>Sign in | Suqilic</title>
      <meta name="robots" content="noindex, nofollow" />
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
      </form>
    </div>
  )
}
