import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'

import { useConfirmPasswordReset, useLogin, useRegister, useRequestPasswordReset } from '@/api/account'
import { Field, Seo } from '@/components/ui'
import { applyFieldErrors, errorMessage } from '@/lib/api'
import { useAuth } from '@/stores/auth'

function AuthCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="smoke container-page flex max-w-md flex-col py-16">
      <Seo title={title} />
      <h1 className="section-title mb-8 text-center">{title}</h1>
      {children}
    </div>
  )
}

/** Only allow in-app redirects. */
const safeNext = (next: string | null) => (next?.startsWith('/') && !next.startsWith('//') ? next : '/account')

const loginSchema = z.object({ email: z.email(), password: z.string().min(1, 'Required') })

export function Login() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const login = useLogin()
  const user = useAuth((s) => s.user)
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(loginSchema) })

  if (user) return <Navigate to={safeNext(params.get('next'))} replace />

  return (
    <AuthCard title="Log in">
      <form
        className="space-y-4"
        noValidate
        onSubmit={handleSubmit((v) =>
          login.mutate(v, {
            onSuccess: () => navigate(safeNext(params.get('next')), { replace: true }),
            onError: (e) => toast.error(errorMessage(e, 'Invalid email or password.')),
          }),
        )}
      >
        <Field label="Email" error={errors.email?.message}>
          <input {...register('email')} type="email" autoComplete="email" className="input" />
        </Field>
        <Field label="Password" error={errors.password?.message}>
          <input {...register('password')} type="password" autoComplete="current-password" className="input" />
        </Field>
        <button className="btn-primary w-full" disabled={login.isPending}>
          Log in
        </button>
      </form>
      <div className="mt-6 flex justify-between text-sm text-muted">
        <Link to="/account/forgot-password" className="hover:text-text">
          Forgot password?
        </Link>
        <Link to="/account/register" className="hover:text-text">
          Create account
        </Link>
      </div>
    </AuthCard>
  )
}

const registerSchema = z.object({
  first_name: z.string().trim(),
  last_name: z.string().trim(),
  email: z.email(),
  password: z.string().min(8, 'At least 8 characters'),
})

export function Register() {
  const navigate = useNavigate()
  const signup = useRegister()
  const { register, handleSubmit, setError, formState: { errors } } = useForm({ resolver: zodResolver(registerSchema) })

  return (
    <AuthCard title="Create account">
      <form
        className="space-y-4"
        noValidate
        onSubmit={handleSubmit((v) =>
          signup.mutate(v, {
            onSuccess: () => navigate('/account', { replace: true }),
            onError: (e) => applyFieldErrors(e, setError),
          }),
        )}
      >
        <div className="grid grid-cols-2 gap-4">
          <Field label="First name" error={errors.first_name?.message}>
            <input {...register('first_name')} autoComplete="given-name" className="input" />
          </Field>
          <Field label="Last name" error={errors.last_name?.message}>
            <input {...register('last_name')} autoComplete="family-name" className="input" />
          </Field>
        </div>
        <Field label="Email" error={errors.email?.message}>
          <input {...register('email')} type="email" autoComplete="email" className="input" />
        </Field>
        <Field label="Password" error={errors.password?.message}>
          <input {...register('password')} type="password" autoComplete="new-password" className="input" />
        </Field>
        <button className="btn-primary w-full" disabled={signup.isPending}>
          Create account
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Have an account?{' '}
        <Link to="/account/login" className="text-text underline">
          Log in
        </Link>
      </p>
    </AuthCard>
  )
}

export function ForgotPassword() {
  const request = useRequestPasswordReset()
  const [sent, setSent] = useState(false)
  return (
    <AuthCard title="Reset password">
      {sent ? (
        <p className="text-center text-muted">If that email has an account, a reset link is on its way.</p>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            request.mutate(String(new FormData(e.currentTarget).get('email')), { onSuccess: () => setSent(true) })
          }}
        >
          <input name="email" type="email" required className="input" placeholder="Email" aria-label="Email" />
          <button className="btn-primary w-full" disabled={request.isPending}>
            Send reset link
          </button>
        </form>
      )}
    </AuthCard>
  )
}

export function ResetPassword() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const confirm = useConfirmPasswordReset()
  return (
    <AuthCard title="Choose a new password">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          confirm.mutate(
            {
              uid: params.get('uid') ?? '',
              token: params.get('token') ?? '',
              new_password: String(new FormData(e.currentTarget).get('password')),
            },
            {
              onSuccess: () => {
                toast.success('Password updated. Please log in.')
                navigate('/account/login')
              },
              onError: (err) => toast.error(errorMessage(err)),
            },
          )
        }}
      >
        <input
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="input"
          placeholder="New password"
          aria-label="New password"
        />
        <button className="btn-primary w-full" disabled={confirm.isPending}>
          Update password
        </button>
      </form>
    </AuthCard>
  )
}
