import { Search } from 'lucide-react'
import { useDeferredValue, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useMoney, useSuggest } from '@/api/storefront'

import { Drawer } from '../Drawer'

export function SearchPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [q, setQ] = useState('')
  const deferred = useDeferredValue(q)
  const { data } = useSuggest(deferred)
  const navigate = useNavigate()
  const money = useMoney()

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!q.trim()) return
    navigate(`/search?q=${encodeURIComponent(q.trim())}`)
    onClose()
  }

  return (
    <Drawer open={open} onClose={onClose} title="Search" side="top">
      <div className="container-page py-6">
        <form onSubmit={submit} role="search" className="relative">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" />
          <input
            autoFocus
            className="input pl-10 text-base"
            placeholder="Search stickers, card skins…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search"
          />
        </form>
        {data && deferred.length >= 2 && (
          <div className="mt-6 grid gap-6 md:grid-cols-[1fr_220px]">
            <ul className="space-y-3">
              {data.products.map((p) => (
                <li key={p.id}>
                  <Link to={`/products/${p.slug}`} onClick={onClose} className="flex items-center gap-3 hover:text-accent">
                    <img src={p.image?.thumbnail ?? ''} alt="" className="card size-12 object-cover" />
                    <span className="flex-1 text-sm font-semibold uppercase">{p.title}</span>
                    <span className="text-sm text-muted">{money(p.price_from)}</span>
                  </Link>
                </li>
              ))}
              {!data.products.length && <li className="text-sm text-muted">No products found.</li>}
            </ul>
            {data.collections.length > 0 && (
              <div>
                <p className="label">Collections</p>
                <ul className="space-y-2">
                  {data.collections.map((c) => (
                    <li key={c.slug}>
                      <Link to={`/collections/${c.slug}`} onClick={onClose} className="text-sm hover:underline">
                        {c.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Drawer>
  )
}
