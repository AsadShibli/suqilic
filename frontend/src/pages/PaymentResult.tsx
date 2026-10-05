import { CheckCircle2, Clock, XCircle } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { readPendingPayment, useStartPayment } from '@/api/payments'
import { Seo } from '@/components/ui'

const COPY = {
  paid: { icon: CheckCircle2, tone: 'text-success', title: 'Payment received', body: 'Thanks! Your order is paid and we’ll start preparing it.' },
  pending: { icon: Clock, tone: 'text-muted', title: 'Confirming your payment', body: 'The bank is still confirming the payment. Check back on the order tracking page shortly.' },
  cancelled: { icon: XCircle, tone: 'text-danger', title: 'Payment cancelled', body: 'You cancelled the payment. Your order is saved, so you can pay now or later.' },
  failed: { icon: XCircle, tone: 'text-danger', title: 'Payment failed', body: 'The payment didn’t go through and you were not charged. Your order is saved.' },
}

export default function PaymentResult() {
  const [params] = useSearchParams()
  const result = (params.get('result') ?? 'failed') as keyof typeof COPY
  const orderNumber = params.get('order')
  const { icon: Icon, tone, title, body } = COPY[result] ?? COPY.failed
  const pending = readPendingPayment()
  const canRetry = (result === 'failed' || result === 'cancelled') && pending?.order_number === orderNumber
  const startPayment = useStartPayment()

  return (
    <div className="smoke container-page max-w-xl py-16 text-center">
      <Seo title={title} />
      <Icon className={`mx-auto size-12 ${tone}`} />
      <h1 className="section-title mt-4">{title}</h1>
      <p className="mt-3 text-muted">
        {body}
        {orderNumber && (
          <>
            {' '}
            Order <strong className="text-text">{orderNumber}</strong>.
          </>
        )}
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {canRetry && pending && (
          <button className="btn-primary" disabled={startPayment.isPending} onClick={() => startPayment.mutate(pending)}>
            {startPayment.isPending ? 'Opening payment…' : 'Try payment again'}
          </button>
        )}
        <Link to="/orders/track" className="btn-outline">
          Track order
        </Link>
        <Link to="/" className={canRetry ? 'btn-outline' : 'btn-primary'}>
          Keep shopping
        </Link>
      </div>
    </div>
  )
}
