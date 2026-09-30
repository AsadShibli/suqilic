import useEmblaCarousel from 'embla-carousel-react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import type { ProductCard as ProductCardType } from '@/lib/types'

import { ProductCard } from './ProductCard'

type Props = { title: string; products: ProductCardType[]; viewAllLink?: string }

export function ProductCarousel({ title, products, viewAllLink }: Props) {
  const [emblaRef, embla] = useEmblaCarousel({ align: 'start', slidesToScroll: 'auto', containScroll: 'trimSnaps' })
  const [page, setPage] = useState({ current: 1, total: 1 })

  const sync = useCallback(() => {
    if (embla) setPage({ current: embla.selectedScrollSnap() + 1, total: embla.scrollSnapList().length })
  }, [embla])

  useEffect(() => {
    if (!embla) return
    sync()
    embla.on('select', sync).on('reInit', sync)
    return () => {
      embla.off('select', sync).off('reInit', sync)
    }
  }, [embla, sync])

  if (!products.length) return null

  return (
    <section className="container-page py-10" aria-roledescription="carousel" aria-label={title}>
      <div className="mb-6 flex items-end justify-between gap-4">
        <h2 className="section-title">{title}</h2>
        {viewAllLink && (
          <Link to={viewAllLink} className="text-sm font-semibold tracking-wide uppercase underline-offset-4 hover:underline">
            View all
          </Link>
        )}
      </div>
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="-ml-4 flex">
          {products.map((p) => (
            <div key={p.id} className="min-w-0 shrink-0 grow-0 basis-1/2 pl-4 sm:basis-1/3 lg:basis-1/5">
              <ProductCard product={p} />
            </div>
          ))}
        </div>
      </div>
      {page.total > 1 && (
        <div className="mt-6 flex items-center justify-center gap-4 text-sm text-muted">
          <button
            className="rounded-sm border border-border p-2 hover:border-accent disabled:opacity-40"
            onClick={() => embla?.scrollPrev()}
            disabled={page.current === 1}
            aria-label="Previous"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span aria-live="polite">
            {page.current} / {page.total}
          </span>
          <button
            className="rounded-sm border border-border p-2 hover:border-accent disabled:opacity-40"
            onClick={() => embla?.scrollNext()}
            disabled={page.current === page.total}
            aria-label="Next"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      )}
    </section>
  )
}
