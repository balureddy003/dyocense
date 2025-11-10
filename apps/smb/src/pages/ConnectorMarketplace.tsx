import {
    Badge,
    Box,
    Button,
    Card,
    Container,
    Divider,
    Grid,
    Group,
    Loader,
    Modal,
    Paper,
    SegmentedControl,
    Stack,
    Tabs,
    Text,
    TextInput,
    Title,
    Tooltip,
} from '@mantine/core'
import {
    IconCheck,
    IconCircleCheck,
    IconClock,
    IconCloud,
    IconDatabase,
    IconKey,
    IconPlug,
    IconSearch,
    IconShoppingBag,
    IconShoppingCart,
    IconSparkles,
    IconStar,
    IconTrendingUp,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { get } from '../lib/api'
import { useAuthStore } from '../stores/auth'

interface Connector {
    id: string
    name: string
    displayName: string
    category: string
    description: string
    icon: string
    dataTypes: string[]
    authType: string
    tier: 'free' | 'standard' | 'premium' | 'enterprise'
    popular: boolean
    verified: boolean
    region: string
    documentationUrl?: string
    setupComplexity: string
    syncRealtime: boolean
    features: string[]
    limitations: string[]
    configFields: any[]
}

interface MarketplaceResponse {
    connectors: Connector[]
    total: number
    categories: string[]
    tiers: string[]
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    ecommerce: <IconShoppingCart size={20} />,
    finance: <IconTrendingUp size={20} />,
    crm: <IconDatabase size={20} />,
    erp: <IconDatabase size={20} />,
    pos: <IconShoppingBag size={20} />,
    storage: <IconCloud size={20} />,
    payments: <IconKey size={20} />,
}

const TIER_COLORS: Record<string, string> = {
    free: 'green',
    standard: 'blue',
    premium: 'violet',
    enterprise: 'orange',
}

export default function ConnectorMarketplace() {
    const apiToken = useAuthStore((s) => s.apiToken)
    const [selectedCategory, setSelectedCategory] = useState('all')
    const [selectedTier, setSelectedTier] = useState('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null)
    const [detailsOpen, setDetailsOpen] = useState(false)

    // Fetch marketplace connectors
    const { data: marketplace, isLoading } = useQuery<MarketplaceResponse>({
        queryKey: ['marketplace', selectedCategory, selectedTier, searchQuery],
        queryFn: async () => {
            const params = new URLSearchParams()
            if (selectedCategory !== 'all') params.append('category', selectedCategory)
            if (selectedTier !== 'all') params.append('tier', selectedTier)
            if (searchQuery) params.append('search', searchQuery)

            return await get(`/v1/marketplace/connectors?${params.toString()}`, apiToken)
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    })

    // Fetch connected connectors
    const tenantId = useAuthStore((s) => s.tenantId)
    const { data: connected } = useQuery({
        queryKey: ['connected-connectors', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/connectors/connected`, apiToken),
        enabled: !!tenantId,
    })

    const handleConnectorClick = (connector: Connector) => {
        setSelectedConnector(connector)
        setDetailsOpen(true)
    }

    const connectors = marketplace?.connectors || []
    const popularConnectors = connectors.filter((c) => c.popular)

    return (
        <Container size="xl" py="xl">
            {/* Header */}
            <Stack gap="md" mb="xl">
                <Group justify="space-between">
                    <div>
                        <Group gap="xs">
                            <IconPlug size={32} />
                            <Title order={1}>Connector Marketplace</Title>
                        </Group>
                        <Text c="dimmed" mt="xs">
                            Connect your business tools and unlock data-driven insights
                        </Text>
                    </div>
                    <Group>
                        <Badge size="lg" variant="light" color="blue">
                            {marketplace?.total || 0} Available
                        </Badge>
                        <Badge size="lg" variant="filled" color="green">
                            {connected?.total || 0} Connected
                        </Badge>
                    </Group>
                </Group>

                {/* Search and Filters */}
                <Paper p="md" withBorder>
                    <Stack gap="md">
                        <TextInput
                            placeholder="Search connectors..."
                            leftSection={<IconSearch size={16} />}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            size="md"
                        />
                        <Group gap="md">
                            <SegmentedControl
                                value={selectedCategory}
                                onChange={(value) => setSelectedCategory(value)}
                                data={[
                                    { label: 'All', value: 'all' },
                                    { label: 'E-commerce', value: 'ecommerce' },
                                    { label: 'Finance', value: 'finance' },
                                    { label: 'CRM', value: 'crm' },
                                    { label: 'ERP', value: 'erp' },
                                    { label: 'POS', value: 'pos' },
                                    { label: 'Storage', value: 'storage' },
                                ]}
                            />
                            <SegmentedControl
                                value={selectedTier}
                                onChange={(value) => setSelectedTier(value)}
                                data={[
                                    { label: 'All Tiers', value: 'all' },
                                    { label: 'Free', value: 'free' },
                                    { label: 'Standard', value: 'standard' },
                                    { label: 'Premium', value: 'premium' },
                                    { label: 'Enterprise', value: 'enterprise' },
                                ]}
                            />
                        </Group>
                    </Stack>
                </Paper>
            </Stack>

            {isLoading ? (
                <Group justify="center" py="xl">
                    <Loader size="lg" />
                </Group>
            ) : (
                <Tabs defaultValue="all">
                    <Tabs.List>
                        <Tabs.Tab value="all" leftSection={<IconSparkles size={16} />}>
                            All Connectors ({connectors.length})
                        </Tabs.Tab>
                        <Tabs.Tab value="popular" leftSection={<IconStar size={16} />}>
                            Popular ({popularConnectors.length})
                        </Tabs.Tab>
                        <Tabs.Tab value="connected" leftSection={<IconCircleCheck size={16} />}>
                            Connected ({connected?.total || 0})
                        </Tabs.Tab>
                    </Tabs.List>

                    <Box mt="xl">
                        <Tabs.Panel value="all">
                            <ConnectorGrid connectors={connectors} onSelect={handleConnectorClick} />
                        </Tabs.Panel>

                        <Tabs.Panel value="popular">
                            <ConnectorGrid connectors={popularConnectors} onSelect={handleConnectorClick} />
                        </Tabs.Panel>

                        <Tabs.Panel value="connected">
                            {connected?.total === 0 ? (
                                <Paper p="xl" withBorder>
                                    <Stack align="center" gap="md">
                                        <IconPlug size={48} style={{ opacity: 0.3 }} />
                                        <Text c="dimmed">No connectors connected yet</Text>
                                        <Button onClick={() => setSelectedCategory('all')}>
                                            Browse Marketplace
                                        </Button>
                                    </Stack>
                                </Paper>
                            ) : (
                                <ConnectorGrid connectors={connected?.connectors || []} onSelect={handleConnectorClick} />
                            )}
                        </Tabs.Panel>
                    </Box>
                </Tabs>
            )}

            {/* Connector Details Modal */}
            <Modal
                opened={detailsOpen}
                onClose={() => setDetailsOpen(false)}
                title={
                    <Group gap="sm">
                        {selectedConnector && CATEGORY_ICONS[selectedConnector.category]}
                        <Text fw={600}>{selectedConnector?.displayName}</Text>
                        {selectedConnector?.verified && (
                            <Badge size="sm" color="blue" variant="light" leftSection={<IconCheck size={12} />}>
                                Verified
                            </Badge>
                        )}
                    </Group>
                }
                size="lg"
            >
                {selectedConnector && <ConnectorDetails connector={selectedConnector} />}
            </Modal>
        </Container>
    )
}

function ConnectorGrid({ connectors, onSelect }: { connectors: Connector[]; onSelect: (c: Connector) => void }) {
    if (connectors.length === 0) {
        return (
            <Paper p="xl" withBorder>
                <Stack align="center" gap="md">
                    <IconSearch size={48} style={{ opacity: 0.3 }} />
                    <Text c="dimmed">No connectors found</Text>
                </Stack>
            </Paper>
        )
    }

    return (
        <Grid>
            {connectors.map((connector) => (
                <Grid.Col key={connector.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
                    <ConnectorCard connector={connector} onClick={() => onSelect(connector)} />
                </Grid.Col>
            ))}
        </Grid>
    )
}

function ConnectorCard({ connector, onClick }: { connector: Connector; onClick: () => void }) {
    return (
        <Card
            shadow="sm"
            padding="lg"
            radius="md"
            withBorder
            style={{ cursor: 'pointer', height: '100%' }}
            onClick={onClick}
        >
            <Stack gap="md" h="100%">
                <Group justify="space-between">
                    <Box>
                        {CATEGORY_ICONS[connector.category] || <IconDatabase size={24} />}
                    </Box>
                    <Group gap={4}>
                        {connector.popular && (
                            <Tooltip label="Popular">
                                <IconStar size={16} style={{ color: 'var(--mantine-color-yellow-6)' }} />
                            </Tooltip>
                        )}
                        {connector.verified && (
                            <Tooltip label="Verified">
                                <IconCheck size={16} style={{ color: 'var(--mantine-color-blue-6)' }} />
                            </Tooltip>
                        )}
                    </Group>
                </Group>

                <Stack gap="xs" style={{ flex: 1 }}>
                    <Text fw={600} size="lg">
                        {connector.displayName}
                    </Text>
                    <Text size="sm" c="dimmed" lineClamp={2}>
                        {connector.description}
                    </Text>
                </Stack>

                <Stack gap="xs">
                    <Group gap="xs">
                        <Badge size="xs" color={TIER_COLORS[connector.tier]} variant="light">
                            {connector.tier}
                        </Badge>
                        <Badge size="xs" variant="outline">
                            {connector.category}
                        </Badge>
                        {connector.syncRealtime && (
                            <Badge size="xs" color="teal" variant="light" leftSection={<IconClock size={10} />}>
                                Real-time
                            </Badge>
                        )}
                    </Group>
                    <Text size="xs" c="dimmed">
                        {connector.dataTypes.slice(0, 3).join(', ')}
                        {connector.dataTypes.length > 3 && ` +${connector.dataTypes.length - 3}`}
                    </Text>
                </Stack>
            </Stack>
        </Card>
    )
}

function ConnectorDetails({ connector }: { connector: Connector }) {
    return (
        <Stack gap="md">
            <Text size="sm">{connector.description}</Text>

            <Divider />

            <div>
                <Text size="sm" fw={600} mb="xs">
                    Features
                </Text>
                <Stack gap="xs">
                    {connector.features.map((feature, idx) => (
                        <Group key={idx} gap="xs">
                            <IconCheck size={16} style={{ color: 'var(--mantine-color-green-6)' }} />
                            <Text size="sm">{feature}</Text>
                        </Group>
                    ))}
                </Stack>
            </div>

            {connector.limitations.length > 0 && (
                <>
                    <Divider />
                    <div>
                        <Text size="sm" fw={600} mb="xs">
                            Limitations
                        </Text>
                        <Stack gap="xs">
                            {connector.limitations.map((limitation, idx) => (
                                <Text key={idx} size="sm" c="dimmed">
                                    • {limitation}
                                </Text>
                            ))}
                        </Stack>
                    </div>
                </>
            )}

            <Divider />

            <Group justify="space-between">
                <Stack gap={4}>
                    <Text size="xs" c="dimmed">
                        Region
                    </Text>
                    <Text size="sm">{connector.region}</Text>
                </Stack>
                <Stack gap={4}>
                    <Text size="xs" c="dimmed">
                        Setup Complexity
                    </Text>
                    <Badge size="sm">{connector.setupComplexity}</Badge>
                </Stack>
                <Stack gap={4}>
                    <Text size="xs" c="dimmed">
                        Auth Type
                    </Text>
                    <Badge size="sm" variant="outline">
                        {connector.authType}
                    </Badge>
                </Stack>
            </Group>

            <Button fullWidth size="md" mt="md">
                Connect {connector.displayName}
            </Button>

            {connector.documentationUrl && (
                <Button variant="subtle" component="a" href={connector.documentationUrl} target="_blank">
                    View Documentation
                </Button>
            )}
        </Stack>
    )
}
