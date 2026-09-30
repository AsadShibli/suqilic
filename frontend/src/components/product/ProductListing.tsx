import { useSearchParams } from 'react-router-dom'

import { useProductList } from '@/api/storefront'

import { EmptyState, Spinner } from '../ui'
import { ProductGrid, ProductGridSkeleton } from './ProductGrid'

const SORTS = [
  ['featured', 'Featured'],
  ['best_selling', 'Best selling'],
  ['title', 'Alphabetically, A–Z'],
  ['-title', 'Alphabetically, Z–A'],
  ['price', 'Price, low to high'],
  ['-price', 'Price, high to low'],
  ['-created_at', 'Newest'],
] as const

const FILTER_KEYS = ['ordering', 'in_stock', 'min_price', 'max_price'] as const

/** Sortable, filterable, "load more" grid. Filters live in the URL so results are shareable. */
export function ProductListing({ collection, q }: { collection?: string; q?: string }) {
  const [params, setParams] = useSearchParams()
  const query = Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) ?? undefined]))
  const list = useProductList({ collection, search: q !== undefined }, { ...query, q })
  const products = list.data?.pages.flatMap((p) => p.results) ?? []
  const count = list.data?.pages[0]?.count ?? 0

  const set = (key: string, value: string | null) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  return (
    <>
      <div className="mb-8 flex flex-wrap items-center gap-3 border-y border-border py-3 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="accent-white"
            checked={params.get('in_stock') === 'true'}
            onChange={(e) => set('in_stock', e.target.checked ? 'true' : null)}
          />
          In stock only
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            placeholder="Min $"
            className="input w-24 py-1.5"
            defaultValue={params.get('min_price') ?? ''}
            onBlur={(e) => set('min_price', e.target.value || null)}
            aria-label="Minimum price"
          />
          <span className="text-muted">–</span>
          <input
            type="number"
            min={0}
            placeholder="Max $"
            className="input w-24 py-1.5"
            defaultValue={params.get('max_price') ?? ''}
            onBlur={(e) => set('max_price', e.target.value || null)}
            aria-label="Maximum price"
          />
        </div>
        <span className="ml-auto text-muted">{count} products</span>
        <select
          className="input w-auto py-1.5"
          value={params.get('ordering') ?? 'featured'}
          onChange={(e) => set('ordering', e.target.value === 'featured' ? null : e.target.value)}
          aria-label="Sort by"
        >
          {SORTS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {list.isLoading ? (
        <ProductGridSkeleton />
      ) : products.length ? (
        <>
          <ProductGrid products={products} />
          {list.hasNextPage && (
            <div className="mt-12 flex justify-center">
              <button className="btn-outline" onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage}>
                {list.isFetchingNextPage ? <Spinner className="size-4" /> : 'Load more'}
              </button>
            </div>
          )}
        </>
      ) : (
        <EmptyState title="Nothing here yet">
          <p className="text-muted">Try removing some filters.</p>
        </EmptyState>
      )}
    </>
  )
}
