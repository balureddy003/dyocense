import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type User = {
    id?: string
    user_id?: string
    name?: string
    full_name?: string
    email?: string
} | null

type AuthState = {
    apiToken?: string
    tenantId?: string
    user: User
    setAuth: (opts: { apiToken: string; tenantId?: string; user?: User }) => void
    clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            apiToken: undefined,
            tenantId: undefined,
            user: null,
            setAuth: ({ apiToken, tenantId, user }) => {
                set({ apiToken, tenantId, user: user ?? null })
            },
            clearAuth: () => {
                set({ apiToken: undefined, tenantId: undefined, user: null })
            },
        }),
        {
            name: 'dyocense-auth',
            partialize: (state) => ({
                apiToken: state.apiToken,
                tenantId: state.tenantId,
                user: state.user,
            }),
        }
    )
)
