import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { api, errorMessage } from '@/lib/api'
import type { Address, Cart, Order } from '@/lib/types'
import { useAuth } from '@/stores/auth'
import { useCartUi } from '@/stores/cart'

const CART_KEY = ['cart']

export function useCart() {
  const cartId = useCartUi((s) => s.cartId)
  const access = useAuth((s) => s.access)
  return useQuery({
    queryKey: [...CART_KEY, access ? 'user' : cartId],
    queryFn: () => api.get<Cart>('/cart/').then((r) => r.data),
  })
}

function useCartMutation<V>(fn: (vars: V) => Promise<Cart>, onSuccess?: () => void) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CART_KEY })
      onSuccess?.()
    },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useAddToCart() {
  const openDrawer = useCartUi((s) => s.openDrawer)
  return useCartMutation(
    (vars: { variant_id: number; quantity: number }) => api.post<Cart>('/cart/items/', vars).then((r) => r.data),
    openDrawer,
  )
}

export const useUpdateCartItem = () =>
  useCartMutation(({ id, quantity }: { id: number; quantity: number }) =>
    api.patch<Cart>(`/cart/items/${id}/`, { quantity }).then((r) => r.data),
  )

export const useRemoveCartItem = () =>
  useCartMutation((id: number) => api.delete<Cart>(`/cart/items/${id}/`).then((r) => r.data))

export type OrderRequest = Address & { email: string; customer_note: string }

export function usePlaceOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: OrderRequest) => api.post<Order>('/orders/', body).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: CART_KEY }),
  })
}
