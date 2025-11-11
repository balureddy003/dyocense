import { Badge, Card, Divider, Group, Paper, Stack, Table, Text, ThemeIcon, Title } from '@mantine/core'
import { IconAlertCircle, IconCheck, IconTrendingDown, IconTrendingUp } from '@tabler/icons-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface CoachMessageProps {
    content: string
    isUser: boolean
}

/**
 * Renders coach messages with professional report-style formatting
 * Supports markdown, tables, KPI cards, metrics, and visual elements
 */
export function CoachMessage({ content, isUser }: CoachMessageProps) {
    if (isUser) {
        return (
            <Text
                size="sm"
                style={{
                    whiteSpace: 'pre-wrap',
                    color: 'white',
                }}
            >
                {content}
            </Text>
        )
    }

    // Check if content contains table data (KPI format)
    const hasKPITable = content.includes('| KPI |') || content.includes('| Revenue') || content.includes('| Orders')

    if (hasKPITable) {
        return <KPIReportView content={content} />
    }

    // Render as rich markdown with professional styling
    return (
        <div style={{ color: '#1e293b' }}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h1: ({ children }) => (
                        <Title order={2} size="h3" mb="md" mt="lg" style={{ color: '#0f172a', borderBottom: '2px solid #0ea5e9', paddingBottom: '8px' }}>
                            {children}
                        </Title>
                    ),
                    h2: ({ children }) => (
                        <Title order={3} size="h4" mb="sm" mt="md" style={{ color: '#1e293b' }}>
                            {children}
                        </Title>
                    ),
                    h3: ({ children }) => (
                        <Text size="md" fw={700} mb="xs" mt="sm" style={{ color: '#334155' }}>
                            {children}
                        </Text>
                    ),
                    p: ({ children }) => (
                        <Text size="sm" mb="sm" style={{ color: '#475569', lineHeight: 1.6 }}>
                            {children}
                        </Text>
                    ),
                    ul: ({ children }) => (
                        <Stack gap="xs" mb="md" style={{ listStyle: 'none', padding: 0 }}>
                            {children}
                        </Stack>
                    ),
                    ol: ({ children }) => (
                        <Stack gap="xs" mb="md" component="ol" style={{ paddingLeft: '24px' }}>
                            {children}
                        </Stack>
                    ),
                    li: ({ children }) => (
                        <Group gap="sm" align="flex-start" wrap="nowrap">
                            <ThemeIcon size="xs" radius="xl" color="blue" variant="light" mt={4}>
                                <IconCheck size={10} />
                            </ThemeIcon>
                            <Text size="sm" style={{ color: '#334155', flex: 1 }}>
                                {children}
                            </Text>
                        </Group>
                    ),
                    table: ({ children }) => (
                        <Card withBorder radius="md" p={0} mb="md" style={{ overflow: 'hidden' }}>
                            <Table striped highlightOnHover>
                                {children}
                            </Table>
                        </Card>
                    ),
                    thead: ({ children }) => (
                        <thead style={{ backgroundColor: '#f8fafc' }}>
                            {children}
                        </thead>
                    ),
                    th: ({ children }) => (
                        <th style={{ padding: '12px 16px', fontWeight: 600, color: '#0f172a', fontSize: '13px' }}>
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td style={{ padding: '10px 16px', color: '#475569', fontSize: '13px' }}>
                            {children}
                        </td>
                    ),
                    blockquote: ({ children }) => (
                        <Paper p="md" mb="md" style={{ borderLeft: '4px solid #0ea5e9', backgroundColor: '#f0f9ff' }}>
                            <Text size="sm" style={{ color: '#0c4a6e', fontStyle: 'italic' }}>
                                {children}
                            </Text>
                        </Paper>
                    ),
                    hr: () => <Divider my="md" />,
                    strong: ({ children }) => (
                        <Text span fw={700} style={{ color: '#0f172a' }}>
                            {children}
                        </Text>
                    ),
                    em: ({ children }) => (
                        <Text span fs="italic" style={{ color: '#64748b' }}>
                            {children}
                        </Text>
                    ),
                    code: ({ children, className }) => {
                        const isInline = !className
                        if (isInline) {
                            return (
                                <Badge variant="light" size="sm" style={{ fontFamily: 'monospace', fontWeight: 400 }}>
                                    {children}
                                </Badge>
                            )
                        }
                        return (
                            <Paper p="md" mb="md" style={{ backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                <Text size="xs" style={{ fontFamily: 'monospace', color: '#334155', whiteSpace: 'pre-wrap' }}>
                                    {children}
                                </Text>
                            </Paper>
                        )
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    )
}

/**
 * Special component for KPI report view with metrics cards
 */
function KPIReportView({ content }: { content: string }) {
    // Extract KPI data from markdown table
    const lines = content.split('\n')
    const tableStart = lines.findIndex(line => line.includes('| KPI |') || line.includes('| Revenue'))

    if (tableStart === -1) {
        return <Text size="sm">{content}</Text>
    }

    // Extract introduction text before table
    const intro = lines.slice(0, tableStart).join('\n').trim()

    // Parse table rows
    const kpis: Array<{
        name: string
        value: string
        description: string
        trend?: 'up' | 'down'
        status?: 'good' | 'warning' | 'critical'
    }> = []

    for (let i = tableStart + 2; i < lines.length; i++) {
        const line = lines[i].trim()
        if (!line || !line.startsWith('|')) break

        const parts = line.split('|').map(p => p.trim()).filter(p => p)
        if (parts.length >= 3) {
            const name = parts[0].replace(/\*\*/g, '')
            const value = parts[1]
            const description = parts[2]

            // Determine trend from value
            let trend: 'up' | 'down' | undefined
            if (value.includes('$') && parseFloat(value.replace(/[$,]/g, '')) > 0) trend = 'up'

            // Determine status
            let status: 'good' | 'warning' | 'critical' | undefined
            if (name.toLowerCase().includes('revenue') && parseFloat(value.replace(/[$,]/g, '')) > 0) status = 'good'
            if (name.toLowerCase().includes('orders') && value === '0') status = 'critical'
            if (description.toLowerCase().includes('critical')) status = 'critical'
            if (description.toLowerCase().includes('indicates market')) status = 'good'

            kpis.push({ name, value, description, trend, status })
        }
    }

    return (
        <Stack gap="md">
            {/* Introduction */}
            {intro && (
                <Paper p="md" style={{ backgroundColor: '#f0f9ff', border: '1px solid #bae6fd' }}>
                    <Group gap="sm">
                        <ThemeIcon size="lg" radius="xl" variant="light" color="blue">
                            <IconAlertCircle size={20} />
                        </ThemeIcon>
                        <Text size="sm" fw={600} style={{ color: '#0c4a6e', flex: 1 }}>
                            {intro}
                        </Text>
                    </Group>
                </Paper>
            )}

            {/* KPI Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
                {kpis.map((kpi, idx) => (
                    <Card key={idx} withBorder radius="md" p="md" style={{
                        backgroundColor: 'white',
                        borderColor: kpi.status === 'critical' ? '#fee2e2' : kpi.status === 'warning' ? '#fef3c7' : '#e0f2fe'
                    }}>
                        <Stack gap="xs">
                            {/* KPI Name */}
                            <Group justify="space-between">
                                <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.5px' }}>
                                    {kpi.name}
                                </Text>
                                {kpi.trend && (
                                    <ThemeIcon
                                        size="sm"
                                        radius="xl"
                                        variant="light"
                                        color={kpi.trend === 'up' ? 'teal' : 'red'}
                                    >
                                        {kpi.trend === 'up' ? <IconTrendingUp size={12} /> : <IconTrendingDown size={12} />}
                                    </ThemeIcon>
                                )}
                            </Group>

                            {/* KPI Value */}
                            <Text size="xl" fw={700} style={{
                                color: kpi.status === 'critical' ? '#dc2626' : kpi.status === 'good' ? '#059669' : '#0f172a'
                            }}>
                                {kpi.value}
                            </Text>

                            {/* Description */}
                            <Text size="xs" c="dimmed" style={{ lineHeight: 1.4 }}>
                                {kpi.description}
                            </Text>

                            {/* Status Badge */}
                            {kpi.status && (
                                <Badge
                                    size="sm"
                                    variant="light"
                                    color={kpi.status === 'critical' ? 'red' : kpi.status === 'warning' ? 'yellow' : 'teal'}
                                >
                                    {kpi.status === 'critical' ? 'Needs Attention' : kpi.status === 'warning' ? 'Monitor' : 'Healthy'}
                                </Badge>
                            )}
                        </Stack>
                    </Card>
                ))}
            </div>

            {/* Additional context after KPIs */}
            {lines.slice(tableStart + kpis.length + 3).filter(l => l.trim()).length > 0 && (
                <Paper p="md" style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {lines.slice(tableStart + kpis.length + 3).join('\n')}
                    </ReactMarkdown>
                </Paper>
            )}
        </Stack>
    )
}
