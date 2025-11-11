import {
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
    Text,
    Textarea,
    TextInput,
    Title
} from '@mantine/core'
import { showNotification } from '@mantine/notifications'
import { IconUpload, IconX } from '@tabler/icons-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import React from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { createConnector, deleteConnector, testConnector, type ConnectorTestResponse, type TenantConnector } from '../lib/api'
import { useAuthStore } from '../stores/auth'

type ConnectorField = {
    name: keyof ConnectorFormValues
    label: string
    placeholder?: string
    type?: 'text' | 'textarea' | 'file'
    helper?: string
    accept?: string
}

type ConnectorPreset = {
    id: string
    label: string
    description: string
    fields: ConnectorField[]
    icon?: string
    category?: 'files' | 'ecommerce' | 'erp' | 'cloud'
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
}

const presets: ConnectorPreset[] = [
    {
        id: 'csv_upload',
        label: 'CSV/Excel Upload',
        description: 'Upload a CSV or Excel file from your device, or provide a URL to fetch data automatically.',
        icon: '📊',
        category: 'files',
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
    {
        id: 'google-drive',
        label: 'Google Drive',
        description: 'Bring in spreadsheets from a shared Drive folder.',
        icon: '📁',
        category: 'cloud',
        fields: [
            { name: 'folder_id', label: 'Folder ID', placeholder: 'e.g. 1AbCDriveFolderID' },
            {
                name: 'service_account_json',
                label: 'Service account JSON',
                type: 'textarea',
                placeholder: '{ "type": "service_account", ... }',
                helper: 'Create a Google Cloud service account and share the folder with it.',
            },
        ],
    },
    {
        id: 'shopify',
        label: 'Shopify',
        description: 'Connect your Shopify storefront for orders, carts, and customers.',
        icon: '🛍️',
        category: 'ecommerce',
        fields: [
            { name: 'store_url', label: 'Store URL', placeholder: 'https://yourstore.myshopify.com' },
            { name: 'api_key', label: 'Admin API access token', type: 'textarea' },
        ],
    },
    {
        id: 'grandnode',
        label: 'GrandNode',
        description: 'Sync sales and catalog data from your GrandNode shop.',
        icon: '🛒',
        category: 'ecommerce',
        fields: [
            { name: 'store_url', label: 'Store URL', placeholder: 'https://shop.example.com' },
            { name: 'api_key', label: 'API key', type: 'text' },
        ],
    },
    {
        id: 'erpnext',
        label: 'ERPNext',
        description: 'Connect your ERPNext ERP system to sync inventory, sales orders, and supplier data automatically.',
        icon: '⚙️',
        category: 'erp',
        fields: [
            {
                name: 'api_url',
                label: 'ERPNext URL',
                placeholder: 'https://erp.example.com',
                helper: 'Your ERPNext instance URL (e.g., https://erp.yourcompany.com)'
            },
            {
                name: 'api_key',
                label: 'API Key',
                type: 'text',
                helper: 'Found in User Settings → API Access after generating keys'
            },
            {
                name: 'api_secret',
                label: 'API Secret',
                type: 'textarea',
                helper: '⚠️ Copy this immediately when generating keys - it\'s only shown once! Go to: User → Settings → API Access → Generate Keys'
            },
        ],
    },
]

export default function Connectors() {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const queryClient = useQueryClient()
    const [modalOpen, setModalOpen] = React.useState(false)
    const [presetId, setPresetId] = React.useState(presets[0].id)
    const connectorsQuery = useConnectorsQuery(apiToken, tenantId)
    const selectedPreset = presets.find((preset) => preset.id === presetId) ?? presets[0]

    const form = useForm<ConnectorFormValues>({
        defaultValues: {
            displayName: '',
            syncFrequency: 'manual',
        },
    })

    const resetForm = React.useCallback(
        (preset: ConnectorPreset) => {
            const defaults: ConnectorFormValues = {
                displayName: '',
                syncFrequency: 'manual',
            }
            preset.fields.forEach((field) => {
                defaults[field.name] = '' as never
            })
            form.reset(defaults)
        },
        [form],
    )

    const createMutation = useMutation({
        mutationFn: async (values: ConnectorFormValues) => {
            if (!apiToken) throw new Error('Missing token')
            if (!tenantId) throw new Error('Missing tenant')
            const config: Record<string, unknown> = {}
            selectedPreset.fields.forEach((field) => {
                const value = values[field.name]
                if (value) config[field.name] = value
            })
            return await createConnector(
                {
                    connector_type: selectedPreset.id,
                    display_name: values.displayName || selectedPreset.label,
                    config,
                    sync_frequency: values.syncFrequency,
                },
                apiToken,
                tenantId,
            )
        },
        onSuccess: () => {
            showNotification({ title: 'Connector created', message: 'We will start syncing shortly.', color: 'green' })
            setModalOpen(false)
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
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

    const onSubmit = form.handleSubmit((values) => createMutation.mutate(values))

    const connectors = connectorsQuery.data ?? []

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
                            onClick={() => {
                                resetForm(selectedPreset)
                                setModalOpen(true)
                            }}
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
                                                    loading={testMutation.isPending && testMutation.variables === connector}
                                                    onClick={() => testMutation.mutate(connector)}
                                                >
                                                    Test connection
                                                </Button>
                                                <Button
                                                    radius="xl"
                                                    size="xs"
                                                    variant="outline"
                                                    color="red"
                                                    loading={deleteMutation.isPending && deleteMutation.variables === connector}
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
                                            onClick={() => {
                                                const preset = presets[0]
                                                setPresetId(preset.id)
                                                resetForm(preset)
                                                setModalOpen(true)
                                            }}
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
                            <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.25em' }} mb="md">
                                RECOMMENDED STARTERS
                            </Text>
                            <Stack gap="sm">
                                {presets.map((preset) => (
                                    <Card key={preset.id} withBorder p="md" radius="md" className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => {
                                        setPresetId(preset.id)
                                        resetForm(preset)
                                        setModalOpen(true)
                                    }}>
                                        <Group justify="space-between" align="flex-start" mb="xs">
                                            <div style={{ flex: 1 }}>
                                                <Group gap="xs" mb={4}>
                                                    <Badge size="xs" variant="dot">CONNECTOR</Badge>
                                                </Group>
                                                <Text fw={600} size="sm">{preset.label}</Text>
                                                <Text size="xs" c="dimmed" lineClamp={2}>
                                                    {preset.description}
                                                </Text>
                                            </div>
                                        </Group>
                                        <Button size="xs" variant="light" fullWidth mt="sm">
                                            CONFIGURE
                                        </Button>
                                    </Card>
                                ))}
                            </Stack>
                        </Card>
                    </Grid.Col>
                </Grid>
            </div>

            <Modal
                opened={modalOpen}
                onClose={() => setModalOpen(false)}
                title={
                    <Group gap="xs">
                        <Text fw={600} size="lg">Add connector</Text>
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
                                                cursor: 'pointer',
                                                borderColor: presetId === preset.id ? 'var(--mantine-color-blue-6)' : undefined,
                                                borderWidth: presetId === preset.id ? 2 : 1,
                                                backgroundColor: presetId === preset.id ? 'var(--mantine-color-blue-0)' : undefined,
                                            }}
                                            onClick={() => {
                                                setPresetId(preset.id)
                                                resetForm(preset)
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
                                    {...form.register(field.name)}
                                />
                            ) : (
                                <TextInput
                                    key={field.name}
                                    label={field.label}
                                    placeholder={field.placeholder}
                                    description={field.helper}
                                    {...form.register(field.name)}
                                />
                            ),
                        )}

                        {/* Action Buttons */}
                        <Group justify="space-between" mt="lg">
                            <Button type="button" variant="subtle" onClick={() => setModalOpen(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" loading={createMutation.isPending}>
                                {createMutation.isPending ? 'Connecting…' : 'Connect'}
                            </Button>
                        </Group>
                    </Stack>
                </form>
            </Modal>
        </div>
    )
}
