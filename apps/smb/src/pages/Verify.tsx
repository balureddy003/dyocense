import React from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { tryPost } from '../lib/api'
import { useAuthStore } from '../stores/auth'

export default function Verify() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const setAuth = useAuthStore((s) => s.setAuth)
    const token = searchParams.get('token')
    const next = searchParams.get('next') ?? '/home'
    const [status, setStatus] = React.useState<'processing' | 'error'>('processing')
    const [message, setMessage] = React.useState('Checking your link…')

    React.useEffect(() => {
        if (!token) {
            setStatus('error')
            setMessage('Missing verification token.')
            return
        }
        let isMounted = true
            ; (async () => {
                try {
                    const data = await tryPost<{ jwt?: string; token?: string; tenant_id?: string; tenant?: string; user?: any }>(
                        '/v1/auth/verify',
                        { token },
                    )
                    const jwt = data?.jwt || data?.token || 'dev-jwt'
                    const tenantId = data?.tenant_id || data?.tenant || 'dev-tenant'
                    if (typeof window !== 'undefined') {
                        localStorage.setItem('apiToken', jwt)
                        localStorage.setItem('tenantId', tenantId)
                    }
                    if (isMounted) {
                        setAuth({ apiToken: jwt, tenantId, user: data?.user ?? { name: 'Owner' } })

                        // Check if user has completed onboarding
                        const hasCompletedOnboarding = localStorage.getItem('hasCompletedOnboarding')
                        const destination = hasCompletedOnboarding ? next : '/welcome'

                        navigate(destination, { replace: true })
                    }
                } catch (err) {
                    if (!isMounted) return
                    setStatus('error')
                    setMessage('Verification failed. Request a new magic link below.')
                }
            })()
        return () => {
            isMounted = false
        }
    }, [token, setAuth, navigate, next])

    return (
        <div className="mx-auto max-w-3xl rounded-3xl border border-slate-200 bg-white px-6 py-12 text-center shadow-card">
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand">Verification</p>
            <h1 className="mt-4 text-3xl font-semibold text-slate-900">We’re logging you in</h1>
            <p className="mt-4 text-slate-500">{message}</p>
            {status === 'processing' ? (
                <div className="mt-8 inline-flex animate-pulse items-center gap-3 rounded-full border border-slate-200 px-5 py-2 text-sm text-slate-500">
                    <span className="h-2 w-2 rounded-full bg-brand" />
                    Securing access • provisioning automations • syncing metadata
                </div>
            ) : (
                <Link className="mt-6 inline-flex text-sm font-semibold text-brand" to="/signup">
                    Request a new link
                </Link>
            )}
        </div>
    )
}
