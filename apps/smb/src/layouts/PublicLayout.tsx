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
            <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/70 shadow-[0_10px_30px_rgba(2,6,23,0.45)] backdrop-blur-xl">
                <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
                    <Link to="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg">
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <span className="text-lg font-semibold text-white">Dyocense</span>
                    </Link>

                    {showNav && (
                        <>
                            <nav className="hidden items-center gap-6 md:flex">
                                <a href="/#features" className="text-sm font-medium text-slate-200 transition-colors duration-200 hover:text-white">
                                    How it works
                                </a>
                                <a href="/#pricing" className="text-sm font-medium text-slate-200 transition-colors duration-200 hover:text-white">
                                    Pricing
                                </a>
                                <Link to="/tools" className="text-sm font-medium text-slate-200 transition-colors duration-200 hover:text-white">
                                    Success stories
                                </Link>
                                <Link to="/contact" className="text-sm font-medium text-slate-200 transition-colors duration-200 hover:text-white">
                                    Talk to a coach
                                </Link>
                            </nav>

                            <Link to="/signup" className={`${primaryButton} hidden text-sm md:inline-flex`}>
                                Start your journey
                            </Link>

                            <button
                                type="button"
                                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl text-slate-100 transition-colors duration-200 hover:bg-white/10 md:hidden"
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

            <footer className="border-t border-white/10 bg-slate-950/70 backdrop-blur-xl">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/80">Platform</h3>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li>
                                    <Link to="/tools" className="transition-colors duration-200 hover:text-white">
                                        How it works
                                    </Link>
                                </li>
                                <li>
                                    <a href="/#pricing" className="transition-colors duration-200 hover:text-white">
                                        Pricing plans
                                    </a>
                                </li>
                                <li>
                                    <Link to="/contact" className="transition-colors duration-200 hover:text-white">
                                        Get a demo
                                    </Link>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/80">Resources</h3>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Success stories
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Business tips
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Community
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/80">Support</h3>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Help center
                                    </a>
                                </li>
                                <li>
                                    <Link to="/contact" className="transition-colors duration-200 hover:text-white">
                                        Talk to a coach
                                    </Link>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        System status
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/80">Legal</h3>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Privacy policy
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Terms of service
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="transition-colors duration-200 hover:text-white">
                                        Data security
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="mt-8 border-t border-white/10 pt-6 text-center text-sm text-slate-400">
                        © {new Date().getFullYear()} Dyocense. Your business fitness coach.
                    </div>
                </div>
            </footer>
        </div>
    )
}
