import { useParams } from 'react-router-dom'

import { useCollection } from '@/api/storefront'
import { ProductListing } from '@/components/product/ProductListing'
import { RichText, Seo, Skeleton } from '@/components/ui'

import NotFound from './NotFound'

export default function Collection() {
  const { slug = '' } = useParams()
  const { data: collection, isLoading, isError } = useCollection(slug)

  if (isError) return <NotFound />

  return (
    <div className="container-page py-10">
      {collection && <Seo title={collection.seo_title || collection.title} description={collection.seo_description} />}
      {collection?.banner_image && (
        <img src={collection.banner_image} alt="" className="card mb-8 h-48 w-full object-cover md:h-72" />
      )}
      <header className="smoke mb-8 text-center">
        {isLoading ? (
          <Skeleton className="mx-auto h-10 w-64" />
        ) : (
          <h1 className="font-display text-4xl tracking-wide uppercase md:text-6xl">{collection?.title}</h1>
        )}
        {collection?.description && (
          <RichText html={collection.description} className="mx-auto mt-4 max-w-2xl text-muted" />
        )}
      </header>
      <ProductListing key={slug} collection={slug} />
    </div>
  )
}
