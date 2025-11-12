import {
    Alert,
    Badge,
    Button,
    Card,
    FileButton,
    Grid,
    Group,
    Loader,
    Modal,
    Select,
    Stack,
    Switch,
    Text,
    Textarea,
    TextInput,
    Title
} from '@mantine/core'
import { showNotification } from '@mantine/notifications'
import { IconUpload, IconX } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import React from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { useConnectorsQuery } from '../hooks/useConnectors'
import {
    createConnector,
    deleteConnector,
    getConnectorRecommendations,
    testConnector,
    updateConnector,
    uploadCSV,
    type ConnectorRecommendation,
    type ConnectorTestResponse,
    type TenantConnector
} from '../lib/api'
import { useAuthStore } from '../stores/auth'

type ConnectorField = {
    name: string
    label: string
    placeholder?: string
    type?: 'text' | 'textarea' | 'file'
    helper?: string
    accept?: string
}

type ConnectorFormValues = {
    displayName: string
    syncFrequency: 'manual' | 'daily' | 'weekly'
    file_url?: string
    schedule?: string
    folder_id?: string
    service_account_json?: string
    store_url?: string
    api_key?: string
    api_secret?: string
    api_url?: string
    uploaded_file?: File
    enable_mcp?: boolean
}

type ConnectorPreset = ConnectorRecommendation

const FALLBACK_PRESETS: ConnectorPreset[] = [
    {
        id: 'csv_upload',
        label: 'CSV/Excel Upload',
        description: 'Upload a CSV or Excel file from your device, or provide a URL to fetch data automatically.',
        icon: '📊',
        category: 'files',
        priority: 1,
        reason: 'Quick start - upload your existing spreadsheets',
        fields: [
            {
                name: 'uploaded_file',
                label: 'Upload file',
                type: 'file',
                accept: '.csv,.xlsx,.xls',
                helper: 'Select a CSV or Excel file from your computer'
            },
            {
                name: 'file_url',
                label: 'Or provide a URL (optional)',
                placeholder: 'https://example.com/export.csv',
                helper: 'If you have a hosted file that updates regularly'
            },
        ],
    },
]

export default function Connectors() {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const queryClient = useQueryClient()
    const [modalOpen, setModalOpen] = React.useState(false)
    const [presetId, setPresetId] = React.useState(FALLBACK_PRESETS[0].id)
    const [editingConnector, setEditingConnector] = React.useState<TenantConnector | null>(null)
    const form = useForm<ConnectorFormValues>({
        defaultValues: {
            displayName: '',
            syncFrequency: 'manual',
            enable_mcp: false,
        },
    })

    // Fetch dynamic recommendations based on business profile and data
    const recommendationsQuery = useQuery({
        queryKey: ['connector-recommendations', tenantId],
        queryFn: () => getConnectorRecommendations(apiToken, tenantId),
        enabled: !!apiToken && !!tenantId,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    })

    const presets = recommendationsQuery.data?.recommendations ?? FALLBACK_PRESETS
    const businessProfile = recommendationsQuery.data?.business_profile
    const dataStatus = recommendationsQuery.data?.data_status

    const resetForm = React.useCallback(
        (preset: ConnectorPreset, connector?: TenantConnector | null) => {
            const defaults: ConnectorFormValues = {
                displayName: connector?.display_name ?? '',
                syncFrequency: (connector?.sync_frequency as ConnectorFormValues['syncFrequency']) ?? 'manual',
                enable_mcp: Boolean(connector?.metadata?.mcp_enabled),
            }
            preset.fields.forEach((field) => {
                (defaults as any)[field.name] = '' as never
            })
            form.reset(defaults)
        },
        [form],
    )

    const connectorsQuery = useConnectorsQuery(apiToken, tenantId)
    const selectedPreset = presets.find((preset) => preset.id === presetId) ?? presets[0]

    const openCreateModal = React.useCallback(() => {
        const preset = presets[0]
        setEditingConnector(null)
        setPresetId(preset.id)
        resetForm(preset)
        setModalOpen(true)
    }, [resetForm, presets])

    const openEditModal = React.useCallback(
        (connector: TenantConnector) => {
            const preset = presets.find((p) => p.id === connector.connector_type) ?? presets[0]
            setEditingConnector(connector)
            setPresetId(preset.id)
            resetForm(preset, connector)
            setModalOpen(true)
        },
        [resetForm, presets],
    )

    const createMutation = useMutation({
        mutationFn: async (values: ConnectorFormValues) => {
            if (!apiToken) throw new Error('Missing token')
            if (!tenantId) throw new Error('Missing tenant')
            const config: Record<string, unknown> = {}
            selectedPreset.fields.forEach((field) => {
                const value = (values as any)[field.name]
                // Skip file field from config - we'll handle it separately
                if (value && field.type !== 'file') config[field.name] = value
            })
            const connector = await createConnector(
                {
                    connector_type: selectedPreset.id,
                    display_name: values.displayName || selectedPreset.label,
                    config,
                    sync_frequency: values.syncFrequency,
                    enable_mcp: Boolean(values.enable_mcp),
                },
                apiToken,
                tenantId,
            )

            // If user uploaded a CSV file, send it to the upload endpoint
            if (values.uploaded_file && connector?.connector_id) {
                await uploadCSV(values.uploaded_file, connector.connector_id, apiToken, tenantId)
            }

            return connector
        },
        onSuccess: () => {
            showNotification({ title: 'Connector created', message: 'We will start syncing shortly.', color: 'green' })
            setModalOpen(false)
            setEditingConnector(null)
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
            queryClient.invalidateQueries({ queryKey: ['connector-recommendations', tenantId] })
        },
        onError: () => {
            showNotification({ title: 'Unable to create connector', message: 'Double-check credentials and try again.', color: 'red' })
        },
    })

    const deleteMutation = useMutation({
        mutationFn: async (connector: TenantConnector) => {
            if (!apiToken) throw new Error('Missing token')
            if (!tenantId) throw new Error('Missing tenant')
            await deleteConnector(connector.connector_id, apiToken, tenantId)
        },
        onSuccess: (_data, connector) => {
            showNotification({
                title: 'Connector removed',
                message: `${connector.display_name ?? connector.connector_name} disconnected.`,
                color: 'yellow',
            })
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
        },
        onError: () => {
            showNotification({ title: 'Unable to remove connector', message: 'Try again later.', color: 'red' })
        },
    })

    const updateMutation = useMutation({
        mutationFn: async ({ connector, values, preset }: { connector: TenantConnector; values: ConnectorFormValues; preset: ConnectorPreset }) => {
            if (!apiToken) throw new Error('Missing token')
            if (!tenantId) throw new Error('Missing tenant')
            const config: Record<string, unknown> = {}
            preset.fields.forEach((field) => {
                const value = (values as any)[field.name]
                // Skip file field from config - we'll handle it separately
                if (value && field.type !== 'file') config[field.name] = value
            })
            const result = await updateConnector(
                connector.connector_id,
                {
                    display_name: values.displayName || connector.display_name,
                    config: Object.keys(config).length > 0 ? config : undefined,
                    sync_frequency: values.syncFrequency,
                    enable_mcp: values.enable_mcp,
                },
                apiToken,
                tenantId,
            )

            // If user uploaded a new CSV file, send it to the upload endpoint
            if (values.uploaded_file && connector?.connector_id) {
                await uploadCSV(values.uploaded_file, connector.connector_id, apiToken, tenantId)
            }

            return result
        },
        onSuccess: (_resp, { connector }) => {
            showNotification({
                title: 'Connector updated',
                message: `${connector.display_name ?? connector.connector_name} will be revalidated.`,
                color: 'green',
            })
            setModalOpen(false)
            setEditingConnector(null)
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
            queryClient.invalidateQueries({ queryKey: ['connector-recommendations', tenantId] })
        },
        onError: (error) => {
            const detail = (error as any)?.body?.detail || (error as Error).message
            showNotification({ title: 'Update failed', message: detail, color: 'red' })
        },
    })

    const testMutation = useMutation<ConnectorTestResponse, any, TenantConnector>({
        mutationFn: async (connector: TenantConnector) => {
            if (!apiToken) throw new Error('Missing token')
            if (!tenantId) throw new Error('Missing tenant')
            return await testConnector(connector.connector_id, apiToken, tenantId)
        },
        onSuccess: (response, connector) => {
            const success = response?.success ?? false
            const title = success ? 'Connection successful' : 'Connection check failed'
            const message =
                response?.message ||
                (success
                    ? `${connector.display_name ?? connector.connector_name} responded successfully.`
                    : 'We could not verify the connector credentials.')
            showNotification({
                title,
                message,
                color: success ? 'green' : 'red',
            })
            if (success) {
                queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
            }
        },
        onError: (error) => {
            const detail =
                (error as any)?.body?.detail ||
                (error as Error)?.message ||
                'Unable to reach the connector.'
            showNotification({
                title: 'Test failed',
                message: detail,
                color: 'red',
            })
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
        }
    })

    const onSubmit = form.handleSubmit((values) => {
        if (editingConnector) {
            updateMutation.mutate({ connector: editingConnector, values, preset: selectedPreset })
        } else {
            createMutation.mutate(values)
        }
    })

    const connectors = connectorsQuery.data ?? []
    const isSaving = editingConnector ? updateMutation.isPending : createMutation.isPending

    return (
        <div className="page-shell">
            <div className="mx-auto w-full max-w-7xl">
                {/* Header */}
                <div className="glass-panel--light mb-6">
                    <Group justify="space-between" align="flex-start" wrap="nowrap">
                        <div style={{ flex: 1 }}>
                            <Group gap="sm" mb="sm" align="center">
                                <Text size="2rem">🔌</Text>
                                <Title order={2} className="text-gray-900">
                                    Data Connectors
                                </Title>
                            </Group>
                            <Text className="text-gray-600 mb-3" maw={700}>
                                <strong>Think of this as connecting your fitness tracker to your health app.</strong> Your business data flows in automatically,
                                updating your Business Health Score and powering personalized insights from your AI Coach.
                            </Text>
                            <Text className="text-gray-500" size="sm" maw={700}>
                                Start with CSV uploads or Google Drive for quick setup. Your connected data enables auto-tracking of goals,
                                real-time health metrics, and AI-powered recommendations.
                            </Text>

                            {/* Business Profile & Data Status Insights */}
                            {businessProfile && (
                                <Card mt="md" radius="lg" shadow="xs" className="border border-blue-100 bg-blue-50">
                                    <Group gap="sm">
                                        <Text size="sm" fw={600}>📊 Your Business Profile:</Text>
                                        {businessProfile.business_type && (
                                            <Badge size="sm" variant="light" color="blue">{businessProfile.business_type}</Badge>
                                        )}
                                        {businessProfile.industry && (
                                            <Badge size="sm" variant="light" color="cyan">{businessProfile.industry}</Badge>
                                        )}
                                        {businessProfile.team_size && (
                                            <Badge size="sm" variant="light" color="grape">Team: {businessProfile.team_size}</Badge>
                                        )}
                                    </Group>
                                    {dataStatus && (
                                        <Text size="xs" c="dimmed" mt="xs">
                                            Data connected: {' '}
                                            {dataStatus.has_orders && '✓ Orders '}
                                            {dataStatus.has_inventory && '✓ Inventory '}
                                            {dataStatus.has_customers && '✓ Customers '}
                                            {dataStatus.has_products && '✓ Products '}
                                            {!dataStatus.has_orders && !dataStatus.has_inventory && !dataStatus.has_customers && !dataStatus.has_products && 'None yet - add a connector to get started'}
                                        </Text>
                                    )}
                                </Card>
                            )}
                            <Card mt="lg" radius="lg" shadow="xs" className="border border-dashed border-purple-200">
                                <Group justify="space-between">
                                    <Text fw={600}>ERPNext + MCP docs</Text>
                                    <Button
                                        variant="outline"
                                        radius="xl"
                                        size="xs"
                                        component="a"
                                        target="_blank"
                                        rel="noreferrer"
                                        href="https://github.com/dyocense/dyocense/blob/main/docs/ERPNEXT_CONNECTOR_GUIDE.md"
                                    >
                                        View guide
                                    </Button>
                                </Group>
                                <Text size="sm" color="dimmed" mt="xs">
                                    Follow the ERPNext Connector Guide to configure API keys, enable plaintext credentials, and
                                    start the MCP server from the connectors backend (`CONNECTOR_ENABLE_ERP_MCP=1` + ERP_URL/ERP_KEY/ERP_SECRET).
                                </Text>
                                <Text size="xs" color="dimmed">
                                    Agents can then call tools such as “create document” or “check stock availability” once the MCP service is running.
                                </Text>
                            </Card>
                            <Group mt="md" gap="sm">
                                {connectors.length > 0 ? (
                                    <Badge size="lg" color="green" variant="light" leftSection="✓">
                                        {connectors.length} Connected
                                    </Badge>
                                ) : (
                                    <Badge size="lg" color="orange" variant="light" leftSection="⚠️">
                                        No data connected yet
                                    </Badge>
                                )}
                                <Button variant="subtle" size="sm" component={Link} to="/marketplace" leftSection={<span>🏪</span>}>
                                    Browse Marketplace
                                </Button>
                            </Group>
                        </div>
                        <Button
                            size="lg"
                            onClick={openCreateModal}
                        >
                            Add connector
                        </Button>
                    </Group>
                </div>

                {/* Main Content Grid */}
                <Grid gutter="lg">
                    {/* Connected Sources - Left */}
                    <Grid.Col span={{ base: 12, md: 6 }}>
                        <Card className="glass-panel--light h-full">
                            <Group justify="space-between" align="center" mb="md">
                                <Text fw={600} size="lg">Connected sources</Text>
                                <Button size="xs" variant="subtle" onClick={() => connectorsQuery.refetch?.()}>
                                    Refresh
                                </Button>
                            </Group>

                            <Text size="sm" c="dimmed" mb="md">
                                Connect your first data source to unlock real-time health tracking and personalized insights.
                            </Text>

                            {connectorsQuery.isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader />
                                </div>
                            ) : connectorsQuery.isError ? (
                                <Text size="sm" c="red">
                                    Unable to load connectors. Please try again.
                                </Text>
                            ) : connectors.length ? (
                                <Stack gap="sm">
                                    {connectors.map((connector) => (
                                        <Card key={connector.connector_id} withBorder p="md" radius="md">
                                            <Group justify="space-between" align="flex-start">
                                                <div style={{ flex: 1 }}>
                                                    <Group gap="xs" mb={4}>
                                                        <Text fw={600}>{connector.display_name ?? connector.connector_name}</Text>
                                                        <Badge
                                                            size="xs"
                                                            color={connector.status === 'active' ? 'green' : connector.status === 'error' ? 'red' : 'yellow'}
                                                        >
                                                            {connector.status}
                                                        </Badge>
                                                    </Group>
                                                    <Text size="xs" c="dimmed">
                                                        {connector.connector_type} · {connector.data_types.join(', ')}
                                                    </Text>
                                                    {connector.last_sync && (
                                                        <Text size="xs" c="gray.5">
                                                            Last sync: {new Date(connector.last_sync).toLocaleString()}
                                                        </Text>
                                                    )}
                                                    {connector.metadata?.error_message && (
                                                        <Text size="xs" c="red.4">
                                                            {connector.metadata.error_message}
                                                        </Text>
                                                    )}
                                                </div>
                                                <Badge color={connector.status === 'active' ? 'green' : connector.status === 'error' ? 'red' : 'yellow'} variant="light">
                                                    {connector.status}
                                                </Badge>
                                            </Group>
                                            <Group mt="sm">
                                                <Button
                                                    radius="xl"
                                                    size="xs"
                                                    variant="light"
                                                    loading={
                                                        testMutation.isPending &&
                                                        testMutation.variables?.connector_id === connector.connector_id
                                                    }
                                                    onClick={() => testMutation.mutate(connector)}
                                                >
                                                    Test connection
                                                </Button>
                                                {connector.metadata?.mcp_enabled && (
                                                    <Badge size="xs" color="blue" variant="light">MCP enabled</Badge>
                                                )}
                                                <Button
                                                    radius="xl"
                                                    size="xs"
                                                    variant="light"
                                                    color="blue"
                                                    onClick={() => openEditModal(connector)}
                                                >
                                                    Edit
                                                </Button>
                                                <Button
                                                    radius="xl"
                                                    size="xs"
                                                    variant="outline"
                                                    color="red"
                                                    loading={
                                                        deleteMutation.isPending &&
                                                        deleteMutation.variables?.connector_id === connector.connector_id
                                                    }
                                                    onClick={() => deleteMutation.mutate(connector)}
                                                >
                                                    Remove
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            ) : (
                                <Card withBorder p="lg" radius="md" className="border-2 border-dashed border-gray-300">
                                    <Stack align="center" gap="sm">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.1em' }}>
                                            QUICKSTART
                                        </Text>
                                        <Text size="sm" c="dimmed" ta="center">
                                            Upload your sales or inventory data to get started with actionable insights.
                                        </Text>
                                        <Button
                                            variant="light"
                                            onClick={openCreateModal}
                                        >
                                            ADD CONNECTOR
                                        </Button>
                                    </Stack>
                                </Card>
                            )}
                        </Card>
                    </Grid.Col>

                    {/* Recommended Starters - Right */}
                    <Grid.Col span={{ base: 12, md: 6 }}>
                        <Card className="glass-panel--light">
                            <Group justify="space-between" align="center" mb="md">
                                <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.25em' }}>
                                    {recommendationsQuery.isLoading ? 'LOADING RECOMMENDATIONS...' : 'RECOMMENDED FOR YOU'}
                                </Text>
                                {recommendationsQuery.isLoading && <Loader size="xs" />}
                            </Group>

                            {recommendationsQuery.isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader />
                                </div>
                            ) : (
                                <Stack gap="sm">
                                    {presets.map((preset) => (
                                        <Card key={preset.id} withBorder p="md" radius="md" className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => {
                                            setEditingConnector(null)
                                            setPresetId(preset.id)
                                            resetForm(preset)
                                            setModalOpen(true)
                                        }}>
                                            <Group justify="space-between" align="flex-start" mb="xs">
                                                <div style={{ flex: 1 }}>
                                                    <Group gap="xs" mb={4}>
                                                        <Text size="xl">{preset.icon}</Text>
                                                        <Badge size="xs" variant="dot" color="blue">
                                                            {preset.category.toUpperCase()}
                                                        </Badge>
                                                    </Group>
                                                    <Text fw={600} size="sm">{preset.label}</Text>
                                                    <Text size="xs" c="dimmed" lineClamp={2} mb="xs">
                                                        {preset.description}
                                                    </Text>
                                                    {preset.reason && (
                                                        <Badge size="sm" variant="light" color="violet" leftSection="💡">
                                                            {preset.reason}
                                                        </Badge>
                                                    )}
                                                </div>
                                            </Group>
                                            <Button size="xs" variant="light" fullWidth mt="sm">
                                                CONFIGURE
                                            </Button>
                                        </Card>
                                    ))}
                                </Stack>
                            )}
                        </Card>
                    </Grid.Col>
                </Grid>
            </div>

            <Modal
                opened={modalOpen}
                onClose={() => setModalOpen(false)}
                title={
                    <Group gap="xs">
                        <Text fw={600} size="lg">
                            {editingConnector ? 'Edit connector' : 'Add connector'}
                        </Text>
                    </Group>
                }
                size="xl"
                centered
                styles={{
                    body: { maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' },
                }}
            >
                <form onSubmit={onSubmit}>
                    <Stack gap="md">
                        {/* Connector Type Selection - Grid of Cards */}
                        <div>
                            <Text size="sm" fw={600} mb="sm">Select connector type</Text>
                            <Grid gutter="xs">
                                {presets.map((preset) => (
                                    <Grid.Col key={preset.id} span={6}>
                                        <Card
                                            padding="md"
                                            radius="md"
                                            withBorder
                                            style={{
                                                cursor: editingConnector ? 'not-allowed' : 'pointer',
                                                borderColor: presetId === preset.id ? 'var(--mantine-color-blue-6)' : undefined,
                                                borderWidth: presetId === preset.id ? 2 : 1,
                                                backgroundColor: presetId === preset.id ? 'var(--mantine-color-blue-0)' : undefined,
                                                opacity: editingConnector ? 0.6 : 1,
                                            }}
                                            onClick={() => {
                                                if (editingConnector) return
                                                setPresetId(preset.id)
                                                resetForm(preset, editingConnector)
                                            }}
                                        >
                                            <Group gap="sm" align="flex-start" wrap="nowrap">
                                                {preset.icon && (
                                                    <Text size="xl" style={{ lineHeight: 1 }}>
                                                        {preset.icon}
                                                    </Text>
                                                )}
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <Text size="sm" fw={600} lineClamp={1}>
                                                        {preset.label}
                                                    </Text>
                                                    <Text size="xs" c="dimmed" lineClamp={2} mt={4}>
                                                        {preset.description}
                                                    </Text>
                                                </div>
                                            </Group>
                                        </Card>
                                    </Grid.Col>
                                ))}
                            </Grid>
                            {editingConnector && (
                                <Text size="xs" c="dimmed" mt="xs">
                                    Connector type cannot be changed after creation. Re-enter credentials below to update settings.
                                </Text>
                            )}
                        </div>

                        {/* Display Name */}
                        <TextInput
                            label="Display name (optional)"
                            placeholder={`My ${selectedPreset.label}`}
                            description="Give this connection a friendly name"
                            {...form.register('displayName')}
                        />

                        {/* Sync Frequency */}
                        <Select
                            label="Sync frequency"
                            description="How often should we check for updates?"
                            data={[
                                { value: 'manual', label: 'Manual - Sync when triggered' },
                                { value: 'daily', label: 'Daily - Once per day' },
                                { value: 'weekly', label: 'Weekly - Once per week' },
                            ]}
                            {...form.register('syncFrequency')}
                            value={form.watch('syncFrequency')}
                            onChange={(value) => form.setValue('syncFrequency', (value as ConnectorFormValues['syncFrequency']) ?? 'manual')}
                        />

                        {editingConnector && (
                            <Alert color="yellow" title="Re-enter credentials" radius="md">
                                For security, saved credentials are hidden. Please re-enter any keys or URLs you want to update for{' '}
                                {editingConnector.display_name ?? editingConnector.connector_name}.
                            </Alert>
                        )}

                        {/* Dynamic Fields */}
                        {selectedPreset.fields.map((field) =>
                            field.type === 'file' ? (
                                <div key={field.name}>
                                    <Text size="sm" fw={600} mb="xs">
                                        {field.label}
                                    </Text>
                                    <FileButton
                                        accept={field.accept}
                                        onChange={(file) => form.setValue('uploaded_file', file ?? undefined)}
                                    >
                                        {(props) => (
                                            <Button
                                                {...props}
                                                variant="light"
                                                fullWidth
                                                leftSection={<IconUpload size={16} />}
                                                rightSection={
                                                    form.watch('uploaded_file') ? (
                                                        <IconX
                                                            size={16}
                                                            style={{ cursor: 'pointer' }}
                                                            onClick={(e) => {
                                                                e.stopPropagation()
                                                                form.setValue('uploaded_file', undefined)
                                                            }}
                                                        />
                                                    ) : null
                                                }
                                            >
                                                {form.watch('uploaded_file')?.name || 'Choose file'}
                                            </Button>
                                        )}
                                    </FileButton>
                                    {field.helper && (
                                        <Text size="xs" c="dimmed" mt="xs">
                                            {field.helper}
                                        </Text>
                                    )}
                                </div>
                            ) : field.type === 'textarea' ? (
                                <Textarea
                                    key={field.name}
                                    label={field.label}
                                    placeholder={field.placeholder}
                                    description={field.helper}
                                    minRows={3}
                                    {...form.register(field.name as any)}
                                />
                            ) : (
                                <TextInput
                                    key={field.name}
                                    label={field.label}
                                    placeholder={field.placeholder}
                                    description={field.helper}
                                    {...form.register(field.name as any)}
                                />
                            ),
                        )}

                        {/* MCP Toggle */}
                        <Switch
                            label="Enable MCP tools for this connector"
                            description="Start a background MCP server so AI agents can call ERP and CSV tools in-context."
                            checked={Boolean(form.watch('enable_mcp'))}
                            onChange={(e) => form.setValue('enable_mcp', e.currentTarget.checked)}
                        />

                        {/* Action Buttons */}
                        <Group justify="space-between" mt="lg">
                            <Button type="button" variant="subtle" onClick={() => setModalOpen(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" loading={isSaving}>
                                {editingConnector ? (isSaving ? 'Saving…' : 'Save changes') : isSaving ? 'Connecting…' : 'Connect'}
                            </Button>
                        </Group>
                    </Stack>
                </form>
            </Modal>
        </div >
    )
}
