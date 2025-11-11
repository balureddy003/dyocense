import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toolConfigs } from '../data/tools'
import { primaryButton, secondaryButton } from '../lib/theme'
import { useAuthStore } from '../stores/auth'

// Fitness-aligned headline bullets focusing on health, coaching, motivation
const heroHighlights = [
    'Live Business Health Score (close your rings for revenue, ops & customers)',
    'Weekly action plan from your AI coach',
    'Milestone celebrations & streak tracking to sustain momentum',
]

const benefitCards = [
    {
        title: 'Know Your Health',
        copy: 'Real-time business health score across revenue, cash flow, customers, inventory & operations.',
        icon: '📊',
    },
    {
        title: 'Set Clear Goals',
        copy: 'Type "Grow Q4 revenue 25%" — the coach turns it into a SMART, trackable objective.',
        icon: '🎯',
    },
    {
        title: 'Weekly Action Plan',
        copy: 'Receive 5–7 focused tasks. Check them off, build streaks, watch your score climb.',
        icon: '✅',
    },
    {
        title: 'Celebrate Progress',
        copy: 'Confetti for milestones, badges for streaks, uplifting coach insights keep motivation high.',
        icon: '🏆',
    },
    {
        title: 'Stay On Track',
        copy: 'Smart nudges when metrics slip or tasks stall—support without micromanagement.',
        icon: '🕒',
    },
    {
        title: 'Own Your Data',
        copy: 'Lightweight connectors (ERP, storefront, CSV). You control scopes & retention—no customer PII.',
        icon: '🔒',
    },
]

const journeySteps = [
    'Take a 60‑second assessment to generate your Business Health Score.',
    'Set or refine 1–3 priority goals (revenue, customers, cash flow, operations).',
    'Get your personalized weekly action plan from the AI coach.',
    'Check off tasks, build streaks, and watch your score improve.',
]

const connectors = [
    { label: 'ERPNext', detail: 'Inventory, orders & suppliers' },
    { label: 'Salesforce', detail: 'Leads, opportunities & pipeline' },
    { label: 'GrandNode', detail: 'E-commerce catalog & orders' },
    { label: 'CSV Upload', detail: 'Custom data exports' },
]

const pricingPlans = [
    {
        id: 'pilot',
        name: 'Pilot',
        price: '$0',
        cadence: '14-day guided trial',
        bullets: ['Full platform access', 'Connect your real data', 'Live onboarding session'],
        cta: 'Try the pilot',
    },
    {
        id: 'run',
        name: 'Run',
        price: '$79',
        cadence: 'per seat / month',
        bullets: ['Unlimited plans & evidence', '3 agents included', 'Email + chat support'],
        highlight: true,
        cta: 'Start Run plan',
    },
    {
        id: 'scale',
        name: 'Scale',
        price: 'Custom',
        cadence: 'annual',
        bullets: ['Dedicated success pod', 'Private data boundary', 'Outcome-based pricing'],
        cta: 'Talk to sales',
    },
]

const dataRequirements = [
    'Business profile (industry, team size)',
    'At least one data source (ERP, storefront, or CSV export)',
    'Owner approval for email/calendar automation (optional)',
]

export default function LandingPage() {
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()

    useEffect(() => {
        if (apiToken) navigate('/home', { replace: true })
    }, [apiToken, navigate])

    return (
        <div className="page-shell space-y-12">
            <section className="glass-panel--light grid gap-8 md:grid-cols-[1fr_0.8fr]">
                <div className="space-y-6">
                    <p className="eyebrow">Your business fitness coach</p>
                    <h1 className="text-4xl font-bold leading-tight text-gray-900 md:text-5xl">Set goals. Track progress. Achieve more.</h1>
                    <p className="text-lg text-gray-700">60‑second assessment → health score → weekly action plan. Motivation & celebration built in—no extra headcount.</p>
                    <ul className="space-y-2 text-sm text-gray-700">
                        {heroHighlights.map((item) => (
                            <li className="flex items-start gap-2" key={item}>
                                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand-500"></span>
                                {item}
                            </li>
                        ))}
                    </ul>
                    <div className="flex flex-col gap-3 sm:flex-row">
                        <Link className={`${primaryButton} w-full justify-center sm:w-auto`} to="/signup?plan=pilot">
                            Start free assessment
                        </Link>
                        <Link className={`${secondaryButton} w-full justify-center sm:w-auto`} to="#pricing">
                            See pricing
                        </Link>
                    </div>
                </div>
                <div className="glass-panel--accent space-y-6 text-center">
                    <div className="mx-auto inline-flex items-center gap-2 rounded-full bg-brand-500 px-4 py-2 text-sm font-semibold text-white shadow-brand-glow-sm">
                        <span className="relative flex h-2 w-2">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75"></span>
                            <span className="relative inline-flex h-2 w-2 rounded-full bg-white"></span>
                        </span>
                        Early Access
                    </div>
                    <div>
                        <h3 className="text-2xl font-bold text-gray-900">Join Growing SMBs</h3>
                        <p className="mt-3 text-gray-700">
                            Dyocense is your AI business coach designed specifically for small business owners who want to grow smarter, not just faster.
                        </p>
                    </div>
                    <div className="space-y-3 text-left">
                        <div className="flex items-start gap-3">
                            <span className="text-green-600 text-xl font-bold">✓</span>
                            <div>
                                <p className="font-semibold text-gray-900">Real-time health tracking</p>
                                <p className="text-sm text-gray-700">Monitor your business vitals like revenue, operations, and customer health</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-green-600 text-xl font-bold">✓</span>
                            <div>
                                <p className="font-semibold text-gray-900">AI-powered guidance</p>
                                <p className="text-sm text-gray-700">Get personalized weekly action plans based on your data</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <span className="text-green-600 text-xl font-bold">✓</span>
                            <div>
                                <p className="font-semibold text-gray-900">Built for busy owners</p>
                                <p className="text-sm text-gray-700">No complexity, no fluff—just actionable insights when you need them</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="glass-panel space-y-6" id="features">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <h2 className="text-3xl font-bold text-gray-900">Why owners choose Dyocense</h2>
                    <p className="text-gray-700">Like a fitness coach—but for your business performance.</p>
                </div>
                <div className="grid gap-5 md:grid-cols-3">
                    {benefitCards.map((benefit) => (
                        <div className="card-elevated flex h-full flex-col gap-3 p-6" key={benefit.title}>
                            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand text-2xl shadow-brand-glow-sm">{benefit.icon}</div>
                            <h3 className="text-xl font-semibold text-gray-900">{benefit.title}</h3>
                            <p className="text-sm text-gray-700">{benefit.copy}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="grid gap-6 md:grid-cols-2">
                <div className="glass-panel space-y-6">
                    <h2 className="text-3xl font-bold text-gray-900">How the journey works</h2>
                    <p className="text-gray-700">Simple 4‑step loop that compounds results week after week.</p>
                    <ol className="space-y-4 text-gray-700">
                        {journeySteps.map((step, index) => (
                            <li className="flex gap-4" key={step}>
                                <span className="text-brand-600 font-bold">{String(index + 1).padStart(2, '0')}</span>
                                <p>{step}</p>
                            </li>
                        ))}
                    </ol>
                </div>
                <div className="glass-panel space-y-4">
                    <p className="eyebrow">Plug in lightweight data signals</p>
                    <ul className="space-y-4 text-gray-700">
                        {connectors.map((connector) => (
                            <li className="flex flex-col" key={connector.label}>
                                <span className="text-base font-semibold text-gray-900">{connector.label}</span>
                                <span className="text-sm text-gray-600">{connector.detail}</span>
                            </li>
                        ))}
                    </ul>
                    <Link to="/connectors" className={`${primaryButton} w-full justify-center`}>
                        Browse connectors
                    </Link>
                </div>
            </section>

            <section className="glass-panel space-y-8" id="tools">
                <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div className="space-y-2">
                        <h2 className="text-4xl font-bold text-gray-900 leading-tight">Your coaching spaces</h2>
                        <p className="text-lg text-gray-600 max-w-2xl">Focused views for goals, weekly plan, health trends, and coach insights.</p>
                    </div>
                    <Link to="/tools" className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700 hover:gap-2 transition-all">
                        View all tools
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                    </Link>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                    {toolConfigs.map((tool) => (
                        <div className="card-elevated flex h-full flex-col gap-4 p-6 hover-lift" key={tool.key}>
                            <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-50 to-violet-50 px-3 py-1 w-fit">
                                <div className="h-1.5 w-1.5 rounded-full bg-brand-500"></div>
                                <p className="text-xs uppercase tracking-widest text-brand-700 font-bold">{tool.summary}</p>
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900 leading-tight">{tool.title}</h3>
                            <ul className="space-y-3 text-base text-gray-700 flex-1">
                                {tool.outcomes.slice(0, 3).map((item) => (
                                    <li className="flex items-start gap-3" key={item}>
                                        <svg className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="leading-relaxed">{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-auto flex flex-col gap-3 pt-4 border-t border-gray-100">
                                <Link className={`${primaryButton} w-full justify-center`} to={`/signup?tool=${tool.key}`}>
                                    {tool.cta}
                                </Link>
                                <Link className="text-center text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline inline-flex items-center justify-center gap-1" to={`/tools?tool=${tool.key}`}>
                                    See how it works
                                    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="glass-panel space-y-6" id="pricing">
                <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">Pricing that grows with your momentum</h2>
                        <p className="text-gray-700">Start free, prove value early, scale when weekly improvements are consistent.</p>
                    </div>
                    <p className="text-sm text-gray-600">Every plan includes onboarding specialists, templates, and compliance reviews.</p>
                </div>
                <div className="grid gap-5 md:grid-cols-3">
                    {pricingPlans.map((plan) => (
                        <div className={`card-elevated flex h-full flex-col gap-4 p-6 ${plan.highlight ? 'ring-2 ring-brand-400 shadow-brand-glow' : ''}`} key={plan.name}>
                            <h3 className="text-2xl font-semibold text-gray-900">{plan.name}</h3>
                            <p className="text-4xl font-bold text-gray-900">
                                {plan.price}
                                <span className="ml-2 text-base font-normal text-gray-600">{plan.cadence}</span>
                            </p>
                            <ul className="space-y-3 text-sm text-gray-700">
                                {plan.bullets.map((item) => (
                                    <li className="flex items-start gap-2" key={item}>
                                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand-500"></span>
                                        {item}
                                    </li>
                                ))}
                            </ul>
                            <Link
                                className={`${plan.highlight ? primaryButton : secondaryButton} w-full justify-center`}
                                to={`/signup?plan=${plan.id}`}
                            >
                                {plan.cta}
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            <section className="glass-panel space-y-6" id="trust">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">Data boundaries & controls</h2>
                        <p className="text-gray-700">We only ingest what fuels coaching. You define scopes & retention windows.</p>
                    </div>
                    <span className="rounded-full border border-brand-300 bg-brand-50 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-brand-700">
                        Zero customer PII
                    </span>
                </div>
                <p className="text-gray-700">
                    Dyocense only ingests the metadata needed to coordinate your work. You control scopes and retention.
                </p>
                <ul className="space-y-3 text-gray-700">
                    {dataRequirements.map((requirement) => (
                        <li className="flex gap-3" key={requirement}>
                            <span className="text-brand-500 font-bold">•</span>
                            {requirement}
                        </li>
                    ))}
                </ul>
                <p className="text-gray-700">Audit trails, role-based access, and redaction policies ship by default—no customer PII, ever.</p>
            </section>

            <section className="glass-panel--light text-center">
                <p className="eyebrow">Ready to start your assessment?</p>
                <h2 className="mt-4 text-3xl font-bold text-gray-900">Get your Business Health Score & first weekly plan</h2>
                <p className="mt-3 text-gray-700">60‑second assessment → health score → AI‑generated action plan. No credit card.</p>
                <div className="mt-6 flex flex-col items-center justify-center gap-4 sm:flex-row">
                    <Link className={`${primaryButton} w-full justify-center sm:w-auto`} to="/signup">
                        Start free assessment
                    </Link>
                    <Link className={`${secondaryButton} w-full justify-center sm:w-auto`} to="/contact">
                        Book a walkthrough
                    </Link>
                </div>
            </section>
        </div>
    )
}
