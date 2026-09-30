import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type CartUiState = {
  cartId: string | null
  drawerOpen: boolean
  setCartId: (id: string | null) => void
  openDrawer: () => void
  closeDrawer: () => void
}

/** Guest cart id (sent as X-Cart-Id) plus drawer UI state. Cart contents live in React Query. */
export const useCartUi = create<CartUiState>()(
  persist(
    (set) => ({
      cartId: null,
      drawerOpen: false,
      setCartId: (cartId) => set({ cartId }),
      openDrawer: () => set({ drawerOpen: true }),
      closeDrawer: () => set({ drawerOpen: false }),
    }),
    { name: 'suqilic-cart', partialize: (s) => ({ cartId: s.cartId }) },
  ),
)
