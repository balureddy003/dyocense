import { Badge, Group, HoverCard, Stack, Text } from '@mantine/core'

interface DataSource {
    name: string
    icon: string
    lastSync: string
    recordCount: number
}

interface DataSourcesIndicatorProps {
    sources: DataSource[]
}

const sourceIcons: Record<string, string> = {
    stripe: '💳',
    quickbooks: '📒',
    'google-ads': '📢',
    shopify: '🛍️',
    salesforce: '☁️',
    hubspot: '🎯',
    default: '📊'
}

export default function DataSourcesIndicator({ sources }: DataSourcesIndicatorProps) {
    if (!sources || sources.length === 0) return null

    return (
        <Group gap={6} mt={8}>
            <Text size="10px" c="dimmed" fw={500} tt="uppercase">
                Data from:
            </Text>
            {sources.map((source, i) => (
                <HoverCard key={i} width={220} shadow="md" position="bottom">
                    <HoverCard.Target>
                        <Badge
                            size="sm"
                            variant="light"
                            color="gray"
                            leftSection={sourceIcons[source.icon.toLowerCase()] || sourceIcons.default}
                            styles={{
                                root: {
                                    cursor: 'pointer',
                                    fontSize: '11px',
                                    fontWeight: 500
                                }
                            }}
                        >
                            {source.name}
                        </Badge>
                    </HoverCard.Target>
                    <HoverCard.Dropdown>
                        <Stack gap={6}>
                            <Group justify="space-between">
                                <Text size="12px" fw={600}>{source.name}</Text>
                                <Text size="10px" c="green">✓ Connected</Text>
                            </Group>
                            <div style={{ height: 1, background: '#e5e7eb' }} />
                            <Group justify="space-between">
                                <Text size="11px" c="dimmed">Last synced:</Text>
                                <Text size="11px" fw={500}>{source.lastSync}</Text>
                            </Group>
                            <Group justify="space-between">
                                <Text size="11px" c="dimmed">Records:</Text>
                                <Text size="11px" fw={500}>{source.recordCount.toLocaleString()}</Text>
                            </Group>
                        </Stack>
                    </HoverCard.Dropdown>
                </HoverCard>
            ))}
        </Group>
    )
}
