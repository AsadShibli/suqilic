export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] }

export type Image = { id: number; image: string; thumbnail: string | null; alt_text: string; is_main: boolean; position: number }

export type ProductCard = {
  id: number
  title: string
  slug: string
  price_from: string | null
  has_price_range: boolean
  compare_at_price: string | null
  in_stock: boolean
  image: Image | null
}

export type Variant = {
  id: number
  title: string
  sku: string | null
  price: string
  stock_quantity: number
  in_stock: boolean
  options: Record<string, string>
}

export type Product = ProductCard & {
  description: string
  video_url: string
  images: Image[]
  options: { name: string; values: string[] }[]
  variants: Variant[]
  tags: string[]
  collections: { title: string; slug: string }[]
  seo_title: string
  seo_description: string
}

export type Collection = {
  id: number
  title: string
  slug: string
  description: string
  banner_image: string | null
  seo_title: string
  seo_description: string
}

export type HeroBanner = {
  id: number
  image_desktop: string
  image_mobile: string | null
  heading: string
  subheading: string
  button_text: string
  button_link: string
}

export type HomeSection = {
  id: number
  type: 'hero' | 'product_carousel'
  title: string
  view_all_link: string
  banners: HeroBanner[]
  products: ProductCard[]
}

export type SiteSettings = {
  store_name: string
  logo: string | null
  favicon: string | null
  announcement_text: string
  announcement_link: string
  announcement_active: boolean
  contact_email: string
  currency_symbol: string
  currency_code: string
  instagram_url: string
  tiktok_url: string
  seo_default_title: string
  seo_default_description: string
}

export type MenuItem = { id: number; label: string; url: string; children: MenuItem[] }

export type Page = { title: string; slug: string; page_type: 'page' | 'policy'; body: string; updated_at: string }

export type Video = { id: number; title: string; video_url: string; thumbnail: string | null; product_slug: string | null }

export type CartItem = {
  id: number
  variant: number
  quantity: number
  product_title: string
  product_slug: string
  variant_title: string
  unit_price: string
  stock_quantity: number
  line_total: string
  image: string | null
}

export type Cart = { id: string | null; items: CartItem[]; subtotal: string; item_count: number }

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'

export type OrderItem = {
  product_title: string
  product_slug: string | null
  variant_title: string
  sku: string
  unit_price: string
  quantity: number
  line_total: string
}

export type Address = {
  full_name: string
  phone: string
  line1: string
  line2: string
  city: string
  region: string
  postal_code: string
  country: string
}

export type Order = Address & {
  order_number: string
  status: OrderStatus
  email: string
  customer_note: string
  subtotal: string
  items: OrderItem[]
  created_at: string
}

export type User = {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string
  is_staff: boolean
  is_superuser: boolean
  date_joined: string
}

export type SavedAddress = Address & { id: number; is_default: boolean }
