import type { TenantConnector } from '../lib/api'

export type ToolDescriptor = {
    id: string
    label: string
    description?: string
    connector: string
}

export type PromptDescriptor = {
    id: string
    title: string
    text: string
    connector: string
}

// Maps connector_type -> tool and prompt generators
const registry: Record<string, {
    tools: () => ToolDescriptor[]
    prompts: () => PromptDescriptor[]
}> = {
    erpnext: {
        tools: () => ([
            { id: 'erp.stock', label: 'Check stock', description: 'Actual vs reserved per warehouse', connector: 'erpnext' },
            { id: 'erp.orders', label: 'Sales orders', description: 'Filter by status or customer', connector: 'erpnext' },
            { id: 'erp.posuppliers', label: 'Purchase orders', description: 'Replenishment planning', connector: 'erpnext' },
        ]),
        prompts: () => ([
            {
                id: 'erp.prompt.inventory_health',
                title: 'Inventory health check',
                text: 'Run an inventory health check: low stock, excess stock, discrepancies, and reorder suggestions.',
                connector: 'erpnext',
            },
            {
                id: 'erp.prompt.order_status',
                title: 'Customer order status',
                text: "Show open sales orders, pending deliveries, and invoice status for customer 'ACME'.",
                connector: 'erpnext',
            },
            {
                id: 'erp.prompt.low_stock_po',
                title: 'Build PO for low stock',
                text: 'Identify low stock items that need reordering and draft a purchase order with recommended quantities.',
                connector: 'erpnext',
            },
        ]),
    },
    csv_upload: {
        tools: () => ([
            { id: 'csv.query', label: 'Query CSV', description: 'Filter and select columns', connector: 'csv_upload' },
            { id: 'csv.analyze', label: 'Analyze CSV', description: 'Summary, missing values, uniques', connector: 'csv_upload' },
            { id: 'csv.aggregate', label: 'Aggregate CSV', description: 'Group by and metrics', connector: 'csv_upload' },
        ]),
        prompts: () => ([
            {
                id: 'csv.prompt.find_trends',
                title: 'Find sales trends',
                text: 'From the latest CSV, find top 5 products by revenue and month-over-month growth.',
                connector: 'csv_upload',
            },
            {
                id: 'csv.prompt.data_quality',
                title: 'Data quality scan',
                text: 'Scan the CSV for missing values, invalid types, and potential outliers; propose fixes.',
                connector: 'csv_upload',
            },
            {
                id: 'csv.prompt.segment_compare',
                title: 'Compare segments',
                text: 'Compare performance across customer segments (e.g., region) and summarize key differences.',
                connector: 'csv_upload',
            },
        ]),
    },
    'google-drive': {
        tools: () => ([
            { id: 'csv.query', label: 'Query Sheet (CSV)', description: 'Filter and select columns', connector: 'google-drive' },
            { id: 'csv.analyze', label: 'Analyze Sheet', description: 'Summary, missing values, uniques', connector: 'google-drive' },
        ]),
        prompts: () => ([
            {
                id: 'gdrive.prompt.sheet_summary',
                title: 'Summarize spreadsheet',
                text: 'Summarize key metrics and trends from the latest spreadsheet and list anomalies.',
                connector: 'google-drive',
            },
        ]),
    },
}

export function getTenantToolsAndPrompts(connectors: TenantConnector[] | undefined) {
    const active = (connectors || []).filter(c => c.status === 'active')
    const tools: ToolDescriptor[] = []
    const prompts: PromptDescriptor[] = []
    for (const c of active) {
        const entry = registry[c.connector_type]
        if (!entry) continue
        tools.push(...entry.tools())
        prompts.push(...entry.prompts())
    }
    // De-duplicate by id
    const byId = <T extends { id: string }>(arr: T[]) => Array.from(new Map(arr.map(i => [i.id, i])).values())
    return { tools: byId(tools), prompts: byId(prompts) }
}
