import { useMoney } from '@/api/storefront'
import { formatDate } from '@/lib/format'
import type { Order } from '@/lib/types'

export function OrderStatusBadge({ status }: { status: Order['status'] }) {
  const tone = { pending: 'text-muted', confirmed: 'text-text', shipped: 'text-text', delivered: 'text-success', cancelled: 'text-danger' }
  return (
    <span className={`rounded-sm border border-border px-2 py-0.5 text-xs font-semibold tracking-widest uppercase ${tone[status]}`}>
      {status}
    </span>
  )
}

export function OrderSummary({ order }: { order: Order }) {
  const money = useMoney()
  return (
    <div className="card space-y-4 p-6 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold">{order.order_number}</p>
        <div className="flex items-center gap-3 text-sm text-muted">
          {formatDate(order.created_at)} <OrderStatusBadge status={order.status} />
        </div>
      </div>
      <ul className="space-y-2 border-t border-border pt-4 text-sm">
        {order.items.map((item, i) => (
          <li key={i} className="flex justify-between gap-4">
            <span className="text-muted">
              {item.quantity} × {item.product_title}
              {item.variant_title !== 'Default' && ` (${item.variant_title})`}
            </span>
            <span>{money(item.line_total)}</span>
          </li>
        ))}
      </ul>
      <p className="flex justify-between border-t border-border pt-4 font-semibold">
        <span>Subtotal</span>
        <span>{money(order.subtotal)}</span>
      </p>
      <p className="text-sm text-muted">
        Ship to: {[order.line1, order.line2, order.city, order.region, order.postal_code, order.country].filter(Boolean).join(', ')}
      </p>
    </div>
  )
}
