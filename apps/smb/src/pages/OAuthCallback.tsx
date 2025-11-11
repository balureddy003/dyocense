import React from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { post } from '../lib/api'
import { useAuthStore } from '../stores/auth'

export default function OAuthCallback() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const setAuth = useAuthStore((s) => s.setAuth)

    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const provider = window.location.pathname.split('/').pop() // get provider from path
    const [status, setStatus] = React.useState<'processing' | 'error'>('processing')
    const [message, setMessage] = React.useState('Completing sign in...')

    React.useEffect(() => {
        if (!code || !state) {
            setStatus('error')
            setMessage('Invalid OAuth callback. Missing parameters.')
            return
        }

        let isMounted = true
            ; (async () => {
                try {
                    const data = await post<{
                        token?: string
                        tenant_id?: string
                        user_id?: string
                        expires_in?: number
                        user?: {
                            user_id?: string
                            email?: string
                            full_name?: string
                        }
                    }>(
                        `/v1/auth/${provider}/callback`,
                        { code, state },
                    )

                    const jwt = data?.token
                    const tenantId = data?.tenant_id

                    if (!jwt || !tenantId) {
                        throw new Error('Invalid authentication response')
                    }

                    // Extract user information
                    const user = data?.user ? {
                        user_id: data.user.user_id,
                        email: data.user.email,
                        full_name: data.user.full_name,
                    } : null

                    if (isMounted) {
                        // Set auth in store (which persists to localStorage automatically)
                        setAuth({ apiToken: jwt, tenantId, user })

                        // Check if user has completed onboarding
                        const hasCompletedOnboarding = localStorage.getItem('hasCompletedOnboarding')
                        const destination = hasCompletedOnboarding ? '/home' : '/welcome'

                        navigate(destination, { replace: true })
                    }
                } catch (err) {
                    if (!isMounted) return
                    console.error('OAuth callback error:', err)
                    setStatus('error')
                    setMessage('Authentication failed. Please try again.')
                }
            })()
        return () => {
            isMounted = false
        }
    }, [code, state, provider, setAuth, navigate])

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
            <div className="mx-auto max-w-md rounded-3xl border border-slate-700 bg-slate-800 px-8 py-12 text-center shadow-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-400">OAuth Authentication</p>
                <h1 className="mt-4 text-3xl font-semibold text-white">
                    {status === 'processing' ? 'Signing you in...' : 'Authentication Failed'}
                </h1>
                <p className="mt-4 text-slate-300">{message}</p>
                {status === 'processing' ? (
                    <div className="mt-8 inline-flex animate-pulse items-center gap-3 rounded-full border border-slate-600 px-5 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-indigo-500" />
                        Securing access • Syncing your profile
                    </div>
                ) : (
                    <div className="mt-8 space-y-3">
                        <a href="/login" className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors">
                            Try again
                        </a>
                        <p className="text-xs text-slate-400">
                            Or <a href="/contact" className="text-indigo-400 hover:underline">contact support</a> if you need help
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
