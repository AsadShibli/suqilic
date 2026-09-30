import { Link } from 'react-router-dom'

import { useCart } from '@/api/cart'
import { useMoney } from '@/api/storefront'
import { useCartUi } from '@/stores/cart'

import { CartLines } from '../cart/CartLines'
import { Drawer } from '../Drawer'
import { EmptyState } from '../ui'

export function CartDrawer() {
  const { drawerOpen, closeDrawer } = useCartUi()
  const { data: cart } = useCart()
  const money = useMoney()
  const hasItems = Boolean(cart?.items.length)

  return (
    <Drawer
      open={drawerOpen}
      onClose={closeDrawer}
      title={`Cart (${cart?.item_count ?? 0})`}
      footer={
        hasItems && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted">Subtotal</span>
              <span className="font-semibold">{money(cart?.subtotal)}</span>
            </div>
            <Link to="/checkout" onClick={closeDrawer} className="btn-primary w-full">
              Place order request
            </Link>
            <Link to="/cart" onClick={closeDrawer} className="btn-outline w-full">
              View cart
            </Link>
          </div>
        )
      }
    >
      {hasItems ? (
        <div className="px-5">
          <CartLines items={cart!.items} compact onNavigate={closeDrawer} />
        </div>
      ) : (
        <EmptyState title="Your cart is empty">
          <button onClick={closeDrawer} className="btn-outline">
            Continue shopping
          </button>
        </EmptyState>
      )}
    </Drawer>
  )
}
