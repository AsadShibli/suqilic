import { Menu, Search, ShoppingBag, User } from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { useCart } from '@/api/cart'
import { useMenu, useSettings } from '@/api/storefront'
import { useAuth } from '@/stores/auth'
import { useCartUi } from '@/stores/cart'

import { Drawer } from '../Drawer'
import { SearchPanel } from './SearchPanel'

export function Header() {
  const { data: settings } = useSettings()
  const { data: menu = [] } = useMenu('header')
  const { data: cart } = useCart()
  const openCart = useCartUi((s) => s.openDrawer)
  const user = useAuth((s) => s.user)
  const [searchOpen, setSearchOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <>
      {settings?.announcement_active && settings.announcement_text && (
        <div className="bg-accent py-2 text-center text-sm font-semibold tracking-wide text-bg uppercase">
          {settings.announcement_link ? (
            <Link to={settings.announcement_link}>{settings.announcement_text}</Link>
          ) : (
            settings.announcement_text
          )}
        </div>
      )}
      <header className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur">
        <div className="container-page grid grid-cols-[1fr_auto_1fr] items-center py-3">
          <div className="flex items-center gap-1">
            <button className="p-2 lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open menu">
              <Menu className="size-5" />
            </button>
            <button className="p-2" onClick={() => setSearchOpen(true)} aria-label="Search">
              <Search className="size-5" />
            </button>
          </div>
          <Link to="/" aria-label={settings?.store_name ?? 'Suqilic'}>
            <img src="/logo.png" alt={settings?.store_name ?? 'Suqilic'} className="h-8 w-auto md:h-10" />
          </Link>
          <div className="flex items-center justify-end gap-1">
            <Link to={user ? '/account' : '/account/login'} className="p-2" aria-label="Account">
              <User className="size-5" />
            </Link>
            <button className="relative p-2" onClick={openCart} aria-label="Open cart">
              <ShoppingBag className="size-5" />
              {Boolean(cart?.item_count) && (
                <span className="absolute -top-0.5 -right-0.5 flex size-5 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-bg">
                  {cart!.item_count}
                </span>
              )}
            </button>
          </div>
        </div>
        <nav className="container-page hidden pb-3 lg:block" aria-label="Main">
          <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2">
            {menu.map((item) => (
              <li key={item.id}>
                <NavLink
                  to={item.url}
                  className={({ isActive }) =>
                    `text-sm font-semibold tracking-wide uppercase transition-colors hover:text-accent ${isActive ? 'text-accent underline underline-offset-8' : 'text-text/80'}`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
      <Drawer open={menuOpen} onClose={() => setMenuOpen(false)} title="Menu" side="left">
        <nav aria-label="Mobile">
          <ul className="divide-y divide-border">
            {menu.map((item) => (
              <li key={item.id}>
                <Link
                  to={item.url}
                  onClick={() => setMenuOpen(false)}
                  className="block px-5 py-4 text-sm font-semibold tracking-widest uppercase"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </Drawer>
    </>
  )
}
