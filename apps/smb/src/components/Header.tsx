import { Link, useNavigate } from 'react-router-dom'
import { primaryButton, secondaryButton } from '../lib/theme'
import { useAuthStore } from '../stores/auth'

export default function Header() {
    const apiToken = useAuthStore((s) => s.apiToken)
    const clearAuth = useAuthStore((s) => s.clearAuth)
    const isAuthenticated = Boolean(apiToken)
    const navigate = useNavigate()

    const handleSignOut = () => {
        clearAuth()
        navigate('/', { replace: true })
    }

    return (
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
            <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 md:px-6">
                <Link to="/" className="text-lg font-semibold tracking-tight text-white">
                    Dyocense
                </Link>
                <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
                    {isAuthenticated ? (
                        <>
                            <Link to="/tools" className="transition hover:text-white">
                                Tools
                            </Link>
                            <Link to="/connectors" className="transition hover:text-white">
                                Connectors
                            </Link>
                            <Link to="/copilot" className="transition hover:text-white">
                                Copilot
                            </Link>
                            <Link to="/home" className="transition hover:text-white">
                                Workspace
                            </Link>
                            <Link to="/planner" className={secondaryButton}>
                                Planner
                            </Link>
                            <button type="button" onClick={handleSignOut} className="text-sm font-semibold text-slate-600 hover:text-brand">
                                Sign out
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/#tools" className="transition hover:text-white">
                                Features
                            </Link>
                            <Link to="/#pricing" className="transition hover:text-white">
                                Pricing
                            </Link>
                            <Link to="/tools" className="transition hover:text-white">
                                Product tour
                            </Link>
                            <Link to="/contact" className="transition hover:text-white">
                                Talk to sales
                            </Link>
                            <Link to="/signup" className={primaryButton}>
                                Get started
                            </Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    )
}
