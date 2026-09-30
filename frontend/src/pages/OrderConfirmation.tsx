import { CheckCircle2 } from 'lucide-react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { OrderSummary } from '@/components/OrderSummary'
import { Seo } from '@/components/ui'
import type { Order } from '@/lib/types'

export default function OrderConfirmation() {
  const { number } = useParams()
  const order = (useLocation().state as { order?: Order } | null)?.order

  return (
    <div className="smoke container-page max-w-2xl py-16 text-center">
      <Seo title="Order received" />
      <CheckCircle2 className="mx-auto size-12 text-success" />
      <h1 className="section-title mt-4">Thank you!</h1>
      <p className="mt-3 text-muted">
        We received your order request <strong className="text-text">{number}</strong>. A confirmation email is on its
        way, and we’ll contact you shortly to confirm delivery.
      </p>
      {order && (
        <div className="mt-8">
          <OrderSummary order={order} />
        </div>
      )}
      <div className="mt-8 flex justify-center gap-3">
        <Link to="/" className="btn-primary">
          Keep shopping
        </Link>
        <Link to="/orders/track" className="btn-outline">
          Track order
        </Link>
      </div>
    </div>
  )
}
