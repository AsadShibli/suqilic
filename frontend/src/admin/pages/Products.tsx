import { Copy } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { money } from '@/lib/format'

import { useAdminAction, useAdminList } from '../api'
import { StatusPill } from '../components/PageHeader'
import { IconButton, ResourcePage } from '../components/ResourcePage'

export default function Products() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [status, setStatus] = useState('')
  const [collection, setCollection] = useState('')
  const lowStock = params.get('low_stock') === 'true'
  const { data: collections } = useAdminList('collections', { page_size: 100 })
  const action = useAdminAction<{ id: number }>('products')

  return (
    <ResourcePage
      key={`${status}-${collection}-${lowStock}`}
      title={lowStock ? 'Low-stock products' : 'Products'}
      singular="product"
      resource="products"
      searchable
      canCreate={false}
      params={{ status: status || undefined, collection_products__collection: collection || undefined, low_stock: lowStock || undefined }}
      onRowClick={(row) => navigate(String(row.id))}
      filters={
        <>
          <select className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
          <select className="input w-auto" value={collection} onChange={(e) => setCollection(e.target.value)} aria-label="Collection">
            <option value="">All collections</option>
            {collections?.results.map((c) => (
              <option key={c.id} value={c.id}>
                {String(c.title)}
              </option>
            ))}
          </select>
          <button className="btn-primary ml-auto" onClick={() => navigate('new')}>
            Add product
          </button>
        </>
      }
      columns={[
        {
          key: 'image',
          label: '',
          render: (r) => (r.image ? <img src={String(r.image)} alt="" className="size-10 rounded-sm object-cover" /> : null),
        },
        { key: 'title', label: 'Title', sortable: true },
        { key: 'status', label: 'Status', render: (r) => <StatusPill value={String(r.status)} /> },
        { key: 'price_from', label: 'Price', sortable: true, render: (r) => money(r.price_from as string) },
        { key: 'total_stock', label: 'Stock', sortable: true },
        { key: 'variant_count', label: 'Variants' },
      ]}
      rowActions={(row) => (
        <IconButton
          label="Duplicate"
          onClick={() =>
            action.mutate(
              { path: `${row.id}/duplicate/` },
              {
                onSuccess: (copy) => {
                  toast.success('Duplicated as draft')
                  navigate(String(copy.id))
                },
              },
            )
          }
        >
          <Copy className="size-4" />
        </IconButton>
      )}
    />
  )
}
