import { useState } from 'react'

import { useTrackOrder } from '@/api/account'
import { OrderSummary } from '@/components/OrderSummary'
import { Seo, Spinner } from '@/components/ui'

export default function TrackOrder() {
  const [params, setParams] = useState<{ order_number: string; email: string } | null>(null)
  const { data: order, isFetching, isError } = useTrackOrder(params)

  return (
    <div className="container-page max-w-xl py-16">
      <Seo title="Track your order" />
      <h1 className="section-title mb-8 text-center">Track your order</h1>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          const form = new FormData(e.currentTarget)
          setParams({ order_number: String(form.get('order_number')).trim(), email: String(form.get('email')).trim() })
        }}
      >
        <input name="order_number" required className="input" placeholder="Order number (e.g. SQ-000123)" />
        <input name="email" type="email" required className="input" placeholder="Email used for the order" />
        <button className="btn-primary w-full" disabled={isFetching}>
          {isFetching ? <Spinner className="size-4" /> : 'Find order'}
        </button>
      </form>
      <div className="mt-8">
        {isError && <p className="text-center text-danger">No order matches those details.</p>}
        {order && <OrderSummary order={order} />}
      </div>
    </div>
  )
}
