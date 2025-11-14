import { Badge, Button, Card, Group, Stack, Text, TextInput, Title } from '@mantine/core'
import { IconPlus, IconRefresh, IconSearch } from '@tabler/icons-react'
import React, { useMemo, useState } from 'react'

type Connector = {
    id: string
    name: string
    type: string
    status: 'active' | 'inactive' | 'error' | 'syncing'
    lastSync?: string
}

export type ConnectorListProps = {
    connectors?: Connector[]
    onCreate?: () => void
    onSync?: (id: string) => void
}

const statusColor: Record<Connector['status'], string> = {
    active: 'green',
    inactive: 'gray',
    error: 'red',
    syncing: 'yellow',
}

export const ConnectorList: React.FC<ConnectorListProps> = ({ connectors, onCreate, onSync }) => {
    const [q, setQ] = useState('')
    const items = useMemo<Connector[]>(() => {
        if (connectors && connectors.length) return connectors
        // Fallback sample data until backend endpoints are live
        return [
            { id: 'qb', name: 'QuickBooks', type: 'accounting', status: 'active', lastSync: '2025-11-10T12:00:00Z' },
            { id: 'shopify', name: 'Shopify', type: 'commerce', status: 'inactive' },
            { id: 'stripe', name: 'Stripe', type: 'payments', status: 'error', lastSync: '2025-11-12T08:22:00Z' },
        ]
    }, [connectors])

    const filtered = items.filter((c) => (c.name + c.type).toLowerCase().includes(q.toLowerCase()))

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Title order={3}>Connectors</Title>
                <Group>
                    <TextInput leftSection={<IconSearch size={16} />} placeholder="Search connectors" value={q} onChange={(e) => setQ(e.currentTarget.value)} />
                    <Button leftSection={<IconPlus size={16} />} onClick={onCreate}>Add Connector</Button>
                </Group>
            </Group>

            <Stack>
                {filtered.map((c) => (
                    <Card withBorder key={c.id} radius="md">
                        <Group justify="space-between" align="center">
                            <div>
                                <Group>
                                    <Text fw={600}>{c.name}</Text>
                                    <Badge color="blue" variant="light">{c.type}</Badge>
                                </Group>
                                <Group gap="xs">
                                    <Badge color={statusColor[c.status]} variant="filled">{c.status}</Badge>
                                    {c.lastSync && (<Text size="xs" c="dimmed">Last sync: {new Date(c.lastSync).toLocaleString()}</Text>)}
                                </Group>
                            </div>
                            <Group>
                                <Button variant="light" leftSection={<IconRefresh size={16} />} onClick={() => onSync?.(c.id)}>Sync</Button>
                            </Group>
                        </Group>
                    </Card>
                ))}
                {filtered.length === 0 && (
                    <Card withBorder radius="md"><Text c="dimmed">No connectors found.</Text></Card>
                )}
            </Stack>
        </Stack>
    )
}

export default ConnectorList
