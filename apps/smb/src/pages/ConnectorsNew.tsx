import {
    ActionIcon,
    Badge,
    Button,
    Card,
    Grid,
    Group,
    Loader,
    Modal,
    ScrollArea,
    Stack,
    Tabs,
    Text,
    TextInput,
    Textarea,
    Title
} from '@mantine/core'
import { showNotification } from '@mantine/notifications'
import { IconCheck, IconPlug, IconRefresh, IconSearch, IconTrash, IconX } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { del, get, post } from '../lib/api'
import { useAuthStore } from '../stores/auth'

// Types
type ConnectorCategory = 'ecommerce' | 'finance' | 'crm' | 'erp' | 'inventory' | 'analytics' | 'marketing' | 'storage' | 'pos' | 'all'

interface MarketplaceConnector {
    id: string
    name: string
    display_name: string
    category: ConnectorCategory
    description: string
    icon: string
    data_types: string[]
    auth_type: string
    tier: string
    popular: boolean
    verified: boolean
    setup_complexity: string
    sync_realtime: boolean
    config_fields: ConfigField[]
    features?: string[]
}

interface ConfigField {
    name: string
    label: string
    type: string
    required: boolean
    placeholder?: string
    helper?: string
}

interface ConnectedConnector {
    connector_id: string
    tenant_id: string
    connector_type: string
    connector_name: string
    display_name?: string
    status: 'active' | 'error' | 'pending'
    last_sync?: string
    data_types: string[]
    metadata?: {
        error_message?: string
        [key: string]: unknown
    }
}

export default function ConnectorsNew() {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const queryClient = useQueryClient()

    const [selectedCategory, setSelectedCategory] = useState<ConnectorCategory>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [setupModalOpen, setSetupModalOpen] = useState(false)
    const [selectedConnector, setSelectedConnector] = useState<MarketplaceConnector | null>(null)

    // Fetch marketplace connectors
    const { data: marketplaceData, isLoading: isLoadingMarketplace } = useQuery({
        queryKey: ['marketplace-connectors', selectedCategory, searchQuery],
        queryFn: async () => {
            const params = new URLSearchParams()
            if (selectedCategory !== 'all') params.append('category', selectedCategory)
            if (searchQuery) params.append('search', searchQuery)

            const data = await get<{
                connectors: MarketplaceConnector[]
                total: number
                categories: string[]
            }>(`/v1/marketplace/connectors?${params.toString()}`)
            return data
        },
    })

    // Fetch connected connectors
    const { data: connectedConnectors, isLoading: isLoadingConnected } = useQuery({
        queryKey: ['connected-connectors', tenantId],
        queryFn: async () => {
            if (!tenantId) return []
            const data = await get<ConnectedConnector[]>(`/v1/tenants/${tenantId}/connectors/connected`)
            return data
        },
        enabled: !!tenantId,
    })

    const connectedIds = new Set(connectedConnectors?.map((c) => c.connector_type) || [])

    // Connect mutation
    const connectMutation = useMutation({
        mutationFn: async (payload: { connector_id: string; config: Record<string, unknown> }) => {
            if (!tenantId) throw new Error('No tenant ID')
            return await post(`/v1/tenants/${tenantId}/connectors/connect`, payload)
        },
        onSuccess: (_, variables) => {
            showNotification({
                title: 'Connector added',
                message: `${selectedConnector?.display_name} connected successfully!`,
                color: 'green',
                icon: <IconCheck />,
            })
            setSetupModalOpen(false)
            setSelectedConnector(null)
            queryClient.invalidateQueries({ queryKey: ['connected-connectors', tenantId] })
        },
        onError: (error: Error) => {
            showNotification({
                title: 'Connection failed',
                message: error.message || 'Please check your credentials and try again.',
                color: 'red',
                icon: <IconX />,
            })
        },
    })

    // Disconnect mutation
    const disconnectMutation = useMutation({
        mutationFn: async (connector: ConnectedConnector) => {
            if (!tenantId) throw new Error('No tenant ID')
            await del(`/v1/tenants/${tenantId}/connectors/${connector.connector_id}`)
        },
        onSuccess: (_, connector) => {
            showNotification({
                title: 'Connector removed',
                message: `${connector.display_name || connector.connector_name} disconnected.`,
                color: 'yellow',
            })
            queryClient.invalidateQueries({ queryKey: ['connected-connectors', tenantId] })
        },
    })

    // Sync mutation
    const syncMutation = useMutation({
        mutationFn: async (connector: ConnectedConnector) => {
            if (!tenantId) throw new Error('No tenant ID')
            await post(`/v1/tenants/${tenantId}/connectors/${connector.connector_id}/sync`, {})
        },
        onSuccess: () => {
            showNotification({
                title: 'Sync started',
                message: 'Data sync initiated. This may take a few moments.',
                color: 'blue',
                icon: <IconRefresh />,
            })
            queryClient.invalidateQueries({ queryKey: ['connected-connectors', tenantId] })
        },
    })

    const handleConnectClick = (connector: MarketplaceConnector) => {
        setSelectedConnector(connector)
        setSetupModalOpen(true)
    }

    const getIconEmoji = (icon: string) => {
        const iconMap: Record<string, string> = {
            ShoppingCart: '🛒',
            Calculator: '💰',
            Users: '👥',
            Package: '📦',
            TrendingUp: '📈',
            Mail: '📧',
            Cloud: '☁️',
            CreditCard: '💳',
        }
        return iconMap[icon] || '🔌'
    }

    return (
        <div className="page-shell">
            <div className="mx-auto w-full max-w-7xl">
                {/* Header */}
                <div className="glass-panel--light mb-6">
                    <Group justify="space-between" align="flex-start" mb="md">
                        <div style={{ flex: 1 }}>
                            <Group gap="sm" mb="sm">
                                <Text size="xl">🔌</Text>
                                <Title order={2} className="text-gray-900">
                                    Data Connectors
                                </Title>
                            </Group>
                            <Text className="text-gray-600 mb-3" maw={700}>
                                <strong>Think of this as connecting your fitness tracker to your health app.</strong> Your business
                                data flows in automatically, updating your Business Health Score and powering personalized insights
                                from your AI Coach.
                            </Text>
                            <Text className="text-gray-500" size="sm" maw={700}>
                                Start with CSV uploads or Google Drive for quick setup. Your connected data enables auto-tracking of
                                goals, real-time health metrics, and AI-powered recommendations.
                            </Text>
                        </div>
                        <Button
                            size="lg"
                            onClick={() => {
                                // Show marketplace in modal or scroll to marketplace section
                                const marketplace = document.getElementById('marketplace-section')
                                marketplace?.scrollIntoView({ behavior: 'smooth' })
                            }}
                        >
                            Add connector
                        </Button>
                    </Group>

                    <Group gap="xs">
                        {!connectedConnectors || connectedConnectors.length === 0 ? (
                            <Badge color="yellow" variant="light" size="lg" leftSection="⚠️">
                                No data connected yet
                            </Badge>
                        ) : (
                            <Badge color="green" variant="light" size="lg" leftSection={<IconCheck size={14} />}>
                                {connectedConnectors.length} Connected
                            </Badge>
                        )}
                        <Button variant="subtle" size="sm" leftSection={<span>🏪</span>}>
                            Browse Marketplace
                        </Button>
                    </Group>
                </div>

                <Grid gutter="lg">
                    {/* Connected Sources - Left Column */}
                    <Grid.Col span={{ base: 12, md: 6 }}>
                        <Card className="glass-panel--light h-full">
                            <Group justify="space-between" mb="md">
                                <Text fw={600} size="lg">
                                    Connected sources
                                </Text>
                                <Button
                                    variant="subtle"
                                    size="xs"
                                    leftSection={<IconRefresh size={14} />}
                                    onClick={() => queryClient.invalidateQueries({ queryKey: ['connected-connectors'] })}
                                >
                                    Refresh
                                </Button>
                            </Group>

                            <Text size="sm" c="dimmed" mb="md">
                                Connect your first data source to unlock real-time health tracking and personalized insights.
                            </Text>

                            {isLoadingConnected ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader size="md" />
                                </div>
                            ) : !connectedConnectors || connectedConnectors.length === 0 ? (
                                <div className="text-center py-8">
                                    <Card withBorder p="lg" radius="md" className="border-2 border-dashed">
                                        <Stack align="center" gap="sm">
                                            <Text size="sm" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.1em' }}>
                                                QUICKSTART
                                            </Text>
                                            <Text size="sm" c="dimmed">
                                                Upload your sales or inventory data to get started with actionable insights.
                                            </Text>
                                            <Button
                                                variant="light"
                                                onClick={() => {
                                                    const marketplace = document.getElementById('marketplace-section')
                                                    marketplace?.scrollIntoView({ behavior: 'smooth' })
                                                }}
                                            >
                                                ADD CONNECTOR
                                            </Button>
                                        </Stack>
                                    </Card>
                                </div>
                            ) : (
                                <Stack gap="sm">
                                    {connectedConnectors.map((connector) => (
                                        <Card key={connector.connector_id} withBorder radius="md" p="md">
                                            <Group justify="space-between" align="flex-start" mb="xs">
                                                <div style={{ flex: 1 }}>
                                                    <Group gap="xs" mb={4}>
                                                        <Text fw={600}>{connector.display_name || connector.connector_name}</Text>
                                                        <Badge
                                                            size="xs"
                                                            color={
                                                                connector.status === 'active'
                                                                    ? 'green'
                                                                    : connector.status === 'error'
                                                                        ? 'red'
                                                                        : 'yellow'
                                                            }
                                                        >
                                                            {connector.status}
                                                        </Badge>
                                                    </Group>
                                                    <Text size="xs" c="dimmed">
                                                        {connector.connector_type} · {connector.data_types.join(', ')}
                                                    </Text>
                                                    {connector.last_sync && (
                                                        <Text size="xs" c="dimmed">
                                                            Last sync: {new Date(connector.last_sync).toLocaleString()}
                                                        </Text>
                                                    )}
                                                    {connector.metadata?.error_message && (
                                                        <Text size="xs" c="red">
                                                            {connector.metadata.error_message}
                                                        </Text>
                                                    )}
                                                </div>
                                            </Group>

                                            <Group gap="xs" mt="sm">
                                                <Button
                                                    size="xs"
                                                    variant="light"
                                                    leftSection={<IconRefresh size={14} />}
                                                    onClick={() => syncMutation.mutate(connector)}
                                                    loading={syncMutation.isPending && syncMutation.variables === connector}
                                                >
                                                    Test connection
                                                </Button>
                                                <Button
                                                    size="xs"
                                                    variant="outline"
                                                    color="red"
                                                    onClick={() => disconnectMutation.mutate(connector)}
                                                    loading={disconnectMutation.isPending && disconnectMutation.variables === connector}
                                                >
                                                    Remove
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            )}
                        </Card>
                    </Grid.Col>

                    {/* Marketplace - Right Column */}
                    <Grid.Col span={{ base: 12, md: 6 }} id="marketplace-section">
                        <Card className="glass-panel--light">
                            <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.25em' }} mb="md">
                                RECOMMENDED STARTERS
                            </Text>
                            Connect your business tools to unlock real-time insights and AI-powered recommendations
                        </Text>
                        {connectedConnectors && connectedConnectors.length > 0 && (
                            <Group gap="xs">
                                <Badge color="green" variant="light" size="lg">
                                    <IconCheck size={14} /> {connectedConnectors.length} Connected
                                </Badge>
                            </Group>
                        )}
                    </div>
                </Group>
            </div>

            <Grid gutter="lg">
                {/* Connected Connectors - Left Column */}
                <Grid.Col span={{ base: 12, md: 5 }}>
                    <Card className="glass-panel--light h-full">
                        <Group justify="space-between" mb="md">
                            <Text fw={600} size="lg">
                                My Connections
                            </Text>
                            <ActionIcon
                                variant="subtle"
                                onClick={() => queryClient.invalidateQueries({ queryKey: ['connected-connectors'] })}
                            >
                                <IconRefresh size={18} />
                            </ActionIcon>
                        </Group>

                        {isLoadingConnected ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader size="md" />
                            </div>
                        ) : !connectedConnectors || connectedConnectors.length === 0 ? (
                            <div className="text-center py-12">
                                <Text size="xl" className="mb-2">
                                    🔌
                                </Text>
                                <Text size="sm" c="dimmed" className="mb-4">
                                    No connectors yet. Browse the marketplace to get started!
                                </Text>
                            </div>
                        ) : (
                            <ScrollArea h={600}>
                                <Stack gap="sm">
                                    {connectedConnectors.map((connector) => (
                                        <Card key={connector.connector_id} withBorder radius="md" p="md">
                                            <Group justify="space-between" align="flex-start" mb="xs">
                                                <div>
                                                    <Group gap="xs">
                                                        <Text fw={600}>{connector.display_name || connector.connector_name}</Text>
                                                        <Badge
                                                            size="xs"
                                                            color={
                                                                connector.status === 'active'
                                                                    ? 'green'
                                                                    : connector.status === 'error'
                                                                        ? 'red'
                                                                        : 'yellow'
                                                            }
                                                        >
                                                            {connector.status}
                                                        </Badge>
                                                    </Group>
                                                    <Text size="xs" c="dimmed">
                                                        {connector.data_types.join(', ')}
                                                    </Text>
                                                    {connector.last_sync && (
                                                        <Text size="xs" c="dimmed">
                                                            Last sync: {new Date(connector.last_sync).toLocaleString()}
                                                        </Text>
                                                    )}
                                                    {connector.metadata?.error_message && (
                                                        <Text size="xs" c="red">
                                                            {connector.metadata.error_message}
                                                        </Text>
                                                    )}
                                                </div>
                                            </Group>

                                            <Group gap="xs" mt="sm">
                                                <Button
                                                    size="xs"
                                                    variant="light"
                                                    leftSection={<IconRefresh size={14} />}
                                                    onClick={() => syncMutation.mutate(connector)}
                                                    loading={syncMutation.isPending && syncMutation.variables === connector}
                                                >
                                                    Sync
                                                </Button>
                                                <Button
                                                    size="xs"
                                                    variant="subtle"
                                                    color="red"
                                                    leftSection={<IconTrash size={14} />}
                                                    onClick={() => disconnectMutation.mutate(connector)}
                                                    loading={disconnectMutation.isPending && disconnectMutation.variables === connector}
                                                >
                                                    Remove
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            </ScrollArea>
                        )}
                    </Card>
                </Grid.Col>

                {/* Marketplace - Right Column */}
                <Grid.Col span={{ base: 12, md: 7 }}>
                    <Card className="glass-panel--light">
                        <Text fw={600} size="lg" mb="md">
                            Connector Marketplace
                        </Text>

                        {/* Search */}
                        <TextInput
                            placeholder="Search connectors..."
                            leftSection={<IconSearch size={16} />}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            mb="md"
                        />

                        {/* Category Tabs */}
                        <Tabs value={selectedCategory} onChange={(val) => setSelectedCategory((val as ConnectorCategory) || 'all')} mb="md">
                            <Tabs.List>
                                <Tabs.Tab value="all">All</Tabs.Tab>
                                <Tabs.Tab value="ecommerce">E-commerce</Tabs.Tab>
                                <Tabs.Tab value="finance">Finance</Tabs.Tab>
                                <Tabs.Tab value="inventory">Inventory</Tabs.Tab>
                                <Tabs.Tab value="storage">Storage</Tabs.Tab>
                            </Tabs.List>
                        </Tabs>

                        {isLoadingMarketplace ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader size="md" />
                            </div>
                        ) : (
                            <ScrollArea h={600}>
                                <Grid gutter="md">
                                    {marketplaceData?.connectors.map((connector) => {
                                        const isConnected = connectedIds.has(connector.id)

                                        return (
                                            <Grid.Col key={connector.id} span={6}>
                                                <Card withBorder radius="md" p="md" className="h-full flex flex-col">
                                                    <Group gap="xs" mb="xs">
                                                        <Text size="xl">{getIconEmoji(connector.icon)}</Text>
                                                        <div style={{ flex: 1 }}>
                                                            <Group gap={4}>
                                                                <Text fw={600} size="sm">
                                                                    {connector.display_name}
                                                                </Text>
                                                                {connector.verified && (
                                                                    <Badge size="xs" color="blue" variant="light">
                                                                        Verified
                                                                    </Badge>
                                                                )}
                                                            </Group>
                                                            <Text size="xs" c="dimmed">
                                                                {connector.setup_complexity}
                                                            </Text>
                                                        </div>
                                                    </Group>

                                                    <Text size="xs" c="dimmed" lineClamp={2} mb="xs">
                                                        {connector.description}
                                                    </Text>

                                                    <Group gap={4} mb="sm">
                                                        {connector.data_types.slice(0, 3).map((type) => (
                                                            <Badge key={type} size="xs" variant="dot">
                                                                {type}
                                                            </Badge>
                                                        ))}
                                                    </Group>

                                                    <Button
                                                        size="xs"
                                                        fullWidth
                                                        variant={isConnected ? 'light' : 'filled'}
                                                        color={isConnected ? 'green' : 'brand'}
                                                        leftSection={isConnected ? <IconCheck size={14} /> : <IconPlug size={14} />}
                                                        onClick={() => !isConnected && handleConnectClick(connector)}
                                                        disabled={isConnected}
                                                        className="mt-auto"
                                                    >
                                                        {isConnected ? 'Connected' : 'Connect'}
                                                    </Button>
                                                </Card>
                                            </Grid.Col>
                                        )
                                    })}
                                </Grid>
                            </ScrollArea>
                        )}
                    </Card>
                </Grid.Col>
            </Grid>

            {/* Setup Modal */}
            {selectedConnector && (
                <ConnectorSetupModal
                    connector={selectedConnector}
                    opened={setupModalOpen}
                    onClose={() => {
                        setSetupModalOpen(false)
                        setSelectedConnector(null)
                    }}
                    onConnect={(config) => {
                        connectMutation.mutate({
                            connector_id: selectedConnector.id,
                            config,
                        })
                    }}
                    isLoading={connectMutation.isPending}
                />
            )}
        </div>
        </div >
    )
}

// Setup Modal Component
interface ConnectorSetupModalProps {
    connector: MarketplaceConnector
    opened: boolean
    onClose: () => void
    onConnect: (config: Record<string, unknown>) => void
    isLoading: boolean
}

function ConnectorSetupModal({ connector, opened, onClose, onConnect, isLoading }: ConnectorSetupModalProps) {
    const { register, handleSubmit, formState: { errors } } = useForm()

    const onSubmit = (data: Record<string, unknown>) => {
        onConnect(data)
    }

    return (
        <Modal opened={opened} onClose={onClose} title={`Connect ${connector.display_name}`} size="lg">
            <form onSubmit={handleSubmit(onSubmit)}>
                <Stack gap="md">
                    <Text size="sm" c="dimmed">
                        {connector.description}
                    </Text>

                    {connector.features && connector.features.length > 0 && (
                        <div>
                            <Text size="sm" fw={600} mb="xs">
                                Features:
                            </Text>
                            <Stack gap={4}>
                                {connector.features.slice(0, 3).map((feature, idx) => (
                                    <Group key={idx} gap="xs">
                                        <IconCheck size={14} color="green" />
                                        <Text size="xs">{feature}</Text>
                                    </Group>
                                ))}
                            </Stack>
                        </div>
                    )}

                    <div>
                        <Text size="sm" fw={600} mb="xs">
                            Configuration:
                        </Text>
                        <Stack gap="sm">
                            {connector.config_fields.map((field) => {
                                if (field.type === 'textarea') {
                                    return (
                                        <Textarea
                                            key={field.name}
                                            label={field.label}
                                            placeholder={field.placeholder}
                                            description={field.helper}
                                            required={field.required}
                                            {...register(field.name, { required: field.required })}
                                            error={errors[field.name] ? `${field.label} is required` : undefined}
                                        />
                                    )
                                }

                                return (
                                    <TextInput
                                        key={field.name}
                                        label={field.label}
                                        placeholder={field.placeholder}
                                        description={field.helper}
                                        type={field.type === 'password' ? 'password' : 'text'}
                                        required={field.required}
                                        {...register(field.name, { required: field.required })}
                                        error={errors[field.name] ? `${field.label} is required` : undefined}
                                    />
                                )
                            })}
                        </Stack>
                    </div>

                    <Group justify="space-between" mt="md">
                        <Button variant="subtle" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button type="submit" loading={isLoading} leftSection={<IconPlug size={16} />}>
                            Connect
                        </Button>
                    </Group>
                </Stack>
            </form>
        </Modal>
    )
}
