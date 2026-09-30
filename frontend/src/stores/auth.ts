import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { User } from '@/lib/types'

type AuthState = {
  access: string | null
  refresh: string | null
  user: User | null
  setSession: (s: { access: string; refresh: string; user: User }) => void
  setAccess: (access: string, refresh?: string) => void
  setUser: (user: User) => void
  clear: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      setSession: ({ access, refresh, user }) => set({ access, refresh, user }),
      setAccess: (access, refresh) => set((s) => ({ access, refresh: refresh ?? s.refresh })),
      setUser: (user) => set({ user }),
      clear: () => set({ access: null, refresh: null, user: null }),
    }),
    { name: 'suqilic-auth' },
  ),
)
