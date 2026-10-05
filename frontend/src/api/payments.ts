import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'

import { api, errorMessage } from '@/lib/api'

export const usePaymentConfig = () =>
  useQuery({
    queryKey: ['payment-config'],
    queryFn: () => api.get<{ online_payments: boolean }>('/payments/config/').then((r) => r.data),
    staleTime: 5 * 60_000,
  })

const PENDING_KEY = 'suqilic-pending-payment'
type PendingPayment = { order_number: string; email: string }

/** Remember which order is being paid so the result page can offer a retry after the gateway redirect. */
function rememberPendingPayment(value: PendingPayment) {
  try {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(value))
  } catch {
    // storage unavailable (private mode); retry falls back to order tracking
  }
}

export function readPendingPayment(): PendingPayment | null {
  try {
    return JSON.parse(sessionStorage.getItem(PENDING_KEY) ?? 'null')
  } catch {
    return null
  }
}

/** Open an SSLCommerz checkout session and send the browser to the hosted payment page. */
export function useStartPayment() {
  return useMutation({
    mutationFn: (body: PendingPayment) =>
      api.post<{ redirect_url: string }>('/payments/sslcommerz/start/', body).then((r) => r.data),
    onSuccess: ({ redirect_url }, body) => {
      rememberPendingPayment(body)
      window.location.assign(redirect_url)
    },
    onError: (e) => toast.error(errorMessage(e, 'Could not reach the payment gateway. Please try again.')),
  })
}
