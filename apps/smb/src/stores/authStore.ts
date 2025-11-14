import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type AuthUser = {
    sub: string
    tenant_id: string
    email: string
    role: string
}

type AuthStore = {
    token: string | null
    user: AuthUser | null
    setAuth: (token: string, user: AuthUser) => void
    clearAuth: () => void
    isAuthenticated: boolean
}

export const useAuthStore = create<AuthStore>()(
    persist(
        (set, get) => ({
            token: null,
            user: null,
            isAuthenticated: false,
            setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
            clearAuth: () => set({ token: null, user: null, isAuthenticated: false }),
        }),
        {
            name: 'auth-storage',
        }
    )
)
