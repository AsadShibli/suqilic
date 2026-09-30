import { useSearchParams } from 'react-router-dom'

import { ProductListing } from '@/components/product/ProductListing'
import { Seo } from '@/components/ui'

export default function Search() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''

  return (
    <div className="container-page py-10">
      <Seo title={q ? `Search: ${q}` : 'Search'} />
      <h1 className="section-title mb-6 text-center">Search</h1>
      <form
        role="search"
        className="mx-auto mb-10 max-w-xl"
        onSubmit={(e) => {
          e.preventDefault()
          const value = new FormData(e.currentTarget).get('q')?.toString().trim() ?? ''
          setParams(value ? { q: value } : {})
        }}
      >
        <input name="q" defaultValue={q} key={q} className="input text-base" placeholder="Search…" aria-label="Search" />
      </form>
      {q && <ProductListing q={q} />}
    </div>
  )
}
