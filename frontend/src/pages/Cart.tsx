import { Link } from 'react-router-dom'

import { useCart } from '@/api/cart'
import { useMoney } from '@/api/storefront'
import { CartLines } from '@/components/cart/CartLines'
import { EmptyState, PageLoader, Seo } from '@/components/ui'

export default function Cart() {
  const { data: cart, isLoading } = useCart()
  const money = useMoney()

  if (isLoading) return <PageLoader />

  return (
    <div className="container-page max-w-4xl py-10">
      <Seo title="Cart" />
      <h1 className="section-title mb-8">Your cart</h1>
      {cart?.items.length ? (
        <>
          <CartLines items={cart.items} />
          <div className="mt-8 flex flex-col items-end gap-4 border-t border-border pt-6">
            <p className="text-lg">
              Subtotal <span className="ml-4 font-semibold">{money(cart.subtotal)}</span>
            </p>
            <p className="text-sm text-muted">No payment needed now — we’ll contact you to confirm your order.</p>
            <Link to="/checkout" className="btn-primary">
              Place order request
            </Link>
          </div>
        </>
      ) : (
        <EmptyState title="Your cart is empty">
          <Link to="/" className="btn-primary">
            Continue shopping
          </Link>
        </EmptyState>
      )}
    </div>
  )
}
