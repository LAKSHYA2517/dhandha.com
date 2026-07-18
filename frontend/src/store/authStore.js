import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      supabaseUser: null,
      login: (token, user) => set({ token, user }),
      setSupabaseUser: (supabaseUser) => set({ supabaseUser }),
      logout: () => set({ token: null, user: null, supabaseUser: null }),
    }),
    { name: 'ciq-auth' }
  )
)
