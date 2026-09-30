import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Spinner } from '@/components/ui'
import { api } from '@/lib/api'
import { formatDate, money } from '@/lib/format'

import type { Row } from '../api'
import { DataTable } from '../components/DataTable'
import { PageHeader, StatusPill } from '../components/PageHeader'

type Stats = {
  pending_orders: number
  orders_this_week: number
  revenue_this_week: string | number
  total_products: number
  low_stock_variants: number
  unread_messages: number
}

export default function Dashboard() {
  const stats = useQuery({ queryKey: ['admin', 'stats'], queryFn: () => api.get<Stats>('/admin/dashboard/stats/').then((r) => r.data) })
  const recent = useQuery({
    queryKey: ['admin', 'orders', 'recent'],
    queryFn: () => api.get<Row[]>('/admin/dashboard/recent-orders/').then((r) => r.data),
  })
  const s = stats.data

  const tiles = s
    ? [
        { label: 'Pending orders', value: s.pending_orders, to: 'orders' },
        { label: 'Orders this week', value: s.orders_this_week, to: 'orders' },
        { label: 'Requested this week', value: money(s.revenue_this_week), to: 'orders' },
        { label: 'Products', value: s.total_products, to: 'products' },
        { label: 'Low-stock variants', value: s.low_stock_variants, to: 'products?low_stock=true' },
        { label: 'Unread messages', value: s.unread_messages, to: 'messages' },
      ]
    : []

  return (
    <>
      <PageHeader title="Dashboard" />
      {stats.isLoading ? (
        <Spinner />
      ) : (
        <div className="mb-10 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          {tiles.map((t) => (
            <Link key={t.label} to={t.to} className="card p-5 transition-colors hover:border-accent">
              <p className="text-xs tracking-wider text-muted uppercase">{t.label}</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums">{t.value}</p>
            </Link>
          ))}
        </div>
      )}
      <h2 className="mb-4 text-sm font-semibold tracking-widest uppercase">Recent orders</h2>
      <DataTable
        rows={recent.data ?? []}
        loading={recent.isLoading}
        columns={[
          { key: 'order_number', label: 'Order', render: (r) => <Link to={`orders/${r.id}`} className="underline">{String(r.order_number)}</Link> },
          { key: 'full_name', label: 'Customer' },
          { key: 'status', label: 'Status', render: (r) => <StatusPill value={String(r.status)} /> },
          { key: 'subtotal', label: 'Subtotal', render: (r) => money(r.subtotal as string) },
          { key: 'created_at', label: 'Date', render: (r) => formatDate(String(r.created_at)) },
        ]}
      />
    </>
  )
}
