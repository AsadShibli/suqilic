import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'
import type { Order, Paginated, SavedAddress, User } from '@/lib/types'
import { useAuth } from '@/stores/auth'
import { useCartUi } from '@/stores/cart'

type Session = { access: string; refresh: string; user: User }

/** Store the session and fold any guest cart into the account cart. */
function useStartSession() {
  const qc = useQueryClient()
  return async (session: Session) => {
    useAuth.getState().setSession(session)
    const { cartId, setCartId } = useCartUi.getState()
    if (cartId) {
      await api.post('/cart/merge/', { cart_id: cartId }).catch(() => undefined)
      setCartId(null)
    }
    qc.invalidateQueries({ queryKey: ['cart'] })
  }
}

export function useLogin(endpoint = '/auth/login/') {
  const start = useStartSession()
  return useMutation({
    mutationFn: (body: { email: string; password: string }) => api.post<Session>(endpoint, body).then((r) => r.data),
    onSuccess: start,
  })
}

export function useRegister() {
  const start = useStartSession()
  return useMutation({
    mutationFn: (body: { email: string; password: string; first_name: string; last_name: string }) =>
      api.post<Session>('/auth/register/', body).then((r) => r.data),
    onSuccess: start,
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return async () => {
    const { refresh, clear } = useAuth.getState()
    if (refresh) await api.post('/auth/logout/', { refresh }).catch(() => undefined)
    clear()
    qc.clear()
  }
}

export const useRequestPasswordReset = () =>
  useMutation({ mutationFn: (email: string) => api.post('/auth/password-reset/', { email }) })

export const useConfirmPasswordReset = () =>
  useMutation({
    mutationFn: (body: { uid: string; token: string; new_password: string }) =>
      api.post('/auth/password-reset/confirm/', body),
  })

export function useUpdateMe() {
  const setUser = useAuth((s) => s.setUser)
  return useMutation({
    mutationFn: (body: Partial<User>) => api.patch<User>('/me/', body).then((r) => r.data),
    onSuccess: setUser,
  })
}

export const useMyOrders = () =>
  useQuery({ queryKey: ['me', 'orders'], queryFn: () => api.get<Paginated<Order>>('/me/orders/').then((r) => r.data) })

export const useMyAddresses = () =>
  useQuery({ queryKey: ['me', 'addresses'], queryFn: () => api.get<SavedAddress[]>('/me/addresses/').then((r) => r.data) })

export const useTrackOrder = (params: { order_number: string; email: string } | null) =>
  useQuery({
    queryKey: ['track', params],
    queryFn: () => api.get<Order>('/orders/track/', { params: params! }).then((r) => r.data),
    enabled: Boolean(params),
    retry: false,
  })
