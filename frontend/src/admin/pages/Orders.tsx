import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { formatDate, money } from '@/lib/format'

import { StatusPill } from '../components/PageHeader'
import { ResourcePage } from '../components/ResourcePage'

export const ORDER_STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'] as const

export default function Orders() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')

  return (
    <ResourcePage
      key={status}
      title="Orders"
      resource="orders"
      searchable
      exportable
      params={{ status: status || undefined }}
      onRowClick={(row) => navigate(String(row.id))}
      filters={
        <select className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
          <option value="">All statuses</option>
          {ORDER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      }
      columns={[
        { key: 'order_number', label: 'Order' },
        { key: 'full_name', label: 'Customer' },
        { key: 'phone', label: 'Phone' },
        { key: 'item_count', label: 'Items' },
        { key: 'subtotal', label: 'Subtotal', sortable: true, render: (r) => money(r.subtotal as string) },
        { key: 'status', label: 'Status', sortable: true, render: (r) => <StatusPill value={String(r.status)} /> },
        { key: 'created_at', label: 'Date', sortable: true, render: (r) => formatDate(String(r.created_at)) },
      ]}
    />
  )
}
