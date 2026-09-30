import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { useMenu, useSettings } from '@/api/storefront'
import { api, errorMessage } from '@/lib/api'

export function Footer() {
  const { data: settings } = useSettings()
  const { data: policies = [] } = useMenu('policies')
  const [email, setEmail] = useState('')
  const subscribe = useMutation({
    mutationFn: () => api.post('/newsletter/subscribe/', { email }),
    onSuccess: () => {
      toast.success('You’re on the list.')
      setEmail('')
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  const socials = [
    { label: 'Instagram', url: settings?.instagram_url },
    { label: 'TikTok', url: settings?.tiktok_url },
  ].filter((s) => s.url)

  return (
    <footer className="smoke mt-16 overflow-hidden border-t border-border">
      <div className="container-page grid gap-10 py-14 md:grid-cols-3">
        <div>
          <img src="/logo.png" alt={settings?.store_name ?? 'Suqilic'} className="h-12 w-auto" />
          {socials.length > 0 && (
            <ul className="mt-6 flex gap-4">
              {socials.map((s) => (
                <li key={s.label}>
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-sm text-muted hover:text-accent">
                    {s.label}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
        <nav aria-label="Policies">
          <p className="label">Info</p>
          <ul className="space-y-2 text-sm">
            <li>
              <Link to="/pages/contact-us" className="text-muted hover:text-accent">
                Contact us
              </Link>
            </li>
            <li>
              <Link to="/orders/track" className="text-muted hover:text-accent">
                Track an order
              </Link>
            </li>
            {policies.map((p) => (
              <li key={p.id}>
                <Link to={p.url} className="text-muted hover:text-accent">
                  {p.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            subscribe.mutate()
          }}
        >
          <p className="label">Join the list</p>
          <p className="mb-4 text-sm text-muted">New drops and restocks, straight to your inbox.</p>
          <div className="flex gap-2">
            <input
              type="email"
              required
              className="input"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="Email"
            />
            <button className="btn-primary" disabled={subscribe.isPending}>
              Join
            </button>
          </div>
        </form>
      </div>
      <p className="border-t border-border py-6 text-center text-xs text-muted">
        © {new Date().getFullYear()} {settings?.store_name ?? 'Suqilic'}
      </p>
    </footer>
  )
}
