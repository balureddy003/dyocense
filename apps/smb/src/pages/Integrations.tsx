import {
    ActionIcon,
    Alert,
    Badge,
    Button,
    Card,
    Code,
    Container,
    CopyButton,
    Grid,
    Group,
    Modal,
    MultiSelect,
    Paper,
    Select,
    Stack,
    Table,
    Tabs,
    Text,
    TextInput,
    Textarea,
    Title
} from '@mantine/core'
import {
    IconAlertCircle,
    IconBrandStripe,
    IconCash,
    IconCheck,
    IconCopy,
    IconKey,
    IconPlug,
    IconPlus,
    IconRefresh,
    IconSettings,
    IconShoppingCart,
    IconTrash,
    IconWebhook
} from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

// Types
type IntegrationType = 'quickbooks' | 'stripe' | 'square' | 'custom_api'
type IntegrationStatus = 'active' | 'inactive' | 'error' | 'pending'

interface Integration {
    integration_id: string
    integration_type: IntegrationType
    display_name: string
    status: IntegrationStatus
    connected_at?: string
    last_sync_at?: string
}

interface Webhook {
    webhook_id: string
    integration_id: string
    url: string
    events: string[]
    is_active: boolean
    created_at: string
    last_triggered_at?: string
    total_deliveries: number
    successful_deliveries: number
    failed_deliveries: number
}

interface APIKey {
    key_id: string
    name: string
    description: string
    scopes: string[]
    is_active: boolean
    created_at: string
    expires_at?: string
    last_used_at?: string
    total_requests: number
}

const TENANT_ID = 'tenant-123' // Replace with actual tenant context

const integrationConfigs = {
    quickbooks: {
        name: 'QuickBooks Online',
        icon: IconCash,
        color: 'green',
        description: 'Sync accounting data, invoices, and payments',
        authType: 'oauth' as const,
        features: ['Customers', 'Invoices', 'Payments', 'Reports'],
    },
    stripe: {
        name: 'Stripe',
        icon: IconBrandStripe,
        color: 'indigo',
        description: 'Connect payment processing and subscription data',
        authType: 'api_key' as const,
        features: ['Payments', 'Customers', 'Subscriptions', 'Invoices'],
    },
    square: {
        name: 'Square',
        icon: IconShoppingCart,
        color: 'blue',
        description: 'Integrate POS, inventory, and order management',
        authType: 'oauth' as const,
        features: ['Orders', 'Inventory', 'Customers', 'Products'],
    },
    custom_api: {
        name: 'Custom API',
        icon: IconPlug,
        color: 'gray',
        description: 'Connect your own systems via REST API',
        authType: 'api_key' as const,
        features: ['Full API Access', 'Custom Webhooks', 'Data Sync'],
    },
}

export function Integrations() {
    const queryClient = useQueryClient()
    const [activeTab, setActiveTab] = useState<string | null>('integrations')

    // Integration state
    const [createIntegrationOpened, setCreateIntegrationOpened] = useState(false)
    const [newIntegrationType, setNewIntegrationType] = useState<IntegrationType | null>(null)
    const [newIntegrationName, setNewIntegrationName] = useState('')
    const [connectModalOpened, setConnectModalOpened] = useState(false)
    const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
    const [connectionCredentials, setConnectionCredentials] = useState('')

    // Webhook state
    const [createWebhookOpened, setCreateWebhookOpened] = useState(false)
    const [webhookUrl, setWebhookUrl] = useState('')
    const [webhookEvents, setWebhookEvents] = useState<string[]>([])
    const [webhookIntegrationId, setWebhookIntegrationId] = useState('')
    const [createdWebhookSecret, setCreatedWebhookSecret] = useState('')

    // API Key state
    const [createApiKeyOpened, setCreateApiKeyOpened] = useState(false)
    const [apiKeyName, setApiKeyName] = useState('')
    const [apiKeyDescription, setApiKeyDescription] = useState('')
    const [apiKeyScopes, setApiKeyScopes] = useState<string[]>([])
    const [apiKeyExpireDays, setApiKeyExpireDays] = useState<string>('')
    const [createdApiKey, setCreatedApiKey] = useState('')

    // Fetch integrations
    const { data: integrationsData } = useQuery({
        queryKey: ['integrations', TENANT_ID],
        queryFn: async () => {
            const res = await fetch(`/v1/tenants/${TENANT_ID}/integrations`)
            if (!res.ok) throw new Error('Failed to fetch integrations')
            return res.json()
        },
    })

    // Fetch webhooks
    const { data: webhooksData } = useQuery({
        queryKey: ['webhooks', TENANT_ID],
        queryFn: async () => {
            const res = await fetch(`/v1/tenants/${TENANT_ID}/webhooks`)
            if (!res.ok) throw new Error('Failed to fetch webhooks')
            return res.json()
        },
    })

    // Fetch API keys
    const { data: apiKeysData } = useQuery({
        queryKey: ['apiKeys', TENANT_ID],
        queryFn: async () => {
            const res = await fetch(`/v1/tenants/${TENANT_ID}/api-keys`)
            if (!res.ok) throw new Error('Failed to fetch API keys')
            return res.json()
        },
    })

    // Create integration mutation
    const createIntegrationMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                integration_type: newIntegrationType!,
                display_name: newIntegrationName,
            })
            const res = await fetch(`/v1/tenants/${TENANT_ID}/integrations?${params}`, {
                method: 'POST',
            })
            if (!res.ok) throw new Error('Failed to create integration')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['integrations', TENANT_ID] })
            setCreateIntegrationOpened(false)
            setNewIntegrationType(null)
            setNewIntegrationName('')
        },
    })

    // Connect integration mutation (for API key based)
    const connectIntegrationMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                credentials: connectionCredentials,
            })
            const res = await fetch(
                `/v1/tenants/${TENANT_ID}/integrations/${selectedIntegration!.integration_id}/connect?${params}`,
                { method: 'POST' }
            )
            if (!res.ok) throw new Error('Failed to connect integration')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['integrations', TENANT_ID] })
            setConnectModalOpened(false)
            setConnectionCredentials('')
            setSelectedIntegration(null)
        },
    })

    // Sync integration mutation
    const syncIntegrationMutation = useMutation({
        mutationFn: async (integrationId: string) => {
            const res = await fetch(
                `/v1/tenants/${TENANT_ID}/integrations/${integrationId}/sync`,
                { method: 'POST' }
            )
            if (!res.ok) throw new Error('Failed to sync integration')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['integrations', TENANT_ID] })
        },
    })

    // Delete integration mutation
    const deleteIntegrationMutation = useMutation({
        mutationFn: async (integrationId: string) => {
            const res = await fetch(
                `/v1/tenants/${TENANT_ID}/integrations/${integrationId}`,
                { method: 'DELETE' }
            )
            if (!res.ok) throw new Error('Failed to delete integration')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['integrations', TENANT_ID] })
        },
    })

    // Create webhook mutation
    const createWebhookMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                integration_id: webhookIntegrationId,
                url: webhookUrl,
                events: webhookEvents.join(','),
            })
            const res = await fetch(`/v1/tenants/${TENANT_ID}/webhooks?${params}`, {
                method: 'POST',
            })
            if (!res.ok) throw new Error('Failed to create webhook')
            return res.json()
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['webhooks', TENANT_ID] })
            setCreatedWebhookSecret(data.secret)
            setWebhookUrl('')
            setWebhookEvents([])
            setWebhookIntegrationId('')
        },
    })

    // Delete webhook mutation
    const deleteWebhookMutation = useMutation({
        mutationFn: async (webhookId: string) => {
            const res = await fetch(`/v1/tenants/${TENANT_ID}/webhooks/${webhookId}`, {
                method: 'DELETE',
            })
            if (!res.ok) throw new Error('Failed to delete webhook')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['webhooks', TENANT_ID] })
        },
    })

    // Create API key mutation
    const createApiKeyMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                name: apiKeyName,
                description: apiKeyDescription,
                scopes: apiKeyScopes.join(','),
            })
            if (apiKeyExpireDays) {
                params.append('expires_in_days', apiKeyExpireDays)
            }
            const res = await fetch(`/v1/tenants/${TENANT_ID}/api-keys?${params}`, {
                method: 'POST',
            })
            if (!res.ok) throw new Error('Failed to create API key')
            return res.json()
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['apiKeys', TENANT_ID] })
            setCreatedApiKey(data.api_key)
            setApiKeyName('')
            setApiKeyDescription('')
            setApiKeyScopes([])
            setApiKeyExpireDays('')
        },
    })

    // Revoke API key mutation
    const revokeApiKeyMutation = useMutation({
        mutationFn: async (keyId: string) => {
            const res = await fetch(
                `/v1/tenants/${TENANT_ID}/api-keys/${keyId}/revoke`,
                { method: 'POST' }
            )
            if (!res.ok) throw new Error('Failed to revoke API key')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['apiKeys', TENANT_ID] })
        },
    })

    // Delete API key mutation
    const deleteApiKeyMutation = useMutation({
        mutationFn: async (keyId: string) => {
            const res = await fetch(`/v1/tenants/${TENANT_ID}/api-keys/${keyId}`, {
                method: 'DELETE',
            })
            if (!res.ok) throw new Error('Failed to delete API key')
            return res.json()
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['apiKeys', TENANT_ID] })
        },
    })

    const integrations: Integration[] = integrationsData?.integrations || []
    const webhooks: Webhook[] = webhooksData?.webhooks || []
    const apiKeys: APIKey[] = apiKeysData?.api_keys || []

    const handleConnectClick = (integration: Integration) => {
        const config = integrationConfigs[integration.integration_type]
        if (config.authType === 'oauth') {
            // Initiate OAuth flow
            window.location.href = `/v1/tenants/${TENANT_ID}/integrations/${integration.integration_id}/oauth/initiate?redirect_uri=${encodeURIComponent(window.location.origin + '/oauth-callback')}`
        } else {
            // Show API key modal
            setSelectedIntegration(integration)
            setConnectModalOpened(true)
        }
    }

    return (
        <Container size="xl" py="xl">
            <Stack gap="lg">
                <div>
                    <Title order={2}>Integration Hub</Title>
                    <Text c="dimmed" size="sm">
                        Connect third-party services and enable API access
                    </Text>
                </div>

                <Tabs value={activeTab} onChange={setActiveTab}>
                    <Tabs.List>
                        <Tabs.Tab value="integrations" leftSection={<IconPlug size={16} />}>
                            Integrations
                        </Tabs.Tab>
                        <Tabs.Tab value="webhooks" leftSection={<IconWebhook size={16} />}>
                            Webhooks
                        </Tabs.Tab>
                        <Tabs.Tab value="api-keys" leftSection={<IconKey size={16} />}>
                            API Keys
                        </Tabs.Tab>
                    </Tabs.List>

                    {/* Integrations Tab */}
                    <Tabs.Panel value="integrations" pt="xl">
                        <Stack gap="lg">
                            <Group justify="space-between">
                                <Text size="lg" fw={600}>
                                    Connected Services
                                </Text>
                                <Button
                                    leftSection={<IconPlus size={16} />}
                                    onClick={() => setCreateIntegrationOpened(true)}
                                >
                                    Add Integration
                                </Button>
                            </Group>

                            {integrations.length === 0 ? (
                                <Paper p="xl" withBorder style={{ textAlign: 'center' }}>
                                    <IconPlug size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                                    <Text size="lg" fw={500} mb="xs">
                                        No integrations yet
                                    </Text>
                                    <Text c="dimmed" size="sm" mb="lg">
                                        Connect services like QuickBooks, Stripe, or Square to sync data
                                    </Text>
                                    <Button onClick={() => setCreateIntegrationOpened(true)}>
                                        Add Your First Integration
                                    </Button>
                                </Paper>
                            ) : (
                                <Grid>
                                    {integrations.map((integration) => {
                                        const config = integrationConfigs[integration.integration_type]
                                        const Icon = config.icon
                                        return (
                                            <Grid.Col key={integration.integration_id} span={{ base: 12, md: 6 }}>
                                                <Card shadow="sm" padding="lg" withBorder>
                                                    <Group justify="space-between" mb="md">
                                                        <Group>
                                                            <Icon size={32} color={`var(--mantine-color-${config.color}-6)`} />
                                                            <div>
                                                                <Text fw={600}>{integration.display_name}</Text>
                                                                <Text size="xs" c="dimmed">
                                                                    {config.name}
                                                                </Text>
                                                            </div>
                                                        </Group>
                                                        <Badge
                                                            color={
                                                                integration.status === 'active'
                                                                    ? 'green'
                                                                    : integration.status === 'error'
                                                                        ? 'red'
                                                                        : 'gray'
                                                            }
                                                            variant="light"
                                                        >
                                                            {integration.status}
                                                        </Badge>
                                                    </Group>

                                                    <Text size="sm" c="dimmed" mb="md">
                                                        {config.description}
                                                    </Text>

                                                    <Group gap="xs" mb="md">
                                                        {config.features.map((feature) => (
                                                            <Badge key={feature} size="xs" variant="outline">
                                                                {feature}
                                                            </Badge>
                                                        ))}
                                                    </Group>

                                                    {integration.last_sync_at && (
                                                        <Text size="xs" c="dimmed" mb="md">
                                                            Last synced:{' '}
                                                            {new Date(integration.last_sync_at).toLocaleString()}
                                                        </Text>
                                                    )}

                                                    <Group gap="xs">
                                                        {integration.status === 'pending' ? (
                                                            <Button
                                                                size="xs"
                                                                variant="filled"
                                                                onClick={() => handleConnectClick(integration)}
                                                            >
                                                                Connect
                                                            </Button>
                                                        ) : (
                                                            <>
                                                                <Button
                                                                    size="xs"
                                                                    variant="light"
                                                                    leftSection={<IconRefresh size={14} />}
                                                                    onClick={() =>
                                                                        syncIntegrationMutation.mutate(
                                                                            integration.integration_id
                                                                        )
                                                                    }
                                                                    loading={syncIntegrationMutation.isPending}
                                                                >
                                                                    Sync
                                                                </Button>
                                                                <Button
                                                                    size="xs"
                                                                    variant="light"
                                                                    leftSection={<IconSettings size={14} />}
                                                                >
                                                                    Settings
                                                                </Button>
                                                            </>
                                                        )}
                                                        <ActionIcon
                                                            variant="light"
                                                            color="red"
                                                            onClick={() =>
                                                                deleteIntegrationMutation.mutate(
                                                                    integration.integration_id
                                                                )
                                                            }
                                                        >
                                                            <IconTrash size={16} />
                                                        </ActionIcon>
                                                    </Group>
                                                </Card>
                                            </Grid.Col>
                                        )
                                    })}
                                </Grid>
                            )}
                        </Stack>
                    </Tabs.Panel>

                    {/* Webhooks Tab */}
                    <Tabs.Panel value="webhooks" pt="xl">
                        <Stack gap="lg">
                            <Group justify="space-between">
                                <div>
                                    <Text size="lg" fw={600}>
                                        Webhook Endpoints
                                    </Text>
                                    <Text size="sm" c="dimmed">
                                        Receive real-time event notifications from integrations
                                    </Text>
                                </div>
                                <Button
                                    leftSection={<IconPlus size={16} />}
                                    onClick={() => setCreateWebhookOpened(true)}
                                    disabled={integrations.filter((i) => i.status === 'active').length === 0}
                                >
                                    Create Webhook
                                </Button>
                            </Group>

                            {webhooks.length === 0 ? (
                                <Paper p="xl" withBorder style={{ textAlign: 'center' }}>
                                    <IconWebhook size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                                    <Text size="lg" fw={500} mb="xs">
                                        No webhooks configured
                                    </Text>
                                    <Text c="dimmed" size="sm" mb="lg">
                                        Set up webhooks to receive real-time notifications
                                    </Text>
                                </Paper>
                            ) : (
                                <Table>
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>URL</Table.Th>
                                            <Table.Th>Events</Table.Th>
                                            <Table.Th>Status</Table.Th>
                                            <Table.Th>Deliveries</Table.Th>
                                            <Table.Th>Actions</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {webhooks.map((webhook) => (
                                            <Table.Tr key={webhook.webhook_id}>
                                                <Table.Td>
                                                    <Code>{webhook.url}</Code>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Group gap={4}>
                                                        {webhook.events.slice(0, 2).map((event) => (
                                                            <Badge key={event} size="xs" variant="light">
                                                                {event}
                                                            </Badge>
                                                        ))}
                                                        {webhook.events.length > 2 && (
                                                            <Badge size="xs" variant="light">
                                                                +{webhook.events.length - 2}
                                                            </Badge>
                                                        )}
                                                    </Group>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Badge color={webhook.is_active ? 'green' : 'gray'} size="sm">
                                                        {webhook.is_active ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Text size="sm">
                                                        {webhook.successful_deliveries}/{webhook.total_deliveries}
                                                    </Text>
                                                </Table.Td>
                                                <Table.Td>
                                                    <ActionIcon
                                                        variant="light"
                                                        color="red"
                                                        onClick={() => deleteWebhookMutation.mutate(webhook.webhook_id)}
                                                    >
                                                        <IconTrash size={16} />
                                                    </ActionIcon>
                                                </Table.Td>
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            )}
                        </Stack>
                    </Tabs.Panel>

                    {/* API Keys Tab */}
                    <Tabs.Panel value="api-keys" pt="xl">
                        <Stack gap="lg">
                            <Group justify="space-between">
                                <div>
                                    <Text size="lg" fw={600}>
                                        API Keys
                                    </Text>
                                    <Text size="sm" c="dimmed">
                                        Create keys for programmatic access to your data
                                    </Text>
                                </div>
                                <Button
                                    leftSection={<IconPlus size={16} />}
                                    onClick={() => setCreateApiKeyOpened(true)}
                                >
                                    Generate API Key
                                </Button>
                            </Group>

                            {apiKeys.length === 0 ? (
                                <Paper p="xl" withBorder style={{ textAlign: 'center' }}>
                                    <IconKey size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                                    <Text size="lg" fw={500} mb="xs">
                                        No API keys yet
                                    </Text>
                                    <Text c="dimmed" size="sm" mb="lg">
                                        Generate API keys to access your data programmatically
                                    </Text>
                                </Paper>
                            ) : (
                                <Table>
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>Name</Table.Th>
                                            <Table.Th>Scopes</Table.Th>
                                            <Table.Th>Status</Table.Th>
                                            <Table.Th>Usage</Table.Th>
                                            <Table.Th>Actions</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {apiKeys.map((apiKey) => (
                                            <Table.Tr key={apiKey.key_id}>
                                                <Table.Td>
                                                    <div>
                                                        <Text fw={500}>{apiKey.name}</Text>
                                                        <Text size="xs" c="dimmed">
                                                            {apiKey.description}
                                                        </Text>
                                                    </div>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Group gap={4}>
                                                        {apiKey.scopes.slice(0, 2).map((scope) => (
                                                            <Badge key={scope} size="xs" variant="light">
                                                                {scope}
                                                            </Badge>
                                                        ))}
                                                        {apiKey.scopes.length > 2 && (
                                                            <Badge size="xs" variant="light">
                                                                +{apiKey.scopes.length - 2}
                                                            </Badge>
                                                        )}
                                                    </Group>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Badge color={apiKey.is_active ? 'green' : 'gray'} size="sm">
                                                        {apiKey.is_active ? 'Active' : 'Revoked'}
                                                    </Badge>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Text size="sm">{apiKey.total_requests.toLocaleString()} requests</Text>
                                                </Table.Td>
                                                <Table.Td>
                                                    <Group gap="xs">
                                                        {apiKey.is_active && (
                                                            <Button
                                                                size="xs"
                                                                variant="light"
                                                                color="orange"
                                                                onClick={() => revokeApiKeyMutation.mutate(apiKey.key_id)}
                                                            >
                                                                Revoke
                                                            </Button>
                                                        )}
                                                        <ActionIcon
                                                            variant="light"
                                                            color="red"
                                                            onClick={() => deleteApiKeyMutation.mutate(apiKey.key_id)}
                                                        >
                                                            <IconTrash size={16} />
                                                        </ActionIcon>
                                                    </Group>
                                                </Table.Td>
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            )}
                        </Stack>
                    </Tabs.Panel>
                </Tabs>
            </Stack>

            {/* Create Integration Modal */}
            <Modal
                opened={createIntegrationOpened}
                onClose={() => setCreateIntegrationOpened(false)}
                title="Add Integration"
                size="lg"
            >
                <Stack>
                    <Select
                        label="Integration Type"
                        placeholder="Select a service"
                        data={Object.entries(integrationConfigs).map(([key, config]) => ({
                            value: key,
                            label: config.name,
                        }))}
                        value={newIntegrationType}
                        onChange={(value) => setNewIntegrationType(value as IntegrationType)}
                    />

                    {newIntegrationType && (
                        <>
                            <Alert icon={<IconAlertCircle size={16} />} color="blue">
                                {integrationConfigs[newIntegrationType].description}
                            </Alert>

                            <TextInput
                                label="Display Name"
                                placeholder="e.g., My QuickBooks Account"
                                value={newIntegrationName}
                                onChange={(e) => setNewIntegrationName(e.currentTarget.value)}
                            />
                        </>
                    )}

                    <Group justify="flex-end" mt="md">
                        <Button variant="subtle" onClick={() => setCreateIntegrationOpened(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={() => createIntegrationMutation.mutate()}
                            loading={createIntegrationMutation.isPending}
                            disabled={!newIntegrationType || !newIntegrationName}
                        >
                            Create Integration
                        </Button>
                    </Group>
                </Stack>
            </Modal>

            {/* Connect Integration Modal */}
            <Modal
                opened={connectModalOpened}
                onClose={() => setConnectModalOpened(false)}
                title="Connect Integration"
            >
                <Stack>
                    <Alert icon={<IconAlertCircle size={16} />} color="blue">
                        Enter your{' '}
                        {selectedIntegration &&
                            integrationConfigs[selectedIntegration.integration_type].name}{' '}
                        credentials to connect.
                    </Alert>

                    <Textarea
                        label="Credentials (JSON)"
                        placeholder='{"api_key": "sk_test_..."}'
                        value={connectionCredentials}
                        onChange={(e) => setConnectionCredentials(e.currentTarget.value)}
                        rows={4}
                    />

                    <Group justify="flex-end" mt="md">
                        <Button variant="subtle" onClick={() => setConnectModalOpened(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={() => connectIntegrationMutation.mutate()}
                            loading={connectIntegrationMutation.isPending}
                        >
                            Connect
                        </Button>
                    </Group>
                </Stack>
            </Modal>

            {/* Create Webhook Modal */}
            <Modal
                opened={createWebhookOpened}
                onClose={() => {
                    setCreateWebhookOpened(false)
                    setCreatedWebhookSecret('')
                }}
                title="Create Webhook"
                size="lg"
            >
                <Stack>
                    {createdWebhookSecret ? (
                        <>
                            <Alert icon={<IconCheck size={16} />} color="green" title="Webhook Created">
                                Save this secret - it won't be shown again!
                            </Alert>

                            <TextInput
                                label="Webhook Secret"
                                value={createdWebhookSecret}
                                readOnly
                                rightSection={
                                    <CopyButton value={createdWebhookSecret}>
                                        {({ copied, copy }) => (
                                            <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                            </ActionIcon>
                                        )}
                                    </CopyButton>
                                }
                            />

                            <Button onClick={() => {
                                setCreateWebhookOpened(false)
                                setCreatedWebhookSecret('')
                            }}>
                                Done
                            </Button>
                        </>
                    ) : (
                        <>
                            <Select
                                label="Integration"
                                placeholder="Select integration"
                                data={integrations
                                    .filter((i) => i.status === 'active')
                                    .map((i) => ({
                                        value: i.integration_id,
                                        label: i.display_name,
                                    }))}
                                value={webhookIntegrationId}
                                onChange={(value) => setWebhookIntegrationId(value || '')}
                            />

                            <TextInput
                                label="Webhook URL"
                                placeholder="https://your-api.com/webhooks/dyocense"
                                value={webhookUrl}
                                onChange={(e) => setWebhookUrl(e.currentTarget.value)}
                            />

                            <MultiSelect
                                label="Events"
                                placeholder="Select events to subscribe to"
                                data={[
                                    { value: 'invoice.created', label: 'Invoice Created' },
                                    { value: 'invoice.paid', label: 'Invoice Paid' },
                                    { value: 'payment.received', label: 'Payment Received' },
                                    { value: 'customer.created', label: 'Customer Created' },
                                    { value: 'order.created', label: 'Order Created' },
                                    { value: 'product.updated', label: 'Product Updated' },
                                ]}
                                value={webhookEvents}
                                onChange={setWebhookEvents}
                            />

                            <Group justify="flex-end" mt="md">
                                <Button variant="subtle" onClick={() => setCreateWebhookOpened(false)}>
                                    Cancel
                                </Button>
                                <Button
                                    onClick={() => createWebhookMutation.mutate()}
                                    loading={createWebhookMutation.isPending}
                                    disabled={!webhookIntegrationId || !webhookUrl || webhookEvents.length === 0}
                                >
                                    Create Webhook
                                </Button>
                            </Group>
                        </>
                    )}
                </Stack>
            </Modal>

            {/* Create API Key Modal */}
            <Modal
                opened={createApiKeyOpened}
                onClose={() => {
                    setCreateApiKeyOpened(false)
                    setCreatedApiKey('')
                }}
                title="Generate API Key"
                size="lg"
            >
                <Stack>
                    {createdApiKey ? (
                        <>
                            <Alert icon={<IconCheck size={16} />} color="green" title="API Key Created">
                                Save this key securely - it won't be shown again!
                            </Alert>

                            <TextInput
                                label="API Key"
                                value={createdApiKey}
                                readOnly
                                rightSection={
                                    <CopyButton value={createdApiKey}>
                                        {({ copied, copy }) => (
                                            <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                            </ActionIcon>
                                        )}
                                    </CopyButton>
                                }
                            />

                            <Button onClick={() => {
                                setCreateApiKeyOpened(false)
                                setCreatedApiKey('')
                            }}>
                                Done
                            </Button>
                        </>
                    ) : (
                        <>
                            <TextInput
                                label="Name"
                                placeholder="e.g., Production API Key"
                                value={apiKeyName}
                                onChange={(e) => setApiKeyName(e.currentTarget.value)}
                            />

                            <Textarea
                                label="Description"
                                placeholder="What will this key be used for?"
                                value={apiKeyDescription}
                                onChange={(e) => setApiKeyDescription(e.currentTarget.value)}
                                rows={3}
                            />

                            <MultiSelect
                                label="Scopes"
                                placeholder="Select permissions"
                                data={[
                                    { value: 'read:metrics', label: 'Read Metrics' },
                                    { value: 'write:goals', label: 'Write Goals' },
                                    { value: 'write:tasks', label: 'Write Tasks' },
                                    { value: 'read:reports', label: 'Read Reports' },
                                    { value: 'read:forecasts', label: 'Read Forecasts' },
                                ]}
                                value={apiKeyScopes}
                                onChange={setApiKeyScopes}
                            />

                            <TextInput
                                label="Expires In (days)"
                                placeholder="Leave empty for no expiration"
                                type="number"
                                value={apiKeyExpireDays}
                                onChange={(e) => setApiKeyExpireDays(e.currentTarget.value)}
                            />

                            <Group justify="flex-end" mt="md">
                                <Button variant="subtle" onClick={() => setCreateApiKeyOpened(false)}>
                                    Cancel
                                </Button>
                                <Button
                                    onClick={() => createApiKeyMutation.mutate()}
                                    loading={createApiKeyMutation.isPending}
                                    disabled={!apiKeyName || !apiKeyDescription || apiKeyScopes.length === 0}
                                >
                                    Generate Key
                                </Button>
                            </Group>
                        </>
                    )}
                </Stack>
            </Modal>
        </Container>
    )
}
