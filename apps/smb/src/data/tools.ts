export type ToolConfig = {
    key: string
    title: string
    summary: string
    outcomes: string[]
    inputs: string[]
    metrics: string[]
    route: string
    cta: string
}

export const toolConfigs: ToolConfig[] = [
    {
        key: 'connectors',
        title: 'Data Connectors',
        summary: 'Link POS, ERP, ecommerce, and spreadsheets so planners and agents use live data.',
        outcomes: ['CSV + Google Drive starters', 'Health checks + error badges', 'One-click testing'],
        inputs: ['Connector type', 'Credentials or shared folders', 'Sync cadence'],
        metrics: ['Connected sources count', 'Sync status', 'Last refresh timestamp'],
        route: '/connectors',
        cta: 'Open Connectors',
    },
    {
        key: 'copilot',
        title: 'Goals Copilot',
        summary: 'Fitness-style dashboard that tracks goals, connectors, and GenAI chat in one place.',
        outcomes: ['Template-driven coaching feed', 'Live connector + run status', 'Chat + data playground side-by-side'],
        inputs: ['Template selection', 'Connected data sources', 'Preferred coaching cadence'],
        metrics: ['Goal fitness score', 'Connector health', 'Sessions completed'],
        route: '/copilot',
        cta: 'Open Copilot',
    },
    {
        key: 'planner',
        title: 'AI Planner',
        summary: 'Turn a goal like “grow weekday lunch traffic” into a prioritized, cost-aware plan in under 5 minutes.',
        outcomes: ['Auto-generated milestones', 'Owner + due date assignments', 'Agent suggestions for next steps'],
        inputs: ['Business goal or KPI target', 'Time horizon', 'Constraints (budget, staff)'],
        metrics: ['Plan generated in 4 clicks', '30-day reminder cadence', 'What-if simulations ready'],
        route: '/planner',
        cta: 'Open Planner',
    },
    {
        key: 'agents',
        title: 'Automation Agents',
        summary: 'Conversational copilots that run playbooks, draft collateral, and sync data across tools.',
        outcomes: ['Chat + action cards UI', 'Pre-built restaurant, retail, ecommerce kits', 'Live status tracking'],
        inputs: ['Connected data sources', 'Team permissions', 'Preferred channels'],
        metrics: ['SLA alerts in chat', 'One-click approvals', 'Auto-generated summaries'],
        route: '/agents',
        cta: 'Meet the Agents',
    },
    {
        key: 'executor',
        title: 'Execution HUD',
        summary: 'Track progress, unblock owners, and log evidence without switching tabs.',
        outcomes: ['Daily digest via SMS/email', 'Evidence graph snapshots', 'Exception-based alerts'],
        inputs: ['Plan selection', 'Owners + collaborators', 'Preferred reminder cadence'],
        metrics: ['3 min status updates', 'Audit-ready exports', 'Escalations routed instantly'],
        route: '/executor',
        cta: 'Launch Execution',
    },
]
