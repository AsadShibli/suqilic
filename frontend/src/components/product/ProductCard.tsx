import { Link } from 'react-router-dom'

import { useMoney } from '@/api/storefront'
import type { ProductCard as ProductCardType } from '@/lib/types'

export function ProductCard({ product }: { product: ProductCardType }) {
  const money = useMoney()
  const image = product.image

  return (
    <Link to={`/products/${product.slug}`} className="group block">
      <div className="card relative aspect-square overflow-hidden transition-[border-color,box-shadow] group-hover:border-accent group-hover:shadow-[0_0_24px_rgb(255_255_255/0.12)]">
        {image ? (
          <img
            src={image.thumbnail ?? image.image}
            alt={image.alt_text || product.title}
            loading="lazy"
            className="size-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex size-full items-center justify-center font-display text-4xl text-muted">S</div>
        )}
        {!product.in_stock && (
          <span className="absolute top-2 left-2 rounded-sm bg-bg/80 px-2 py-1 text-[10px] font-semibold tracking-widest uppercase">
            Sold out
          </span>
        )}
      </div>
      <h3 className="mt-3 line-clamp-2 text-sm font-semibold tracking-wide uppercase">{product.title}</h3>
      <p className="mt-1 text-sm text-muted">
        {product.has_price_range && 'From '}
        {money(product.price_from)}
        {product.compare_at_price && Number(product.compare_at_price) > Number(product.price_from) && (
          <s className="ml-2 opacity-60">{money(product.compare_at_price)}</s>
        )}
      </p>
    </Link>
  )
}
