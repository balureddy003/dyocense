import {
    Badge,
    Button,
    Card,
    Grid,
    Group,
    Loader,
    Modal,
    SegmentedControl,
    Select,
    Stack,
    Text,
    Textarea,
    TextInput,
    Title,
} from '@mantine/core'
import { showNotification } from '@mantine/notifications'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import React from 'react'
import { useForm } from 'react-hook-form'
import AgentActionCard from '../components/AgentActionCard'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { createConnector, deleteConnector, testConnector, type TenantConnector } from '../lib/api'
import { useAuthStore } from '../stores/auth'

type ConnectorField = {
    name: keyof ConnectorFormValues
    label: string
    placeholder?: string
    type?: 'text' | 'textarea'
    helper?: string
}

type ConnectorPreset = {
    id: string
    label: string
    description: string
    fields: ConnectorField[]
}

type ConnectorFormValues = {
    displayName: string
    syncFrequency: 'manual' | 'daily' | 'weekly'
    file_url?: string
    schedule?: string
    folder_id?: string
    service_account_json?: string
}

const presets: ConnectorPreset[] = [
    {
        id: 'csv_upload',
        label: 'CSV Upload',
        description: 'Point at a hosted CSV export that Dyocense ingests on a schedule.',
        fields: [
            { name: 'file_url', label: 'CSV URL', placeholder: 'https://example.com/export.csv' },
            { name: 'schedule', label: 'Sync cadence (optional)', placeholder: 'weekly' },
        ],
    },
    {
        id: 'google-drive',
        label: 'Google Drive',
        description: 'Bring in spreadsheets from a shared Drive folder.',
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
        fields: [
            { name: 'store_url', label: 'Store URL', placeholder: 'https://yourstore.myshopify.com' },
            { name: 'api_key', label: 'Admin API access token', type: 'textarea' },
        ],
    },
    {
        id: 'grandnode',
        label: 'GrandNode',
        description: 'Sync sales and catalog data from your GrandNode shop.',
        fields: [
            { name: 'store_url', label: 'Store URL', placeholder: 'https://shop.example.com' },
            { name: 'api_key', label: 'API key', type: 'text' },
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
            await deleteConnector(connector.connector_id, apiToken)
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

    const testMutation = useMutation({
        mutationFn: async (connector: TenantConnector) => {
            if (!apiToken) throw new Error('Missing token')
            return await testConnector(connector.connector_id, apiToken)
        },
        onSuccess: (_response, connector) => {
            showNotification({
                title: 'Test started',
                message: `Checking ${connector.display_name ?? connector.connector_name}.`,
                color: 'green',
            })
            queryClient.invalidateQueries({ queryKey: ['connectors', tenantId] })
        },
        onError: () => {
            showNotification({ title: 'Test failed', message: 'Unable to reach the connector.', color: 'red' })
        },
    })

    const onSubmit = form.handleSubmit((values) => createMutation.mutate(values))

    const connectors = connectorsQuery.data ?? []

    return (
        <div className="mx-auto w-full max-w-6xl rounded-3xl border border-white/10 bg-night-800/80 px-4 py-8 shadow-card md:px-8">
            <Group justify="space-between" align="flex-start" mb="xl">
                <div>
                    <Text size="xs" fw={600} tt="uppercase" c="blue.3" style={{ letterSpacing: '0.25em' }}>
                        Data connectors
                    </Text>
                    <Title order={2} c="white">
                        Remove mocks—stream real SMB data into the copilot
                    </Title>
                    <Text c="gray.4" maw={560}>
                        Start with lightweight connectors like CSV uploads or Google Drive folders. Once connected, Planner, Agents, and Executor use the same live metrics the business trusts.
                    </Text>
                    <Group mt="md" gap="sm">
                        <Badge size="lg" color="blue" variant="light">
                            {connectors.length} Connected
                        </Badge>
                        <Link to="/marketplace">
                            <Button variant="subtle" size="sm" leftSection={<span>🏪</span>}>
                                Browse Marketplace
                            </Button>
                        </Link>
                    </Group>
                </div>
                <Button
                    radius="xl"
                    onClick={() => {
                        resetForm(selectedPreset)
                        setModalOpen(true)
                    }}
                >
                    Add connector
                </Button>
            </Group>

            <Grid gutter="xl">
                <Grid.Col span={{ base: 12, md: 7 }}>
                    <Card radius="xl" withBorder className="bg-night-900/70">
                        <Group justify="space-between" align="center" mb="md">
                            <Title order={4}>Connected sources</Title>
                            <Button radius="xl" size="xs" variant="subtle" onClick={() => connectorsQuery.refetch?.()}>
                                Refresh
                            </Button>
                        </Group>
                        {connectorsQuery.isLoading ? (
                            <Loader />
                        ) : connectorsQuery.isError ? (
                            <Text size="sm" c="red.4">
                                Unable to load connectors. Check the kernel or try again.
                            </Text>
                        ) : connectors.length ? (
                            <Stack gap="sm">
                                {connectors.map((connector) => (
                                    <Card key={connector.connector_id} radius="lg" withBorder className="bg-night-900/40">
                                        <Group justify="space-between" align="flex-start">
                                            <div>
                                                <Text fw={600}>{connector.display_name ?? connector.connector_name}</Text>
                                                <Text size="xs" c="gray.4">
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
                            <Stack gap="sm">
                                <Text size="sm" c="gray.4">
                                    No connectors yet. Hook up at least one data source so Dyocense can replace the mock data.
                                </Text>
                                <AgentActionCard
                                    label="Connect CSV export"
                                    description="Upload your daily sales or inventory exports to start planning with real numbers."
                                    badge="Starter"
                                    cta="Add connector"
                                    onSelect={() => {
                                        const preset = presets[0]
                                        setPresetId(preset.id)
                                        resetForm(preset)
                                        setModalOpen(true)
                                    }}
                                />
                            </Stack>
                        )}
                    </Card>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 5 }}>
                    <Card radius="xl" withBorder className="bg-night-900/60">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                            Recommended starters
                        </Text>
                        <Stack gap="sm" mt="md">
                            {presets.map((preset) => (
                                <AgentActionCard
                                    key={preset.id}
                                    label={preset.label}
                                    description={preset.description}
                                    badge="Connector"
                                    cta="Configure"
                                    onSelect={() => {
                                        setPresetId(preset.id)
                                        resetForm(preset)
                                        setModalOpen(true)
                                    }}
                                />
                            ))}
                        </Stack>
                    </Card>
                </Grid.Col>
            </Grid>

            <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title="Add connector" centered>
                <form onSubmit={onSubmit} className="space-y-4">
                    <SegmentedControl
                        fullWidth
                        value={presetId}
                        onChange={(value) => {
                            setPresetId(value)
                            const preset = presets.find((item) => item.id === value) ?? presets[0]
                            resetForm(preset)
                        }}
                        data={presets.map((preset) => ({ label: preset.label, value: preset.id }))}
                    />
                    <TextInput
                        label="Display name"
                        placeholder={selectedPreset.label}
                        {...form.register('displayName')}
                    />
                    <Select
                        label="Sync frequency"
                        data={[
                            { value: 'manual', label: 'Manual' },
                            { value: 'daily', label: 'Daily' },
                            { value: 'weekly', label: 'Weekly' },
                        ]}
                        {...form.register('syncFrequency')}
                        value={form.watch('syncFrequency')}
                        onChange={(value) => form.setValue('syncFrequency', (value as ConnectorFormValues['syncFrequency']) ?? 'manual')}
                    />
                    {selectedPreset.fields.map((field) =>
                        field.type === 'textarea' ? (
                            <Textarea
                                key={field.name}
                                label={field.label}
                                placeholder={field.placeholder}
                                minRows={4}
                                {...form.register(field.name)}
                            />
                        ) : (
                            <TextInput
                                key={field.name}
                                label={field.label}
                                placeholder={field.placeholder}
                                {...form.register(field.name)}
                            />
                        ),
                    )}
                    {selectedPreset.fields.map(
                        (field) =>
                            field.helper && (
                                <Text key={`${field.name}-helper`} size="xs" c="gray.5">
                                    {field.helper}
                                </Text>
                            ),
                    )}
                    <Group justify="space-between">
                        <Button type="button" variant="subtle" onClick={() => setModalOpen(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" loading={createMutation.isPending} radius="xl">
                            {createMutation.isPending ? 'Connecting…' : 'Connect'}
                        </Button>
                    </Group>
                </form>
            </Modal>
        </div>
    )
}
