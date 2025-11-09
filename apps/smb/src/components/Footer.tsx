import { Link } from 'react-router-dom'

export default function Footer() {
    return (
        <footer className="border-t border-white/5 bg-night-900/70">
            <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-4 py-6 text-sm text-slate-400 md:flex-row md:px-6">
                <p>© {new Date().getFullYear()} Dyocense. All rights reserved.</p>
                <nav className="flex items-center gap-4">
                    <Link className="hover:text-white" to="/">
                        Overview
                    </Link>
                    <Link className="hover:text-white" to="/signup">
                        Start trial
                    </Link>
                    <Link className="hover:text-white" to="/tools">
                        Tools
                    </Link>
                </nav>
            </div>
        </footer>
    )
}
