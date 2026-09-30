import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { useAuth } from '@/stores/auth'
import { useCartUi } from '@/stores/cart'

const { VITE_API_URL, VITE_API_HOST } = import.meta.env

/** Same-origin '/api/v1' in dev (Vite proxy); an explicit URL or host when the API lives elsewhere. */
export const api = axios.create({
  baseURL: VITE_API_URL || (VITE_API_HOST ? `https://${VITE_API_HOST}/api/v1` : '/api/v1'),
})

api.interceptors.request.use((config) => {
  const { access } = useAuth.getState()
  const { cartId } = useCartUi.getState()
  if (access) config.headers.Authorization = `Bearer ${access}`
  if (cartId && !access) config.headers['X-Cart-Id'] = cartId
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccess(): Promise<string | null> {
  const { refresh, setAccess, clear } = useAuth.getState()
  if (!refresh) return null
  try {
    const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh/`, { refresh })
    setAccess(data.access, data.refresh)
    return data.access
  } catch {
    clear()
    return null
  }
}

api.interceptors.response.use(
  (res) => {
    const cartId = res.headers['x-cart-id']
    if (cartId && !useAuth.getState().access) useCartUi.getState().setCartId(cartId)
    return res
  },
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    if (error.response?.status === 401 && original && !original._retried && useAuth.getState().refresh) {
      original._retried = true
      refreshing ??= refreshAccess().finally(() => (refreshing = null))
      const access = await refreshing
      if (access) {
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      }
    }
    return Promise.reject(error)
  },
)

/** Flatten DRF error payloads into a readable message. */
export function errorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  const data = (error as AxiosError<Record<string, unknown>>)?.response?.data
  if (!data || typeof data !== 'object') return fallback
  const first = Object.values(data)[0]
  if (typeof first === 'string') return first
  if (Array.isArray(first) && typeof first[0] === 'string') return first[0]
  return fallback
}

/** Map DRF field errors onto react-hook-form's setError. */
export function applyFieldErrors(error: unknown, setError: (name: never, e: { message: string }) => void) {
  const data = (error as AxiosError<Record<string, string[] | string>>)?.response?.data
  if (!data || typeof data !== 'object') return
  for (const [field, messages] of Object.entries(data)) {
    const message = Array.isArray(messages) ? messages[0] : messages
    if (typeof message === 'string') setError(field as never, { message })
  }
}
