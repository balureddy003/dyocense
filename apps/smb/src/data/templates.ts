export type TemplateGoal = {
    id: string
    title: string
    description: string
    metricLabel: string
    target: string
    status: 'on_track' | 'at_risk' | 'not_started'
}

export type TemplateSession = {
    id: string
    title: string
    duration: string
    description: string
    cta: string
}

export type TemplateConnector = {
    id: string
    name: string
    description: string
    status: 'connected' | 'required' | 'optional'
}

export type TemplatePrompts = {
    home: string[]
    planner: string[]
    agents: string[]
    executor: string[]
    copilot: string[]
}

export type BusinessTemplate = {
    id: string
    name: string
    industry: string
    summary: string
    archetypeId: string
    prompts: TemplatePrompts
    goals: TemplateGoal[]
    sessions: TemplateSession[]
    connectors: TemplateConnector[]
}

export const templates: BusinessTemplate[] = [
    {
        id: 'restaurant',
        name: 'Neighborhood Restaurant',
        industry: 'Restaurant',
        summary: 'Increase covers, reduce waste, and keep the kitchen staffed.',
        archetypeId: 'inventory_basic',
        prompts: {
            home: [
                'How can I boost weekday lunch traffic?',
                'Help me reduce prep waste this week.',
                'Draft a schedule tweak for the weekend rush.',
            ],
            planner: [
                'Break the lunch traffic goal into daily actions.',
                'Rewrite the prep waste milestone for this week.',
                'Highlight which stations cause most overtime.',
            ],
            agents: [
                'Launch the lunch promo agent for next week.',
                'Draft an SMS to VIP guests about a chef special.',
                'Schedule a nightly waste audit with the agents.',
            ],
            executor: [
                'Explain today’s run for the kitchen crew.',
                'List blockers the agents spotted this morning.',
                'Write a digest owners can read in 60 seconds.',
            ],
            copilot: [
                'What should the team focus on this week?',
                'How close are we to cutting waste by 25%?',
                'Suggest two quick-win sessions for the staff.',
            ],
        },
        goals: [
            {
                id: 'goal-traffic',
                title: 'Lunch Traffic Boost',
                description: 'Add 20 more covers Monday–Friday.',
                metricLabel: 'Covers/day',
                target: '+20',
                status: 'at_risk',
            },
            {
                id: 'goal-waste',
                title: 'Reduce Kitchen Waste',
                description: 'Cut produce spoilage by 25%.',
                metricLabel: 'Spoilage',
                target: '-25%',
                status: 'on_track',
            },
            {
                id: 'goal-staff',
                title: 'Staff Efficiency',
                description: 'Lower overtime to <5% of hours.',
                metricLabel: 'OT hours',
                target: '<5%',
                status: 'not_started',
            },
        ],
        sessions: [
            {
                id: 'session-prep',
                title: 'Prep Waste Audit',
                duration: '15 min',
                description: 'Review prep sheets + POS to spot over-portioning.',
                cta: 'Start audit',
            },
            {
                id: 'session-lunch-promo',
                title: 'Weekday Lunch Promo',
                duration: '10 min',
                description: 'Launch SMS/email offer to locals.',
                cta: 'Launch offer',
            },
        ],
        connectors: [
            { id: 'pos', name: 'Point of Sale', description: 'Sales + covers feed', status: 'connected' },
            { id: 'inventory', name: 'Inventory/ERPNext', description: 'Stock + waste data', status: 'required' },
            { id: 'scheduling', name: 'Staff Scheduling', description: 'Labor + overtime', status: 'optional' },
        ],
    },
    {
        id: 'retail',
        name: 'Boutique Retailer',
        industry: 'Retail',
        summary: 'Balance stock, promos, and staffing.',
        archetypeId: 'retail_promo',
        prompts: {
            home: [
                'What items should we markdown this week?',
                'Help me plan a weekend pop-up.',
                'Who needs to be on the floor Saturday?',
            ],
            planner: [
                'Lay out a plan to keep popular SKUs in stock.',
                'What promotion cadence should we run this month?',
                'Reassign owners for the merch refresh tasks.',
            ],
            agents: [
                'Launch the pop-up playbook for Saturday.',
                'Draft a text campaign for loyalty shoppers.',
                'Sync staffing updates to the shared calendar.',
            ],
            executor: [
                'Give me a status line my floor managers can use.',
                'What blockers are slowing the promo plan?',
                'Create a digest for the store owner.',
            ],
            copilot: [
                'Which goal moves the needle fastest this week?',
                'How do we prevent stockouts before the weekend?',
                'Recommend two coaching sessions for the team.',
            ],
        },
        goals: [
            {
                id: 'goal-stockouts',
                title: 'Prevent Stockouts',
                description: 'Keep popular SKUs in stock 98% of the time.',
                metricLabel: 'In stock',
                target: '98%',
                status: 'on_track',
            },
            {
                id: 'goal-margin',
                title: 'Improve Gross Margin',
                description: 'Raise margin by 5 pts with smarter promos.',
                metricLabel: 'Margin',
                target: '+5 pts',
                status: 'at_risk',
            },
        ],
        sessions: [
            {
                id: 'session-merch',
                title: 'Merchandising refresh',
                duration: '20 min',
                description: 'AI suggests display tweaks + promo pairings.',
                cta: 'Review plan',
            },
            {
                id: 'session-pop-up',
                title: 'Pop-up checklist',
                duration: '12 min',
                description: 'Staffing, promos, and supplies for an event.',
                cta: 'Open checklist',
            },
        ],
        connectors: [
            { id: 'pos', name: 'Point of Sale', description: 'Sales + promos', status: 'connected' },
            { id: 'erp', name: 'ERP/Inventory', description: 'Stock + lead times', status: 'required' },
        ],
    },
    {
        id: 'erpnext_ecom',
        name: 'ERP-driven E-commerce',
        industry: 'E-commerce',
        summary: 'Optimize conversion, attachments, and fulfillment when an ERP such as ERPNext or Odoo powers orders + inventory.',
        archetypeId: 'inventory_basic',
        prompts: {
            home: [
                'How do we lift attachment rate on accessory bundles?',
                'Are fulfillment times slipping in peak season?',
                'Which upsell should we pitch after the base product?',
            ],
            planner: [
                'Lay out a sprint to keep ERP fulfillment under two days.',
                'Rewrite the replacement parts goal into weekly jobs.',
                'Show steps to reduce cart abandonment for add-ons.',
            ],
            agents: [
                'Launch the fulfillment pulse agent using ERP data.',
                'Ask the bundle optimizer to suggest a promo set.',
                'Have the parts forecaster project demand for spares.',
            ],
            executor: [
                'Explain the latest ERP fulfillment run for ops.',
                'Summarize risk on accessory conversion this week.',
                'Draft a digest for leadership.',
            ],
            copilot: [
                'Where are we pacing on attachment rates?',
                'What data should we pull from ERPNext for next week’s sprint?',
                'Recommend a quick coaching session for fulfillment.',
            ],
        },
        goals: [
            {
                id: 'goal-attach',
                title: 'Accessory Attachment',
                description: 'Reach a healthy attachment rate on accessory bundles.',
                metricLabel: 'Attachment',
                target: '35%',
                status: 'at_risk',
            },
            {
                id: 'goal-ship',
                title: 'Fulfillment Pulse',
                description: 'Keep ERP-driven ship times under 2 days.',
                metricLabel: 'Ship time',
                target: '<2 days',
                status: 'on_track',
            },
            {
                id: 'goal-parts',
                title: 'Replacement Parts Coverage',
                description: 'Stay above 28 days of coverage for top spare parts.',
                metricLabel: 'Coverage',
                target: '28 days+',
                status: 'not_started',
            },
        ],
        sessions: [
            {
                id: 'session-bundle',
                title: 'Accessory bundle audit',
                duration: '10 min',
                description: 'Use ERP order data to see which kits underperform.',
                cta: 'Run audit',
            },
            {
                id: 'session-fulfillment',
                title: 'Fulfillment pulse',
                duration: '8 min',
                description: 'Spot where ship times slip and who owns the fix.',
                cta: 'Check pulse',
            },
            {
                id: 'session-parts',
                title: 'Replacement parts forecast',
                duration: '12 min',
                description: 'Project spare-part demand before the next rush.',
                cta: 'Forecast parts',
            },
        ],
        connectors: [
            { id: 'erpnext', name: 'ERPNext / ERP', description: 'Orders + inventory data', status: 'connected' },
            { id: 'shopify', name: 'Shopify', description: 'Storefront + carts', status: 'optional' },
            { id: 'grandnode', name: 'GrandNode', description: 'Ecommerce catalog + orders', status: 'optional' },
            { id: 'csv_upload', name: 'Sales CSV Upload', description: 'Ad-hoc exports for experiments', status: 'optional' },
            { id: 'google-drive', name: 'Google Drive', description: 'Planning sheets + trackers', status: 'required' },
        ],
    },
]
