'use client'

import { create } from 'zustand'
import { api, User, getAuthToken, setAuthToken } from '@/lib/api'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    await api.login(email, password)
    const user = await api.getMe()
    set({ user, isAuthenticated: true })
  },

  register: async (email: string, password: string, name: string) => {
    await api.register(email, password, name)
    const user = await api.getMe()
    set({ user, isAuthenticated: true })
  },

  logout: async () => {
    await api.logout()
    set({ user: null, isAuthenticated: false })
  },

  checkAuth: async () => {
    set({ isLoading: true })
    try {
      const token = getAuthToken()
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false })
        return
      }
      const user = await api.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      setAuthToken(null)
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
