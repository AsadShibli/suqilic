import { ArrowLeft, Printer } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PageLoader } from '@/components/ui'
import { formatDate, money } from '@/lib/format'
import type { Order, OrderItem } from '@/lib/types'

import { useAdminAction, useAdminRecord, useAdminSave } from '../api'
import { PageHeader, StatusPill } from '../components/PageHeader'
import { ORDER_STATUSES } from './Orders'

type AdminOrder = Order & {
  id: number
  phone: string
  internal_note: string
  status_history: { from_status: string; to_status: string; note: string; changed_by: string; changed_at: string }[]
}

export default function OrderDetail() {
  const { id } = useParams()
  const { data: order, isLoading } = useAdminRecord<AdminOrder>('orders', id)
  const changeStatus = useAdminAction<AdminOrder>('orders')
  const save = useAdminSave('orders')
  const [status, setStatus] = useState('')
  const [note, setNote] = useState('')
  const [notify, setNotify] = useState(true)

  if (isLoading || !order) return <PageLoader />

  return (
    <>
      <Link to=".." relative="path" className="mb-4 inline-flex items-center gap-2 text-sm text-muted hover:text-text print:hidden">
        <ArrowLeft className="size-4" /> Orders
      </Link>
      <PageHeader title={order.order_number}>
        <StatusPill value={order.status} />
        <StatusPill value={order.payment_method === 'online' ? `online · ${order.payment_status}` : 'cash on delivery'} />
        <button className="btn-outline print:hidden" onClick={() => window.print()}>
          <Printer className="size-4" /> Print
        </button>
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <section className="card p-5">
            <h2 className="label">Items</h2>
            <table className="w-full text-sm">
              <tbody className="divide-y divide-border">
                {order.items.map((item: OrderItem, i) => (
                  <tr key={i}>
                    <td className="py-2">
                      {item.product_title}
                      {item.variant_title !== 'Default' && <span className="text-muted"> — {item.variant_title}</span>}
                      {item.sku && <span className="block text-xs text-muted">SKU {item.sku}</span>}
                    </td>
                    <td className="py-2 pl-4 text-right whitespace-nowrap text-muted">
                      {item.quantity} × {money(item.unit_price)}
                    </td>
                    <td className="py-2 pl-4 text-right">{money(item.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 flex justify-between border-t border-border pt-4 font-semibold">
              <span>Subtotal</span>
              <span>{money(order.subtotal)}</span>
            </p>
          </section>

          <section className="card p-5">
            <h2 className="label">Customer</h2>
            <p className="font-semibold">{order.full_name}</p>
            <p className="text-sm">
              <a href={`mailto:${order.email}`} className="underline">{order.email}</a> · <a href={`tel:${order.phone}`}>{order.phone}</a>
            </p>
            <p className="mt-3 text-sm text-muted">
              {[order.line1, order.line2, order.city, order.region, order.postal_code, order.country].filter(Boolean).join(', ')}
            </p>
            {order.customer_note && <p className="mt-3 rounded-sm bg-surface-2 p-3 text-sm">“{order.customer_note}”</p>}
            <p className="mt-3 text-xs text-muted">Placed {formatDate(order.created_at)}</p>
          </section>
        </div>

        <div className="space-y-6 print:hidden">
          <section className="card space-y-3 p-5">
            <h2 className="label">Update status</h2>
            <select className="input" value={status || order.status} onChange={(e) => setStatus(e.target.value)} disabled={order.status === 'cancelled'}>
              {ORDER_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <textarea className="input" rows={2} placeholder="Note (optional, included in email)" value={note} onChange={(e) => setNote(e.target.value)} />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="accent-white" checked={notify} onChange={(e) => setNotify(e.target.checked)} /> Email the customer
            </label>
            <button
              className="btn-primary w-full"
              disabled={!status || status === order.status || changeStatus.isPending}
              onClick={() =>
                changeStatus.mutate(
                  { path: `${order.id}/status/`, body: { status, note, notify_customer: notify } },
                  {
                    onSuccess: () => {
                      toast.success('Status updated')
                      setNote('')
                      setStatus('')
                    },
                  },
                )
              }
            >
              Update
            </button>
            {order.status === 'cancelled' && <p className="text-xs text-muted">Cancelled orders can’t be reopened; stock was restored.</p>}
          </section>

          <section className="card space-y-3 p-5">
            <h2 className="label">Internal note</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                save.mutate({ id: order.id, values: { internal_note: new FormData(e.currentTarget).get('internal_note') } })
              }}
            >
              <textarea name="internal_note" className="input" rows={3} defaultValue={order.internal_note} />
              <button className="btn-outline mt-3 w-full" disabled={save.isPending}>
                Save note
              </button>
            </form>
          </section>

          {order.status_history.length > 0 && (
            <section className="card p-5">
              <h2 className="label">History</h2>
              <ol className="space-y-3 text-sm">
                {order.status_history.map((h, i) => (
                  <li key={i}>
                    <span className="font-semibold">{h.from_status} → {h.to_status}</span>
                    <span className="block text-xs text-muted">
                      {formatDate(h.changed_at)} · {h.changed_by}
                    </span>
                    {h.note && <span className="block text-muted">{h.note}</span>}
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      </div>
    </>
  )
}
