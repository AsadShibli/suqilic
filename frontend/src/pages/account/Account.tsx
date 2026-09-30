import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'

import { useLogout, useMyOrders, useUpdateMe } from '@/api/account'
import { OrderSummary } from '@/components/OrderSummary'
import { EmptyState, Seo, Spinner } from '@/components/ui'
import { errorMessage } from '@/lib/api'
import { useAuth } from '@/stores/auth'

export default function Account() {
  const user = useAuth((s) => s.user)
  const logout = useLogout()
  const orders = useMyOrders()
  const update = useUpdateMe()

  if (!user) return <Navigate to="/account/login?next=/account" replace />

  return (
    <div className="container-page grid gap-10 py-12 lg:grid-cols-[320px_1fr]">
      <Seo title="Account" />
      <aside className="space-y-6">
        <h1 className="section-title">Account</h1>
        <form
          className="card space-y-3 p-5"
          onSubmit={(e) => {
            e.preventDefault()
            const form = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>
            update.mutate(form, {
              onSuccess: () => toast.success('Profile saved.'),
              onError: (err) => toast.error(errorMessage(err)),
            })
          }}
        >
          <p className="text-sm text-muted">{user.email}</p>
          <input name="first_name" defaultValue={user.first_name} className="input" placeholder="First name" aria-label="First name" />
          <input name="last_name" defaultValue={user.last_name} className="input" placeholder="Last name" aria-label="Last name" />
          <input name="phone" defaultValue={user.phone} className="input" placeholder="Phone" aria-label="Phone" />
          <button className="btn-outline w-full" disabled={update.isPending}>
            Save
          </button>
        </form>
        <button className="btn-outline w-full" onClick={logout}>
          Log out
        </button>
      </aside>
      <section>
        <h2 className="mb-6 text-sm font-semibold tracking-widest uppercase">Order history</h2>
        {orders.isLoading ? (
          <Spinner />
        ) : orders.data?.results.length ? (
          <div className="space-y-4">
            {orders.data.results.map((o) => (
              <OrderSummary key={o.order_number} order={o} />
            ))}
          </div>
        ) : (
          <EmptyState title="No orders yet" />
        )}
      </section>
    </div>
  )
}
