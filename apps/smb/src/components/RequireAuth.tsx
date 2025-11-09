import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'

type Props = {
    children: ReactNode
}

export default function RequireAuth({ children }: Props) {
    const apiToken = useAuthStore((s) => s.apiToken)
    const location = useLocation()

    if (!apiToken) {
        const params = new URLSearchParams({
            next: location.pathname + location.search,
        })
        return <Navigate replace to={`/signup?${params.toString()}`} />
    }

    return <>{children}</>
}
