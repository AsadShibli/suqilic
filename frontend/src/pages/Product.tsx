import clsx from 'clsx'
import { Minus, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAddToCart } from '@/api/cart'
import { useMoney, useProduct, useRelated } from '@/api/storefront'
import { ProductCarousel } from '@/components/product/ProductCarousel'
import { PageLoader, RichText, Seo } from '@/components/ui'
import { VideoEmbed } from '@/components/VideoEmbed'
import type { Product as ProductType } from '@/lib/types'

import NotFound from './NotFound'

function Gallery({ product }: { product: ProductType }) {
  const [active, setActive] = useState(0)
  const image = product.images[active]
  return (
    <div className="space-y-3">
      <div className="card aspect-square overflow-hidden">
        {image ? (
          <a href={image.image} target="_blank" rel="noreferrer" aria-label="Open full-size image">
            <img src={image.image} alt={image.alt_text || product.title} className="size-full object-contain" />
          </a>
        ) : (
          <div className="flex size-full items-center justify-center font-display text-6xl text-muted">S</div>
        )}
      </div>
      {product.images.length > 1 && (
        <div className="no-scrollbar flex gap-3 overflow-x-auto">
          {product.images.map((img, i) => (
            <button
              key={img.id}
              onClick={() => setActive(i)}
              className={clsx('card size-20 shrink-0 overflow-hidden', i === active && 'border-accent')}
              aria-label={`Show image ${i + 1}`}
            >
              <img src={img.thumbnail ?? img.image} alt="" className="size-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function BuyBox({ product }: { product: ProductType }) {
  const money = useMoney()
  const add = useAddToCart()
  const firstAvailable = product.variants.find((v) => v.in_stock) ?? product.variants[0]
  const [selected, setSelected] = useState<Record<string, string>>(firstAvailable?.options ?? {})
  const [quantity, setQuantity] = useState(1)

  const variant = useMemo(
    () =>
      product.options.length
        ? product.variants.find((v) => product.options.every((o) => v.options[o.name] === selected[o.name]))
        : product.variants[0],
    [product, selected],
  )
  const maxQty = Math.min(variant?.stock_quantity ?? 0, 99)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-wide uppercase md:text-3xl">{product.title}</h1>
        <p className="mt-2 text-xl text-muted">
          {variant ? money(variant.price) : money(product.price_from)}
          {product.compare_at_price && <s className="ml-3 text-base opacity-60">{money(product.compare_at_price)}</s>}
        </p>
      </div>

      {product.options.map((option) => (
        <fieldset key={option.name}>
          <legend className="label">{option.name}</legend>
          <div className="flex flex-wrap gap-2">
            {option.values.map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setSelected((s) => ({ ...s, [option.name]: value }))}
                aria-pressed={selected[option.name] === value}
                className={clsx(
                  'rounded-sm border px-4 py-2 text-sm transition-colors',
                  selected[option.name] === value ? 'border-accent bg-accent text-bg' : 'border-border hover:border-accent',
                )}
              >
                {value}
              </button>
            ))}
          </div>
        </fieldset>
      ))}

      <div>
        <span className="label">Quantity</span>
        <div className="inline-flex items-center rounded-sm border border-border">
          <button className="p-3" onClick={() => setQuantity((q) => Math.max(1, q - 1))} aria-label="Decrease quantity">
            <Minus className="size-4" />
          </button>
          <span className="w-10 text-center" aria-live="polite">
            {quantity}
          </span>
          <button
            className="p-3"
            onClick={() => setQuantity((q) => Math.min(maxQty || 1, q + 1))}
            aria-label="Increase quantity"
          >
            <Plus className="size-4" />
          </button>
        </div>
      </div>

      <button
        className="btn-primary w-full py-4"
        disabled={!variant?.in_stock || add.isPending}
        onClick={() => variant && add.mutate({ variant_id: variant.id, quantity })}
      >
        {!variant ? 'Unavailable' : variant.in_stock ? (add.isPending ? 'Adding…' : 'Add to cart') : 'Sold out'}
      </button>

      {product.description && <RichText html={product.description} className="border-t border-border pt-6" />}

      {product.collections.length > 0 && (
        <p className="text-sm text-muted">
          In:{' '}
          {product.collections.map((c, i) => (
            <span key={c.slug}>
              {i > 0 && ', '}
              <Link to={`/collections/${c.slug}`} className="underline-offset-4 hover:underline">
                {c.title}
              </Link>
            </span>
          ))}
        </p>
      )}
    </div>
  )
}

export default function Product() {
  const { slug = '' } = useParams()
  const { data: product, isLoading, isError } = useProduct(slug)
  const { data: related = [] } = useRelated(slug)

  if (isLoading) return <PageLoader />
  if (isError || !product) return <NotFound />

  return (
    <>
      <Seo title={product.seo_title || product.title} description={product.seo_description} />
      <div className="container-page grid gap-10 py-10 md:grid-cols-2 lg:gap-16">
        <Gallery product={product} />
        <BuyBox key={product.id} product={product} />
      </div>
      {product.video_url && (
        <section className="container-page py-10">
          <h2 className="section-title mb-6">How to apply</h2>
          <VideoEmbed url={product.video_url} title={product.title} />
        </section>
      )}
      <ProductCarousel title="You may also like" products={related} />
    </>
  )
}
