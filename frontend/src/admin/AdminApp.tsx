import clsx from 'clsx'
import {
  FileText,
  Home,
  Image,
  LayoutDashboard,
  Layers,
  LogOut,
  Mail,
  Menu as MenuIcon,
  Package,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Tag,
  Users,
  Video,
  X,
} from 'lucide-react'
import { lazy, Suspense, useState } from 'react'
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'

import { useLogout } from '@/api/account'
import { PageLoader } from '@/components/ui'
import { ADMIN_PATH } from '@/lib/config'
import { useAuth } from '@/stores/auth'

import { ConfirmHost } from './components/ConfirmDialog'
import AdminLogin from './pages/Login'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Products = lazy(() => import('./pages/Products'))
const ProductEdit = lazy(() => import('./pages/ProductEdit'))
const Collections = lazy(() => import('./pages/Collections'))
const Orders = lazy(() => import('./pages/Orders'))
const OrderDetail = lazy(() => import('./pages/OrderDetail'))
const Content = () => import('./pages/Content')
const Tags = lazy(() => Content().then((m) => ({ default: m.Tags })))
const HomeSections = lazy(() => Content().then((m) => ({ default: m.HomeSections })))
const Banners = lazy(() => Content().then((m) => ({ default: m.Banners })))
const Menus = lazy(() => Content().then((m) => ({ default: m.Menus })))
const Pages = lazy(() => Content().then((m) => ({ default: m.Pages })))
const Videos = lazy(() => Content().then((m) => ({ default: m.Videos })))
const People = () => import('./pages/People')
const Customers = lazy(() => People().then((m) => ({ default: m.Customers })))
const Messages = lazy(() => People().then((m) => ({ default: m.Messages })))
const Subscribers = lazy(() => People().then((m) => ({ default: m.Subscribers })))
const Staff = lazy(() => People().then((m) => ({ default: m.Staff })))
const SiteSettings = lazy(() => import('./pages/SiteSettings'))

const NAV = [
  { to: '', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: 'orders', label: 'Orders', icon: ShoppingCart },
  { to: 'products', label: 'Products', icon: Package },
  { to: 'collections', label: 'Collections', icon: Layers },
  { to: 'tags', label: 'Tags', icon: Tag },
  { to: 'home', label: 'Home page', icon: Home },
  { to: 'banners', label: 'Hero banners', icon: Image },
  { to: 'menus', label: 'Menus', icon: MenuIcon },
  { to: 'pages', label: 'Pages & policies', icon: FileText },
  { to: 'videos', label: 'How-to videos', icon: Video },
  { to: 'customers', label: 'Customers', icon: Users },
  { to: 'messages', label: 'Messages', icon: Mail },
  { to: 'subscribers', label: 'Subscribers', icon: Mail },
  { to: 'settings', label: 'Settings', icon: Settings },
  { to: 'staff', label: 'Staff', icon: ShieldCheck, superuser: true },
]

export default function AdminApp() {
  const user = useAuth((s) => s.user)
  const logout = useLogout()
  const [navOpen, setNavOpen] = useState(false)

  if (!user?.is_staff) return <AdminLogin />

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <title>Admin | Suqilic</title>
      <meta name="robots" content="noindex, nofollow" />
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-border bg-surface transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0',
          !navOpen && '-translate-x-full',
        )}
      >
        <div className="flex items-center justify-between border-b border-border p-4">
          <Link to={ADMIN_PATH} onClick={() => setNavOpen(false)}>
            <img src="/logo.png" alt="Suqilic" className="h-8" />
          </Link>
          <button className="lg:hidden" onClick={() => setNavOpen(false)} aria-label="Close menu">
            <X className="size-5" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-2" aria-label="Admin">
          {NAV.filter((n) => !n.superuser || user.is_superuser).map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={label}
              to={to ? `${ADMIN_PATH}/${to}` : ADMIN_PATH}
              end={end}
              onClick={() => setNavOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-sm px-3 py-2 text-sm',
                  isActive ? 'bg-accent text-bg' : 'text-muted hover:bg-surface-2 hover:text-text',
                )
              }
            >
              <Icon className="size-4" /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3 text-xs text-muted">
          <p className="truncate">{user.email}</p>
          <div className="mt-2 flex gap-3">
            <a href="/" target="_blank" rel="noreferrer" className="hover:text-text">
              View store
            </a>
            <button onClick={logout} className="inline-flex items-center gap-1 hover:text-text">
              <LogOut className="size-3" /> Log out
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex items-center border-b border-border bg-bg/90 p-3 backdrop-blur lg:hidden">
          <button onClick={() => setNavOpen(true)} aria-label="Open menu">
            <MenuIcon className="size-5" />
          </button>
        </header>
        <main className="p-4 md:p-8">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route index element={<Dashboard />} />
              <Route path="orders" element={<Orders />} />
              <Route path="orders/:id" element={<OrderDetail />} />
              <Route path="products" element={<Products />} />
              <Route path="products/:id" element={<ProductEdit />} />
              <Route path="collections" element={<Collections />} />
              <Route path="tags" element={<Tags />} />
              <Route path="home" element={<HomeSections />} />
              <Route path="banners" element={<Banners />} />
              <Route path="menus" element={<Menus />} />
              <Route path="pages" element={<Pages />} />
              <Route path="videos" element={<Videos />} />
              <Route path="customers" element={<Customers />} />
              <Route path="messages" element={<Messages />} />
              <Route path="subscribers" element={<Subscribers />} />
              <Route path="settings" element={<SiteSettings />} />
              {user.is_superuser && <Route path="staff" element={<Staff />} />}
              <Route path="*" element={<Navigate to={ADMIN_PATH} replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
      <ConfirmHost />
    </div>
  )
}
