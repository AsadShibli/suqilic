import { Minus, Plus, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useRemoveCartItem, useUpdateCartItem } from '@/api/cart'
import { useMoney } from '@/api/storefront'
import type { CartItem } from '@/lib/types'

type Props = { items: CartItem[]; compact?: boolean; onNavigate?: () => void }

export function CartLines({ items, compact, onNavigate }: Props) {
  const update = useUpdateCartItem()
  const remove = useRemoveCartItem()
  const money = useMoney()
  const busy = update.isPending || remove.isPending

  return (
    <ul className="divide-y divide-border">
      {items.map((item) => (
        <li key={item.id} className="flex gap-4 py-5">
          <Link to={`/products/${item.product_slug}`} onClick={onNavigate} className="card size-20 shrink-0 overflow-hidden">
            {item.image && <img src={item.image} alt="" className="size-full object-cover" />}
          </Link>
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <Link
              to={`/products/${item.product_slug}`}
              onClick={onNavigate}
              className="truncate text-sm font-semibold uppercase hover:underline"
            >
              {item.product_title}
            </Link>
            {item.variant_title !== 'Default' && <p className="text-xs text-muted">{item.variant_title}</p>}
            <p className="text-sm text-muted">{money(item.unit_price)}</p>
            <div className="mt-auto flex items-center gap-3">
              <div className="flex items-center rounded-sm border border-border">
                <button
                  className="p-2 hover:text-accent disabled:opacity-40"
                  aria-label="Decrease quantity"
                  disabled={busy || item.quantity <= 1}
                  onClick={() => update.mutate({ id: item.id, quantity: item.quantity - 1 })}
                >
                  <Minus className="size-3" />
                </button>
                <span className="w-8 text-center text-sm">{item.quantity}</span>
                <button
                  className="p-2 hover:text-accent disabled:opacity-40"
                  aria-label="Increase quantity"
                  disabled={busy || item.quantity >= item.stock_quantity}
                  onClick={() => update.mutate({ id: item.id, quantity: item.quantity + 1 })}
                >
                  <Plus className="size-3" />
                </button>
              </div>
              <button
                className="p-2 text-muted hover:text-danger"
                aria-label={`Remove ${item.product_title}`}
                disabled={busy}
                onClick={() => remove.mutate(item.id)}
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          </div>
          {!compact && <p className="text-sm font-semibold">{money(item.line_total)}</p>}
        </li>
      ))}
    </ul>
  )
}
