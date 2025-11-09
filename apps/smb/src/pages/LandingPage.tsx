import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toolConfigs } from '../data/tools'
import { primaryButton, secondaryButton } from '../lib/theme'
import { useAuthStore } from '../stores/auth'

const heroHighlights = [
    'Copilots tuned for owner-operators',
    'No extra headcount or spreadsheets',
    'Works with ERPNext, Shopify, GrandNode, CSV',
]

const benefitCards = [
    {
        title: 'Plan faster',
        copy: 'Point Dyocense at your goals and it drafts explainable milestones, risks, and owner-ready briefs.',
        icon: '⚡',
    },
    {
        title: 'Automate follow-ups',
        copy: 'Assign agents to send updates, QA deliverables, and sync status without chasing your team.',
        icon: '🤝',
    },
    {
        title: 'Prove impact',
        copy: 'Every run logs evidence so exporting an audit or investor update is a single click.',
        icon: '📈',
    },
]

const journeySteps = [
    'Pick a workspace template for retail, services, or ecommerce.',
    'Connect a data source (ERP, storefront, or start with the guided pilot).',
    'Let Dyocense copilots plan, execute, and report with you.',
]

const connectors = [
    { label: 'ERPNext / Odoo', detail: 'Orders + inventory truth' },
    { label: 'Shopify', detail: 'Carts, promos, and customers' },
    { label: 'GrandNode', detail: 'B2B catalog + subscriptions' },
    { label: 'CSV & Google Drive', detail: 'Exports, trackers, forecasts' },
]

const testimonials = [
    {
        quote: 'We launched three promos without hiring ops. Plans, agents, and evidence are ready the moment I log in.',
        author: 'Priya Patel · Owner, UrbanSprout Market',
    },
    {
        quote: 'Dyocense keeps our ERP data and action items in sync. The copilot feels like another teammate.',
        author: 'Leo Santos · COO, RallyParts',
    },
]

const proofPoints = [
    { label: 'SMBs launched', value: '420+' },
    { label: 'Avg. hours saved / week', value: '18' },
    { label: 'Agent coverage', value: '63%' },
]

const pricingPlans = [
    {
        name: 'Pilot',
        price: '$0',
        cadence: '14-day guided trial',
        bullets: ['Sample data + sandbox', 'Planner + Copilot access', 'Live onboarding session'],
        cta: 'Try the pilot',
    },
    {
        name: 'Run',
        price: '$79',
        cadence: 'per seat / month',
        bullets: ['Unlimited plans & evidence', '3 agents included', 'Email + chat support'],
        highlight: true,
        cta: 'Start Run plan',
    },
    {
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
            <section className="glass-panel--light grid gap-8 text-slate-900 md:grid-cols-[1fr_0.8fr]">
                <div className="space-y-6">
                    <p className="eyebrow text-brand-400">GenAI workspace for SMB owners</p>
                    <h1 className="text-4xl font-semibold leading-tight md:text-5xl">Plan, launch, and prove impact without adding headcount</h1>
                    <p className="text-lg text-slate-600">Dyocense is the AI operations desk for lean teams. Plug in your data, invite your crew, and a copilot keeps every plan, agent, and report moving.</p>
                    <ul className="space-y-2 text-sm text-slate-600">
                        {heroHighlights.map((item) => (
                            <li className="flex items-start gap-2" key={item}>
                                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand"></span>
                                {item}
                            </li>
                        ))}
                    </ul>
                    <div className="flex flex-col gap-3 sm:flex-row">
                        <Link className={`${primaryButton} w-full justify-center sm:w-auto`} to="/signup">
                            Start pilot in minutes
                        </Link>
                        <Link className={`${secondaryButton} w-full justify-center sm:w-auto`} to="/contact">
                            See pricing with an advisor
                        </Link>
                    </div>
                </div>
                <div className="glass-panel space-y-6">
                    <div>
                        <p className="eyebrow text-slate-300">SMB impact snapshot</p>
                        <div className="mt-4 grid gap-4 sm:grid-cols-2">
                            {proofPoints.map((point) => (
                                <div key={point.label}>
                                    <p className="text-3xl font-semibold text-white">{point.value}</p>
                                    <p className="text-sm text-slate-200">{point.label}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="rounded-2xl border border-white/15 bg-black/20 p-5">
                        <p className="text-sm font-semibold text-white">Owners report</p>
                        <p className="mt-2 text-2xl font-semibold text-brand">3× faster launch cycles</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.3em] text-slate-200">Based on cross-industry pilot data</p>
                    </div>
                </div>
            </section>

            <section className="glass-panel space-y-6" id="features">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <h2 className="text-3xl font-semibold">Why owners choose Dyocense</h2>
                    <p className="text-slate-100">Everything you need to launch work with confidence.</p>
                </div>
                <div className="grid gap-5 md:grid-cols-3">
                    {benefitCards.map((benefit) => (
                        <div className="flex h-full flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" key={benefit.title}>
                            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 text-2xl">{benefit.icon}</div>
                            <h3 className="text-xl font-semibold text-white">{benefit.title}</h3>
                            <p className="text-sm text-slate-100">{benefit.copy}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="grid gap-6 md:grid-cols-2">
                <div className="glass-panel space-y-6">
                    <h2 className="text-3xl font-semibold">Built for small teams</h2>
                    <p className="text-slate-100">You don’t need a RevOps army. Follow the three-step playbook.</p>
                    <ol className="space-y-4 text-slate-100">
                        {journeySteps.map((step, index) => (
                            <li className="flex gap-4" key={step}>
                                <span className="text-brand font-semibold">{String(index + 1).padStart(2, '0')}</span>
                                <p>{step}</p>
                            </li>
                        ))}
                    </ol>
                </div>
                <div className="glass-panel space-y-4">
                    <p className="eyebrow text-brand-200">Connect what you already use</p>
                    <ul className="space-y-4 text-slate-100">
                        {connectors.map((connector) => (
                            <li className="flex flex-col" key={connector.label}>
                                <span className="text-base font-semibold text-white">{connector.label}</span>
                                <span className="text-sm text-slate-300">{connector.detail}</span>
                            </li>
                        ))}
                    </ul>
                    <Link to="/connectors" className={`${primaryButton} w-full justify-center`}>
                        Browse connectors
                    </Link>
                </div>
            </section>

            <section className="glass-panel space-y-6" id="tools">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h2 className="text-3xl font-semibold">Pick the cockpit that fits today’s job</h2>
                        <p className="text-slate-100">Copilots for planning, automation, and evidence—all powered by the same kernel.</p>
                    </div>
                    <Link to="/tools" className="text-sm font-semibold text-brand hover:underline">
                        View all tools →
                    </Link>
                </div>
                <div className="grid gap-5 md:grid-cols-3">
                    {toolConfigs.map((tool) => (
                        <div className="glass-panel flex h-full flex-col gap-3 p-6" key={tool.key}>
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-200">{tool.summary}</p>
                            <h3 className="text-2xl font-semibold text-white">{tool.title}</h3>
                            <ul className="space-y-2 text-sm text-slate-100">
                                {tool.outcomes.slice(0, 3).map((item) => (
                                    <li className="flex items-start gap-2" key={item}>
                                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand"></span>
                                        {item}
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-auto flex flex-col gap-3">
                                <Link className={`${primaryButton} w-full justify-center`} to={`/signup?tool=${tool.key}`}>
                                    {tool.cta}
                                </Link>
                                <Link className="text-center text-sm font-semibold text-brand hover:underline" to={`/tools?tool=${tool.key}`}>
                                    See how it works →
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="glass-panel space-y-6" id="pricing">
                <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div>
                        <h2 className="text-3xl font-semibold">Pricing for growing operators</h2>
                        <p className="text-slate-100">Predictable seats with flexible automation allowances.</p>
                    </div>
                    <p className="text-sm text-slate-200">Every plan includes onboarding specialists, templates, and compliance reviews.</p>
                </div>
                <div className="grid gap-5 md:grid-cols-3">
                    {pricingPlans.map((plan) => (
                        <div className={`glass-panel flex h-full flex-col gap-4 p-6 ${plan.highlight ? 'ring-2 ring-brand/40' : ''}`} key={plan.name}>
                            <h3 className="text-2xl font-semibold text-white">{plan.name}</h3>
                            <p className="text-4xl font-semibold text-white">
                                {plan.price}
                                <span className="ml-2 text-base font-normal text-slate-300">{plan.cadence}</span>
                            </p>
                            <ul className="space-y-3 text-sm text-slate-100">
                                {plan.bullets.map((item) => (
                                    <li className="flex items-start gap-2" key={item}>
                                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand"></span>
                                        {item}
                                    </li>
                                ))}
                            </ul>
                            <Link className={`${plan.highlight ? primaryButton : secondaryButton} w-full justify-center`} to={plan.name === 'Pilot' ? '/signup' : '/contact'}>
                                {plan.cta}
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            <section className="glass-panel space-y-6" id="trust">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h2 className="text-3xl font-semibold">Data requirements & controls</h2>
                        <p className="text-slate-100">You decide what Dyocense ingests—and how long we keep it.</p>
                    </div>
                    <span className="rounded-full border border-white/30 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-white">
                        Zero customer PII
                    </span>
                </div>
                <p className="text-slate-100">
                    Dyocense only ingests the metadata needed to coordinate your work. You control scopes and retention.
                </p>
                <ul className="space-y-3 text-slate-100">
                    {dataRequirements.map((requirement) => (
                        <li className="flex gap-3" key={requirement}>
                            <span className="text-brand">•</span>
                            {requirement}
                        </li>
                    ))}
                </ul>
                <p className="text-slate-100">Audit trails, role-based access, and redaction policies ship by default so compliance receives a finished package.</p>
            </section>

            <section className="glass-panel--light text-center">
                <p className="text-sm uppercase tracking-[0.3em] text-brand">Ready to launch?</p>
                <h2 className="mt-4 text-3xl font-semibold text-slate-900">Pilot Dyocense with your team this week</h2>
                <p className="mt-3 text-slate-600">Invite your crew, connect a data source, and watch the copilot run your first plan.</p>
                <div className="mt-6 flex flex-col items-center justify-center gap-4 sm:flex-row">
                    <Link className={`${primaryButton} w-full justify-center sm:w-auto`} to="/signup">
                        Start free pilot
                    </Link>
                    <Link className={`${secondaryButton} w-full justify-center sm:w-auto`} to="/contact">
                        Book a walkthrough
                    </Link>
                </div>
            </section>
        </div>
    )
}
