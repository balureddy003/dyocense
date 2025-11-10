import { ReactNode, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'

interface PlatformLayoutProps {
    children: ReactNode
}

const navItems = [
    { path: '/home', label: 'Dashboard', icon: '📊', description: 'Your daily business snapshot' },
    { path: '/goals', label: 'Goals', icon: '🎯', description: 'Set and track objectives' },
    { path: '/planner', label: 'Action Plan', icon: '✅', description: 'Weekly tasks and priorities' },
    { path: '/coach', label: 'Coach', icon: '💡', description: 'AI business coach' },
    { path: '/analytics', label: 'Analytics', icon: '📈', description: 'Track your progress' },
    { path: '/achievements', label: 'Achievements', icon: '🏆', description: 'Unlock badges' },
    { path: '/connectors', label: 'Data', icon: '🔗', description: 'Connected sources' },
]

export default function PlatformLayout({ children }: PlatformLayoutProps) {
    const location = useLocation()
    const navigate = useNavigate()
    const clearAuth = useAuthStore((s) => s.clearAuth)
    const tenantId = useAuthStore((s) => s.tenantId)
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

    const handleSignOut = () => {
        clearAuth()
        navigate('/', { replace: true })
    }

    const isActive = (path: string) => location.pathname === path

    return (
        <div className="flex min-h-screen flex-col bg-neutral-50">
            {/* Platform Header - Desktop & Tablet */}
            <header className="sticky top-0 z-50 border-b border-neutral-200 bg-white shadow-sm backdrop-blur-md">
                <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
                    {/* Logo & Workspace */}
                    <div className="flex items-center gap-3">
                        <Link to="/home" className="flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-600 to-brand-700 text-white">
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <span className="hidden text-lg font-semibold text-neutral-900 sm:inline">Dyocense</span>
                        </Link>
                        {tenantId && (
                            <div className="hidden rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-700 lg:block">
                                Workspace: {tenantId.slice(0, 8)}...
                            </div>
                        )}
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden items-center gap-1 md:flex">
                        {navItems.slice(0, 5).map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${isActive(item.path)
                                    ? 'bg-brand-600/10 text-brand-700'
                                    : 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
                                    }`}
                            >
                                {item.label}
                            </Link>
                        ))}
                    </nav>

                    {/* User Menu */}
                    <div className="flex items-center gap-2">
                        <Link
                            to="/connectors"
                            className="hidden items-center gap-1 rounded-lg border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 transition hover:border-brand-600 hover:text-brand-700 md:inline-flex"
                        >
                            <span>�</span>
                            <span className="hidden lg:inline">Data Sources</span>
                        </Link>
                        <button
                            type="button"
                            onClick={handleSignOut}
                            className="hidden rounded-lg px-3 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100 hover:text-neutral-900 md:inline-flex"
                        >
                            Sign out
                        </button>

                        {/* Mobile Menu Button */}
                        <button
                            type="button"
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-neutral-700 hover:bg-neutral-100 md:hidden"
                            aria-label="Toggle menu"
                        >
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                {mobileMenuOpen ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                )}
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Mobile Menu Dropdown */}
                {mobileMenuOpen && (
                    <div className="border-t border-neutral-200 bg-white md:hidden">
                        <nav className="space-y-1 px-4 py-3">
                            {navItems.map((item) => (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={`flex items-center gap-3 rounded-lg px-3 py-3 text-base font-medium transition ${isActive(item.path) ? 'bg-brand-600/10 text-brand-700' : 'text-neutral-700 hover:bg-neutral-100'
                                        }`}
                                >
                                    <span className="text-xl">{item.icon}</span>
                                    <span>{item.label}</span>
                                </Link>
                            ))}
                            <button
                                type="button"
                                onClick={() => {
                                    setMobileMenuOpen(false)
                                    handleSignOut()
                                }}
                                className="flex w-full items-center gap-3 rounded-lg px-3 py-3 text-base font-medium text-red-600 hover:bg-red-50"
                            >
                                <span className="text-xl">🚪</span>
                                <span>Sign out</span>
                            </button>
                        </nav>
                    </div>
                )}
            </header>

            {/* Main Content - Mobile Optimized Padding */}
            <main className="flex-1 px-4 py-4 pb-20 sm:px-6 sm:py-6 md:pb-6 lg:px-8">{children}</main>

            {/* Bottom Navigation - Mobile Only */}
            <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-neutral-200 bg-white shadow-lg backdrop-blur-md md:hidden">
                <div className="grid grid-cols-5 gap-1 px-2 py-2">
                    {navItems.slice(0, 5).map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`flex flex-col items-center gap-1 rounded-lg px-2 py-2 text-xs font-medium transition ${isActive(item.path) ? 'bg-brand-600/10 text-brand-700' : 'text-neutral-700 active:bg-neutral-100'
                                }`}
                        >
                            <span className="text-xl">{item.icon}</span>
                            <span className="text-[10px]">{item.label}</span>
                        </Link>
                    ))}
                </div>
            </nav>
        </div>
    )
}
