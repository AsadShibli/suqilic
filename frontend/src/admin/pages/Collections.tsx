import { useQuery } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, ListChecks, X } from 'lucide-react'
import { useDeferredValue, useState } from 'react'

import { Drawer } from '@/components/Drawer'
import { Spinner } from '@/components/ui'
import { api } from '@/lib/api'

import { useAdminAction, useAdminList, type Row } from '../api'
import { StatusPill } from '../components/PageHeader'
import { IconButton, ResourcePage } from '../components/ResourcePage'

function CollectionProducts({ collection }: { collection: Row }) {
  const key = ['admin', 'collections', collection.id, 'products']
  const { data: products = [], isLoading } = useQuery({
    queryKey: key,
    queryFn: () => api.get<Row[]>(`/admin/collections/${collection.id}/products/`).then((r) => r.data),
  })
  const action = useAdminAction('collections')
  const [search, setSearch] = useState('')
  const deferred = useDeferredValue(search)
  const { data: results } = useAdminList('products', { search: deferred, page_size: 10 }, deferred.length > 1)

  const setProducts = (ids: number[]) => action.mutate({ path: `${collection.id}/products/`, body: { product_ids: ids } })
  const ids = products.map((p) => p.id)
  const move = (index: number, delta: number) => {
    const next = [...ids]
    const [id] = next.splice(index, 1)
    next.splice(index + delta, 0, id)
    action.mutate({ path: `${collection.id}/products/reorder/`, body: { product_ids: next } })
  }

  return (
    <div className="space-y-4 p-5">
      <input className="input" placeholder="Search products to add…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search products" />
      {deferred.length > 1 && (
        <ul className="card divide-y divide-border">
          {results?.results
            .filter((p) => !ids.includes(p.id))
            .map((p) => (
              <li key={p.id}>
                <button className="w-full p-2 text-left text-sm hover:bg-surface-2" onClick={() => setProducts([...ids, p.id])}>
                  + {String(p.title)}
                </button>
              </li>
            ))}
        </ul>
      )}
      {isLoading ? (
        <Spinner />
      ) : (
        <ol className="divide-y divide-border">
          {products.map((p, i) => (
            <li key={p.id} className="flex items-center gap-3 py-2 text-sm">
              {p.image ? <img src={String(p.image)} alt="" className="size-8 rounded-sm object-cover" /> : null}
              <span className="flex-1 truncate">{String(p.title)}</span>
              <IconButton label="Move up" disabled={i === 0} onClick={() => move(i, -1)}>
                <ArrowUp className="size-4" />
              </IconButton>
              <IconButton label="Move down" disabled={i === products.length - 1} onClick={() => move(i, 1)}>
                <ArrowDown className="size-4" />
              </IconButton>
              <IconButton label="Remove" danger onClick={() => setProducts(ids.filter((x) => x !== p.id))}>
                <X className="size-4" />
              </IconButton>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

export default function Collections() {
  const [managing, setManaging] = useState<Row | null>(null)
  return (
    <>
      <ResourcePage
        title="Collections"
        singular="collection"
        resource="collections"
        searchable
        reorderable
        defaults={{ is_active: true }}
        columns={[
          { key: 'title', label: 'Title', sortable: true },
          { key: 'slug', label: 'Slug' },
          { key: 'product_count', label: 'Products' },
          { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
        ]}
        rowActions={(row) => (
          <IconButton label="Manage products" onClick={() => setManaging(row)}>
            <ListChecks className="size-4" />
          </IconButton>
        )}
        fields={[
          { name: 'title', label: 'Title', type: 'text', required: true },
          { name: 'slug', label: 'Slug', type: 'text', help: 'Leave blank to generate.' },
          { name: 'description', label: 'Description', type: 'textarea' },
          { name: 'banner_image', label: 'Banner image', type: 'image' },
          { name: 'is_active', label: 'Active', type: 'checkbox' },
          { name: 'seo_title', label: 'SEO title', type: 'text' },
          { name: 'seo_description', label: 'SEO description', type: 'text' },
        ]}
      />
      <Drawer open={Boolean(managing)} onClose={() => setManaging(null)} title={`Products in ${managing?.title ?? ''}`}>
        {managing && <CollectionProducts collection={managing} />}
      </Drawer>
    </>
  )
}
