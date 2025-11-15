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
    SegmentedControl,
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
import { API_BASE, del, get, post } from '../lib/api'
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
    supports_mcp?: boolean
}

interface StarterPackItemRef {
    id: string
    required?: boolean
}

interface StarterPack {
    id: string
    title: string
    description: string
    category: ConnectorCategory | 'restaurants'
    connectors: StarterPackItemRef[]
    notes?: string
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
    const [reuploadModalOpen, setReuploadModalOpen] = useState(false)
    const [connectorToReupload, setConnectorToReupload] = useState<ConnectedConnector | null>(null)
    const [editModeOpen, setEditModeOpen] = useState(false)
    const [connectorToEdit, setConnectorToEdit] = useState<ConnectedConnector | null>(null)

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
    const { data: connectedData, isLoading: isLoadingConnected } = useQuery({
        queryKey: ['connected-connectors', tenantId],
        queryFn: async () => {
            if (!tenantId) return { connectors: [], total: 0 }
            const data = await get<{ connectors: ConnectedConnector[]; total: number }>(`/v1/tenants/${tenantId}/connectors/connected`)
            return data
        },
        enabled: !!tenantId,
    })

    const connectedConnectors = connectedData?.connectors || []
    const connectedIds = new Set(connectedConnectors.map((c) => c.connector_type))

    // Fetch starter packs
    const { data: packsData } = useQuery({
        queryKey: ['starter-packs'],
        queryFn: async () => {
            const data = await get<{ packs: StarterPack[]; total: number }>(`/v1/marketplace/starter-packs`)
            return data
        },
    })

    // Connect mutation
    const connectMutation = useMutation({
        mutationFn: async (payload: { connector_id: string; config: Record<string, unknown> }) => {
            if (!tenantId) throw new Error('No tenant ID')

            // Determine display name based on connector type
            let displayName: string
            const isCSV = payload.connector_id === 'csv_upload'

            if (isCSV && payload.config.file_name) {
                // CSV: Use file_name
                displayName = String(payload.config.file_name)
            } else if (payload.config.connection_name) {
                // Use custom connection_name if provided
                displayName = String(payload.config.connection_name)
            } else {
                // Fallback to marketplace display name
                displayName = selectedConnector?.display_name || payload.connector_id
            }

            // Backend expects connector_type, not connector_id
            return await post(`/v1/tenants/${tenantId}/connectors`, {
                connector_type: payload.connector_id,
                display_name: displayName,
                config: payload.config,
                enable_mcp: Boolean((payload.config as any)?.enable_mcp),
            })
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

    const handleReuploadClick = (connector: ConnectedConnector) => {
        setConnectorToReupload(connector)
        setReuploadModalOpen(true)
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
                                    Data Sources
                                </Title>
                            </Group>
                            <Text className="text-gray-600 mb-3" maw={700}>
                                <strong>Think of this as connecting your fitness tracker to your health app.</strong> Your business
                                data flows in automatically, updating your Business Health Score and powering personalized insights
                                from your AI Coach.
                            </Text>
                            <Text className="text-gray-500" size="sm" maw={700}>
                                Start with a CSV upload for quick setup, or connect popular business tools like Salesforce, Shopify, or QuickBooks.
                                Your connected data enables auto-tracking of goals, real-time health metrics, and AI-powered recommendations.
                            </Text>
                        </div>
                        <Button
                            size="lg"
                            onClick={() => {
                                const marketplace = document.getElementById('marketplace-section')
                                marketplace?.scrollIntoView({ behavior: 'smooth' })
                            }}
                        >
                            Add Data Source
                        </Button>
                    </Group>

                    <Group gap="xs">
                        {!connectedConnectors || connectedConnectors.length === 0 ? (
                            <Badge color="yellow" variant="light" size="lg" leftSection="⚠️">
                                No data connected yet - connect your first source to unlock insights
                            </Badge>
                        ) : (
                            <Badge color="green" variant="light" size="lg" leftSection={<IconCheck size={14} />}>
                                {connectedConnectors.length} {connectedConnectors.length === 1 ? 'Source' : 'Sources'} Connected
                            </Badge>
                        )}
                    </Group>
                </div>

                {/* Main Content */}
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
                                        {connectedConnectors.map((connector) => {
                                            // Find marketplace definition to get proper display name
                                            const marketplaceDef = marketplaceData?.connectors.find(
                                                (m) => m.id === connector.connector_type || m.name === connector.connector_type
                                            )
                                            const connectorTypeName = marketplaceDef?.display_name || connector.connector_name

                                            return (
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
                                                                {Boolean(connector.metadata?.mcp_enabled) && (
                                                                    <Badge size="xs" color="violet" variant="light">
                                                                        MCP
                                                                    </Badge>
                                                                )}
                                                            </Group>
                                                            {/* Show connector type if display name is custom, with transport suffix */}
                                                            {connector.display_name && connector.display_name !== connectorTypeName && (
                                                                <Text size="xs" c="dimmed">
                                                                    {connectorTypeName} · {Boolean(connector.metadata?.mcp_enabled) ? 'via MCP' : 'via API'}
                                                                </Text>
                                                            )}
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
                                                        {/* CSV connectors: Show Re-upload instead of Sync */}
                                                        {connector.connector_type === 'csv_upload' ? (
                                                            <Button
                                                                size="xs"
                                                                variant="light"
                                                                leftSection={<IconRefresh size={14} />}
                                                                onClick={() => handleReuploadClick(connector)}
                                                            >
                                                                Re-upload
                                                            </Button>
                                                        ) : (
                                                            <Button
                                                                size="xs"
                                                                variant="light"
                                                                leftSection={<IconRefresh size={14} />}
                                                                onClick={() => syncMutation.mutate(connector)}
                                                                loading={syncMutation.isPending && syncMutation.variables === connector}
                                                            >
                                                                Sync
                                                            </Button>
                                                        )}
                                                        {marketplaceDef?.supports_mcp && (
                                                            <Button
                                                                size="xs"
                                                                variant="subtle"
                                                                onClick={() => {
                                                                    setConnectorToEdit(connector)
                                                                    setEditModeOpen(true)
                                                                }}
                                                            >
                                                                Edit mode
                                                            </Button>
                                                        )}
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
                                            )
                                        })}
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

                            {/* Starter Packs */}
                            {packsData?.packs && packsData.packs.length > 0 && (
                                <Card withBorder mb="md" p="md">
                                    <Group justify="space-between" mb="sm">
                                        <Text fw={600}>Starter Packs</Text>
                                        <Badge color="blue" variant="light">Beta</Badge>
                                    </Group>
                                    <Grid>
                                        {packsData.packs.map((pack) => (
                                            <Grid.Col key={pack.id} span={{ base: 12, md: 6 }}>
                                                <Card withBorder radius="md" p="md">
                                                    <Text fw={600}>{pack.title}</Text>
                                                    <Text size="xs" c="dimmed" mb="xs">{pack.description}</Text>
                                                    <Group gap={6} mb="xs">
                                                        {pack.connectors.slice(0, 4).map((c) => (
                                                            <Badge key={c.id} size="xs" variant="dot">{c.id}</Badge>
                                                        ))}
                                                        {pack.connectors.length > 4 && (
                                                            <Badge size="xs" variant="light">+{pack.connectors.length - 4}</Badge>
                                                        )}
                                                    </Group>
                                                    {pack.notes && (
                                                        <Text size="xs" c="dimmed" mb="xs">{pack.notes}</Text>
                                                    )}
                                                    <Button
                                                        size="xs"
                                                        variant="light"
                                                        onClick={() => {
                                                            // Open connect modal for the first connector in the pack's category, or scroll marketplace to that category
                                                            const market = document.getElementById('marketplace-section')
                                                            market?.scrollIntoView({ behavior: 'smooth' })
                                                            if (pack.category && pack.category !== 'restaurants') {
                                                                setSelectedCategory(pack.category as ConnectorCategory)
                                                            }
                                                        }}
                                                    >
                                                        Explore pack
                                                    </Button>
                                                </Card>
                                            </Grid.Col>
                                        ))}
                                    </Grid>
                                </Card>
                            )}

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
                                    <Tabs.Tab value="crm">CRM</Tabs.Tab>
                                    <Tabs.Tab value="pos">POS</Tabs.Tab>
                                    <Tabs.Tab value="restaurants">Restaurants</Tabs.Tab>
                                    <Tabs.Tab value="marketing">Marketing</Tabs.Tab>
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
                                            // CSV connectors can have multiple instances
                                            const allowMultiple = connector.id === 'csv_upload' || connector.name === 'csv_upload'
                                            const isConnected = !allowMultiple && connectedIds.has(connector.id)

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
                                                                    {connector.supports_mcp && (
                                                                        <Badge size="xs" color="violet" variant="dot">
                                                                            MCP
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
            </div>

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

            {/* Re-upload Modal for CSV */}
            {connectorToReupload && (
                <FileReuploadModal
                    connector={connectorToReupload}
                    opened={reuploadModalOpen}
                    onClose={() => {
                        setReuploadModalOpen(false)
                        setConnectorToReupload(null)
                    }}
                    onSuccess={() => {
                        setReuploadModalOpen(false)
                        setConnectorToReupload(null)
                        queryClient.invalidateQueries({ queryKey: ['connected-connectors', tenantId] })
                    }}
                />
            )}

            {/* Edit Mode Modal */}
            {editModeOpen && connectorToEdit && (
                <ModeEditModal
                    connector={connectorToEdit}
                    supportsMcp={Boolean(marketplaceData?.connectors.find(m => m.id === connectorToEdit.connector_type || m.name === connectorToEdit.connector_type)?.supports_mcp)}
                    opened={editModeOpen}
                    onClose={() => setEditModeOpen(false)}
                    onUpdated={() => queryClient.invalidateQueries({ queryKey: ['connected-connectors', tenantId] })}
                />
            )}
        </div>
    )
}

// File Re-upload Modal Component
interface FileReuploadModalProps {
    connector: ConnectedConnector
    opened: boolean
    onClose: () => void
    onSuccess: () => void
}

function FileReuploadModal({ connector, opened, onClose, onSuccess }: FileReuploadModalProps) {
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const tenantId = useAuthStore((s) => s.tenantId)

    const handleUpload = async () => {
        if (!file || !tenantId) return

        setUploading(true)
        try {
            const formData = new FormData()
            formData.append('file', file)
            formData.append('connector_id', connector.connector_id)
            formData.append('tenant_id', tenantId)
            formData.append('file_name', file.name)

            const response = await fetch(`${API_BASE}/api/connectors/upload_csv`, {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                throw new Error('File upload failed')
            }

            showNotification({
                title: 'File updated',
                message: `${file.name} uploaded successfully!`,
                color: 'green',
                icon: <IconCheck />,
            })

            onSuccess()
        } catch (error) {
            console.error('CSV re-upload error:', error)
            showNotification({
                title: 'Upload failed',
                message: 'Failed to upload file. Please try again.',
                color: 'red',
            })
        } finally {
            setUploading(false)
        }
    }

    return (
        <Modal opened={opened} onClose={onClose} title={`Re-upload File for ${connector.display_name}`} size="md">
            <Stack gap="md">
                <Text size="sm" c="dimmed">
                    Upload a new CSV or Excel file to replace the existing data for this connector.
                </Text>

                <div>
                    <Text size="sm" mb={4} fw={500}>Select New File *</Text>
                    <input
                        type="file"
                        accept=".csv,.xlsx,.xls"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        style={{
                            width: '100%',
                            padding: '8px',
                            border: '1px solid #dee2e6',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    />
                    {file && (
                        <Text size="xs" c="dimmed" mt={4}>
                            Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                        </Text>
                    )}
                    {!file && (
                        <Text size="xs" c="dimmed" mt={4}>
                            Choose a file to upload
                        </Text>
                    )}
                </div>

                <Group justify="space-between" mt="md">
                    <Button variant="subtle" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleUpload}
                        loading={uploading}
                        disabled={!file}
                        leftSection={<IconRefresh size={16} />}
                    >
                        {uploading ? 'Uploading...' : 'Upload File'}
                    </Button>
                </Group>
            </Stack>
        </Modal>
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
    const { register, handleSubmit, formState: { errors }, watch } = useForm()
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [testing, setTesting] = useState(false)
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const [integrationMode, setIntegrationMode] = useState<'http' | 'mcp'>('http')

    const isCSVConnector = connector.id === 'csv_upload' || connector.name === 'csv_upload'

    // Watch all form values for test button
    const formValues = watch()

    const handleTestConnection = async () => {
        setTesting(true)
        setTestResult(null)

        try {
            const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/connectors/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiToken && { 'Authorization': `Bearer ${apiToken}` })
                },
                body: JSON.stringify({
                    connector_type: connector.id,
                    config: { ...formValues, enable_mcp: integrationMode === 'mcp' }
                })
            })

            const data = await response.json()

            setTestResult({
                success: data.success,
                message: data.message
            })

            if (data.success) {
                showNotification({
                    title: 'Connection successful',
                    message: data.message,
                    color: 'green',
                    icon: <IconCheck />
                })
            } else {
                showNotification({
                    title: 'Connection failed',
                    message: data.message,
                    color: 'red',
                    icon: <IconX />
                })
            }
        } catch (error) {
            setTestResult({
                success: false,
                message: 'Failed to test connection'
            })
            showNotification({
                title: 'Test failed',
                message: 'Unable to test connection. Please try again.',
                color: 'red',
                icon: <IconX />
            })
        } finally {
            setTesting(false)
        }
    }

    const onSubmit = async (data: Record<string, unknown>) => {
        if (isCSVConnector && file) {
            // For CSV, upload the file first
            setUploading(true)
            try {
                const formData = new FormData()
                formData.append('file', file)
                formData.append('connector_id', connector.id)
                formData.append('tenant_id', tenantId || 'demo')
                formData.append('file_name', data.file_name as string || file.name)

                const response = await fetch(`${API_BASE}/api/connectors/upload_csv`, {
                    method: 'POST',
                    body: formData,
                })

                if (!response.ok) {
                    throw new Error('File upload failed')
                }

                // Pass file metadata in config
                onConnect({
                    ...data,
                    file_name: data.file_name as string || file.name,
                    file_uploaded: true,
                    enable_mcp: integrationMode === 'mcp',
                })
            } catch (error) {
                console.error('CSV upload error:', error)
                showNotification({
                    title: 'Upload failed',
                    message: 'Failed to upload CSV file. Please try again.',
                    color: 'red',
                })
            } finally {
                setUploading(false)
            }
        } else {
            onConnect({
                ...data,
                enable_mcp: integrationMode === 'mcp',
            })
        }
    }

    return (
        <Modal opened={opened} onClose={onClose} title={`Connect ${connector.display_name}`} size="lg">
            <form onSubmit={handleSubmit(onSubmit)}>
                <Stack gap="md">
                    <Text size="sm" c="dimmed">
                        {connector.description}
                    </Text>

                    {/* Salesforce Setup Guide */}
                    {connector.id === 'salesforce' && (
                        <Card withBorder p="sm" style={{ backgroundColor: '#f8f9fa' }}>
                            <Text size="sm" fw={600} mb="xs">
                                📋 Setup Requirements
                            </Text>
                            <Stack gap={6}>
                                <Text size="xs" c="dimmed">
                                    1. <strong>Create a Connected App</strong> in Salesforce Setup
                                </Text>
                                <Text size="xs" c="dimmed">
                                    2. Enable OAuth Settings with "password" grant type
                                </Text>
                                <Text size="xs" c="dimmed">
                                    3. Copy your Consumer Key and Consumer Secret
                                </Text>
                                <Text size="xs" c="dimmed">
                                    4. Reset your Security Token: Setup → My Personal Information → Reset Security Token
                                </Text>
                            </Stack>
                            <Text size="xs" c="blue" mt="xs" style={{ cursor: 'pointer' }}>
                                <a
                                    href="https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ textDecoration: 'none', color: 'inherit' }}
                                >
                                    📖 View Salesforce Setup Guide →
                                </a>
                            </Text>
                        </Card>
                    )}

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
                        {connector.supports_mcp && (
                            <div style={{ marginBottom: 8 }}>
                                <Text size="xs" c="dimmed" mb={4}>Connection method</Text>
                                <SegmentedControl
                                    value={integrationMode}
                                    onChange={(val) => setIntegrationMode(val as 'http' | 'mcp')}
                                    data={[
                                        { label: 'HTTP API', value: 'http' },
                                        { label: 'MCP (beta)', value: 'mcp' },
                                    ]}
                                />
                                <Text size="xs" c="dimmed" mt={6}>
                                    HTTP is simplest and recommended. Choose MCP to enable agent tool-calls where supported.
                                </Text>
                            </div>
                        )}
                        <Stack gap="sm">
                            {isCSVConnector ? (
                                <>
                                    <TextInput
                                        label="Data Source Name"
                                        placeholder="e.g., Sales Data Q4 2024"
                                        description="Give this data source a descriptive name"
                                        required
                                        {...register('file_name', { required: true })}
                                        error={errors.file_name ? 'Name is required' : undefined}
                                    />
                                    <div>
                                        <Text size="sm" mb={4}>Upload CSV or Excel File *</Text>
                                        <input
                                            type="file"
                                            accept=".csv,.xlsx,.xls"
                                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                                            style={{
                                                width: '100%',
                                                padding: '8px',
                                                border: '1px solid #dee2e6',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        />
                                        {file && (
                                            <Text size="xs" c="dimmed" mt={4}>
                                                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                                            </Text>
                                        )}
                                        {!file && (
                                            <Text size="xs" c="red" mt={4}>
                                                Please select a file to upload
                                            </Text>
                                        )}
                                    </div>
                                </>
                            ) : (
                                connector.config_fields.map((field) => {
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
                                })
                            )}
                        </Stack>
                    </div>

                    {/* Test result display */}
                    {testResult && !isCSVConnector && (
                        <div
                            style={{
                                padding: '12px',
                                borderRadius: '6px',
                                backgroundColor: testResult.success ? '#e7f5f0' : '#ffe5e5',
                                border: `1px solid ${testResult.success ? '#40c057' : '#fa5252'}`
                            }}
                        >
                            <Group gap="xs">
                                {testResult.success ? (
                                    <IconCheck size={18} color="#40c057" />
                                ) : (
                                    <IconX size={18} color="#fa5252" />
                                )}
                                <Text size="sm" fw={500} c={testResult.success ? 'green' : 'red'}>
                                    {testResult.message}
                                </Text>
                            </Group>
                        </div>
                    )}

                    <Group justify="space-between" mt="md">
                        <Button variant="subtle" onClick={onClose}>
                            Cancel
                        </Button>
                        <Group gap="xs">
                            {!isCSVConnector && (
                                <Button
                                    variant="light"
                                    onClick={handleTestConnection}
                                    loading={testing}
                                    leftSection={<IconRefresh size={16} />}
                                >
                                    Test Connection
                                </Button>
                            )}
                            <Button
                                type="submit"
                                loading={isLoading || uploading}
                                leftSection={<IconPlug size={16} />}
                                disabled={isCSVConnector && !file}
                            >
                                {uploading ? 'Uploading...' : 'Connect'}
                            </Button>
                        </Group>
                    </Group>
                </Stack>
            </form>
        </Modal>
    )
}

// Minimal modal to toggle MCP mode for an existing connector
function ModeEditModal({ connector, supportsMcp, opened, onClose, onUpdated }: { connector: ConnectedConnector; supportsMcp: boolean; opened: boolean; onClose: () => void; onUpdated: () => void }) {
    const tenantId = useAuthStore((s) => s.tenantId)
    const [mode, setMode] = useState<'http' | 'mcp'>(Boolean(connector.metadata?.mcp_enabled) ? 'mcp' : 'http')
    const [saving, setSaving] = useState(false)

    const handleSave = async () => {
        if (!tenantId) return
        setSaving(true)
        try {
            await post(`/v1/tenants/${tenantId}/connectors/${connector.connector_id}`, {
                enable_mcp: mode === 'mcp',
            })
            showNotification({ title: 'Updated', message: `Mode set to ${mode.toUpperCase()}`, color: 'green', icon: <IconCheck /> })
            onUpdated()
            onClose()
        } catch (e) {
            showNotification({ title: 'Update failed', message: 'Unable to update mode', color: 'red', icon: <IconX /> })
        } finally {
            setSaving(false)
        }
    }

    return (
        <Modal opened={opened} onClose={onClose} title={`Edit mode: ${connector.display_name || connector.connector_name}`} size="sm">
            <Stack gap="md">
                {supportsMcp ? (
                    <>
                        <Text size="xs" c="dimmed">Select how this connector communicates with the service.</Text>
                        <SegmentedControl
                            value={mode}
                            onChange={(v) => setMode(v as 'http' | 'mcp')}
                            data={[{ label: 'HTTP API', value: 'http' }, { label: 'MCP (beta)', value: 'mcp' }]}
                        />
                        <Text size="xs" c="dimmed">
                            HTTP is simplest and recommended. MCP enables agent tool-calls where supported.
                        </Text>
                    </>
                ) : (
                    <Text size="sm">This connector doesn’t support MCP. It uses HTTP API.</Text>
                )}
                <Group justify="space-between" mt="md">
                    <Button variant="subtle" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSave} loading={saving}>Save</Button>
                </Group>
            </Stack>
        </Modal>
    )
}
