import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { primaryButton } from '../lib/theme'

interface PublicLayoutProps {
    children: ReactNode
    showNav?: boolean
}

export default function PublicLayout({ children, showNav = true }: PublicLayoutProps) {
    return (
        <div className="marketing-surface flex min-h-screen flex-col">
            <header className="sticky top-0 z-50 border-b border-violet-100 bg-white/95 shadow-sm backdrop-blur-xl">
                <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
                    <Link to="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 text-white shadow-md">
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <span className="text-lg font-bold text-gray-900">Dyocense</span>
                    </Link>

                    {showNav && (
                        <>
                            <nav className="hidden items-center gap-6 md:flex">
                                <a href="/#features" className="text-sm font-medium text-gray-700 transition-colors duration-200 hover:text-brand-600">
                                    How it works
                                </a>
                                <a href="/#pricing" className="text-sm font-medium text-gray-700 transition-colors duration-200 hover:text-brand-600">
                                    Pricing
                                </a>
                                <Link to="/tools" className="text-sm font-medium text-gray-700 transition-colors duration-200 hover:text-brand-600">
                                    Success stories
                                </Link>
                                <Link to="/contact" className="text-sm font-medium text-gray-700 transition-colors duration-200 hover:text-brand-600">
                                    Talk to a coach
                                </Link>
                            </nav>

                            <div className="hidden items-center gap-3 md:flex">
                                <Link to="/login" className="text-sm font-semibold text-gray-700 transition-colors duration-200 hover:text-brand-600">
                                    Sign in
                                </Link>
                                <Link to="/signup" className={`${primaryButton} text-sm`}>
                                    Start free
                                </Link>
                            </div>

                            <button
                                type="button"
                                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl text-gray-700 transition-colors duration-200 hover:bg-gray-100 md:hidden"
                                aria-label="Open menu"
                            >
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>
                        </>
                    )}
                </div>
            </header>

            <main className="flex-1 py-10">{children}</main>

            <footer className="border-t border-violet-100 bg-white/95 backdrop-blur-xl">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-900">Platform</h3>
                            <ul className="space-y-2 text-sm text-gray-600">
                                <li>
                                    <Link to="/tools" className="transition-colors duration-200 hover:text-brand-600">
                                        How it works
                                    </Link>
                                </li>
                                <li>
                                    <a href="/#pricing" className="transition-colors duration-200 hover:text-brand-600">
                                        Pricing plans
                                    </a>
                                </li>
                                <li>
                                    <Link to="/contact" className="transition-colors duration-200 hover:text-brand-600">
                                        Get a demo
                                    </Link>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-900">Resources</h3>
                            <ul className="space-y-2 text-sm text-gray-600">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Success stories
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Business tips
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Community
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-900">Support</h3>
                            <ul className="space-y-2 text-sm text-gray-600">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Help center
                                    </a>
                                </li>
                                <li>
                                    <Link to="/contact" className="transition-colors duration-200 hover:text-brand-600">
                                        Talk to a coach
                                    </Link>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        System status
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-900">Legal</h3>
                            <ul className="space-y-2 text-sm text-gray-600">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Privacy policy
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Terms of service
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-brand-600">
                                        Data security
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="mt-8 border-t border-violet-100 pt-6 text-center text-sm text-gray-600">
                        © {new Date().getFullYear()} Dyocense. Your business fitness coach.
                    </div>
                </div>
            </footer>
        </div>
    )
}
