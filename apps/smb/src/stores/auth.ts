import { create } from 'zustand';

export type User = { id?: string; name?: string; email?: string } | null

type AuthState = {
    apiToken?: string
    tenantId?: string
    user: User
    setAuth: (opts: { apiToken: string; tenantId?: string; user?: User }) => void
    clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
    apiToken: (typeof window !== 'undefined' && localStorage.getItem('apiToken')) ?? undefined,
    tenantId: (typeof window !== 'undefined' && localStorage.getItem('tenantId')) ?? undefined,
    user: null,
    setAuth: ({ apiToken, tenantId, user }) => {
        if (typeof window !== 'undefined') {
            if (apiToken) localStorage.setItem('apiToken', apiToken)
            if (tenantId) localStorage.setItem('tenantId', tenantId)
        }
        set({ apiToken, tenantId, user: user ?? null })
    },
    clearAuth: () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('apiToken')
            localStorage.removeItem('tenantId')
        }
        set({ apiToken: undefined, tenantId: undefined, user: null })
    },
}))
