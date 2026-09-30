import { keepPreviousData, useInfiniteQuery, useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'
import { money } from '@/lib/format'
import type {
  Collection,
  HomeSection,
  MenuItem,
  Page,
  Paginated,
  Product,
  ProductCard,
  SiteSettings,
  Video,
} from '@/lib/types'

const get = <T>(url: string, params?: object) => api.get<T>(url, { params }).then((r) => r.data)
const STATIC = { staleTime: 5 * 60_000 }

export const useSettings = () => useQuery({ queryKey: ['settings'], queryFn: () => get<SiteSettings>('/settings/'), ...STATIC })

export function useMoney() {
  const { data } = useSettings()
  return (value: string | number | null | undefined) => money(value, data?.currency_symbol ?? '$')
}

export const useMenu = (menu: 'header' | 'footer' | 'policies') =>
  useQuery({ queryKey: ['menu', menu], queryFn: () => get<MenuItem[]>(`/menus/${menu}/`), ...STATIC })

export const useHome = () => useQuery({ queryKey: ['home'], queryFn: () => get<HomeSection[]>('/home/') })

export const useCollection = (slug: string) =>
  useQuery({ queryKey: ['collection', slug], queryFn: () => get<Collection>(`/collections/${slug}/`) })

export type ProductQuery = { ordering?: string; in_stock?: string; min_price?: string; max_price?: string; q?: string }

/** Paged product listing for a collection (`slug`), search (`q`), or all products. */
export function useProductList(source: { collection?: string; search?: boolean }, params: ProductQuery) {
  const url = source.collection
    ? `/collections/${source.collection}/products/`
    : source.search
      ? '/search/'
      : '/products/'
  return useInfiniteQuery({
    queryKey: ['products', url, params],
    queryFn: ({ pageParam }) => get<Paginated<ProductCard>>(url, { ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
    placeholderData: keepPreviousData,
    enabled: !source.search || Boolean(params.q),
  })
}

export const useProduct = (slug: string) =>
  useQuery({ queryKey: ['product', slug], queryFn: () => get<Product>(`/products/${slug}/`) })

export const useRelated = (slug: string) =>
  useQuery({ queryKey: ['related', slug], queryFn: () => get<ProductCard[]>(`/products/${slug}/related/`), ...STATIC })

export const useSuggest = (q: string) =>
  useQuery({
    queryKey: ['suggest', q],
    queryFn: () =>
      get<{ products: ProductCard[]; collections: { title: string; slug: string }[] }>('/search/suggest/', { q }),
    enabled: q.trim().length >= 2,
    placeholderData: keepPreviousData,
  })

export const usePage = (kind: 'pages' | 'policies', slug: string) =>
  useQuery({ queryKey: [kind, slug], queryFn: () => get<Page>(`/${kind}/${slug}/`), retry: false })

export const useVideos = () => useQuery({ queryKey: ['videos'], queryFn: () => get<Video[]>('/videos/'), ...STATIC })
