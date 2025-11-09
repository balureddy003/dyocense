type Props = {
    label: string
    description: string
    badge?: string
    cta?: string
    onSelect: () => void
}

export default function AgentActionCard({ label, description, badge, cta = 'Open', onSelect }: Props) {
    return (
        <div className="agent-card" onClick={onSelect}>
            <div className="agent-card__text">
                <div className="agent-card__title">
                    <span className="text-base font-semibold text-white">{label}</span>
                    {badge && <span className="agent-card__badge">{badge}</span>}
                </div>
                <p className="text-sm text-slate-300">{description}</p>
            </div>
            <button className="agent-card__cta" type="button">
                {cta}
            </button>
        </div>
    )
}
