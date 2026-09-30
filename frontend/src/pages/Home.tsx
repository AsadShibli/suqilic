import { Link } from 'react-router-dom'

import { useHome } from '@/api/storefront'
import { ProductCarousel } from '@/components/product/ProductCarousel'
import { ProductGridSkeleton } from '@/components/product/ProductGrid'
import { Seo, Skeleton } from '@/components/ui'
import type { HeroBanner } from '@/lib/types'

function Hero({ banner }: { banner: HeroBanner }) {
  return (
    <section className="smoke relative overflow-hidden border-b border-border">
      <picture>
        {banner.image_mobile && <source media="(max-width: 767px)" srcSet={banner.image_mobile} />}
        <img src={banner.image_desktop} alt="" className="absolute inset-0 size-full object-cover opacity-35" />
      </picture>
      <div className="absolute inset-0 bg-gradient-to-t from-bg via-bg/40 to-transparent" />
      <div className="container-page relative flex min-h-[60vh] flex-col items-center justify-center gap-6 py-20 text-center">
        {banner.heading && <h1 className="font-display text-5xl tracking-wide uppercase md:text-7xl">{banner.heading}</h1>}
        {banner.subheading && <p className="max-w-xl text-lg text-text/90">{banner.subheading}</p>}
        {banner.button_text && banner.button_link && (
          <Link to={banner.button_link} className="btn-primary">
            {banner.button_text}
          </Link>
        )}
      </div>
    </section>
  )
}

export default function Home() {
  const { data: sections, isLoading } = useHome()

  if (isLoading) {
    return (
      <div className="container-page space-y-10 py-10">
        <Skeleton className="h-[50vh]" />
        <ProductGridSkeleton count={4} />
      </div>
    )
  }

  return (
    <>
      <Seo />
      {sections?.map((section) =>
        section.type === 'hero' ? (
          section.banners.slice(0, 1).map((b) => <Hero key={b.id} banner={b} />)
        ) : (
          <ProductCarousel
            key={section.id}
            title={section.title}
            products={section.products}
            viewAllLink={section.view_all_link}
          />
        ),
      )}
    </>
  )
}
