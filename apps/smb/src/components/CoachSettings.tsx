import { Badge, Button, Checkbox, FileButton, Group, Modal, MultiSelect, Paper, ScrollArea, Select, Stack, Switch, Text } from '@mantine/core';
import { IconFileUpload, IconSettings, IconX } from '@tabler/icons-react';
import { useMemo, useState } from 'react';



interface CoachPersona {
    id: string
    name: string
    emoji: string
    description: string
    expertise: string[]
    tone: string
}

interface DataSource {
    id: string
    name: string
    connector: string
    record_count: number
    available: boolean
}

interface CoachSettingsProps {
    opened: boolean
    onClose: () => void
    selectedPersona: string
    onPersonaChange: (personaId: string) => void
    selectedDataSources: string[]
    onDataSourcesChange: (sources: string[]) => void
    includeEvidence: boolean
    onIncludeEvidenceChange: (value: boolean) => void
    includeForecast: boolean
    onIncludeForecastChange: (value: boolean) => void
    personas: CoachPersona[]
    dataSources: DataSource[]
    onFileUpload?: (file: File) => void
    uploadedFiles?: { name: string; size: number; uploadedAt: Date }[]
}

// Simplified, SMB-friendly settings UI

export function CoachSettings({
    opened,
    onClose,
    selectedPersona,
    onPersonaChange,
    selectedDataSources,
    onDataSourcesChange,
    includeEvidence,
    onIncludeEvidenceChange,
    includeForecast,
    onIncludeForecastChange,
    personas,
    dataSources,
    onFileUpload,
    uploadedFiles = [],
}: CoachSettingsProps) {
    const [file, setFile] = useState<File | null>(null)
    const [streamingMode, setStreamingMode] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.streamingMode')
            return v ? v === 'true' : true
        } catch {
            return true
        }
    })
    const [showAgentLabels, setShowAgentLabels] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.showAgentLabels')
            return v ? v === 'true' : true
        } catch {
            return true
        }
    })
    const [showAdvanced, setShowAdvanced] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.showAdvanced')
            return v ? v === 'true' : false
        } catch {
            return false
        }
    })

    const [preset, setPreset] = useState<string>(() => {
        try {
            return localStorage.getItem('coach.preset') || 'balanced'
        } catch {
            return 'balanced'
        }
    })

    const [requireReview, setRequireReview] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.requireReview')
            return v ? v === 'true' : false
        } catch {
            return false
        }
    })

    const [guardrailLevel, setGuardrailLevel] = useState<string>(() => {
        try {
            return localStorage.getItem('coach.guardrailLevel') || 'low'
        } catch {
            return 'low'
        }
    })

    const [autoDelegate, setAutoDelegate] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.autoDelegate')
            return v ? v === 'true' : true
        } catch {
            return true
        }
    })

    const [preferredAgents, setPreferredAgents] = useState<string[]>(() => {
        try {
            const raw = localStorage.getItem('coach.preferredAgents')
            return raw ? JSON.parse(raw) : []
        } catch {
            return []
        }
    })

    const [contextPrefs, setContextPrefs] = useState<{ summary: boolean; includeKPIs: boolean; personaTone: boolean }>(() => {
        try {
            const raw = localStorage.getItem('coach.contextPrefs')
            return raw ? JSON.parse(raw) : { summary: true, includeKPIs: true, personaTone: true }
        } catch {
            return { summary: true, includeKPIs: true, personaTone: true }
        }
    })

    // Map presets to implied behavior (informational for now; can be wired to model settings)
    const presetHelp = useMemo(() => {
        switch (preset) {
            case 'creative':
                return 'More exploratory answers, broader suggestions.'
            case 'concise':
                return 'Short, to-the-point answers with fewer digressions.'
            default:
                return 'Balanced tone and length suitable for most tasks.'
        }
    }, [preset])

    const handleFileSelect = (selectedFile: File | null) => {
        if (selectedFile && onFileUpload) {
            setFile(selectedFile)
            onFileUpload(selectedFile)
        }
    }

    const handleDataSourceToggle = (sourceId: string) => {
        if (selectedDataSources.includes(sourceId)) {
            onDataSourcesChange(selectedDataSources.filter((id) => id !== sourceId))
        } else {
            onDataSourcesChange([...selectedDataSources, sourceId])
        }
    }

    const selectedPersonaData = personas.find((p) => p.id === selectedPersona)

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title={
                <Group gap="xs">
                    <IconSettings size={20} />
                    <Text fw={600}>Coach Settings</Text>
                </Group>
            }
            size="lg"
            styles={{
                header: { borderBottom: '1px solid #e5e7eb', paddingBottom: '12px' },
                body: { padding: 0 },
            }}
        >
            <ScrollArea h={560}>
                <Stack gap="lg" p="md">
                    {/* 1. Response style */}
                    <div>
                        <Text fw={600} size="sm" mb="xs">How should Coach respond?</Text>
                        <Group gap="sm" align="center">
                            <Select
                                value={preset}
                                onChange={(val) => { const v = val || 'balanced'; setPreset(v); try { localStorage.setItem('coach.preset', v) } catch { } }}
                                data={[{ value: 'balanced', label: 'Balanced (default)' }, { value: 'creative', label: 'Creative' }, { value: 'concise', label: 'Concise' }]}
                                size="sm"
                                style={{ width: 240 }}
                            />
                            <Text size="xs" c="dimmed">{presetHelp}</Text>
                        </Group>
                    </div>

                    {/* 2. Coach persona */}
                    <div>
                        <Text fw={600} size="sm" mb="xs">Choose a coach</Text>
                        <Select
                            value={selectedPersona}
                            onChange={(val) => { if (val) onPersonaChange(val) }}
                            data={personas.map(p => ({ value: p.id, label: `${p.emoji} ${p.name}` }))}
                            searchable
                            size="sm"
                        />
                        {selectedPersonaData && (
                            <Text size="xs" c="dimmed" mt={6}>{selectedPersonaData.description}</Text>
                        )}
                    </div>

                    {/* 3. Simple toggles */}
                    <Paper p="md" radius="md" withBorder>
                        <Stack gap={10}>
                            <Group justify="space-between">
                                <div>
                                    <Text size="sm" fw={500}>Let Coach pick the right specialist</Text>
                                    <Text size="xs" c="dimmed">Automatically routes tasks to the best helper</Text>
                                </div>
                                <Switch checked={autoDelegate} onChange={(e) => { const v = e.currentTarget.checked; setAutoDelegate(v); try { localStorage.setItem('coach.autoDelegate', String(v)) } catch { } }} />
                            </Group>
                            <Group justify="space-between">
                                <div>
                                    <Text size="sm" fw={500}>Review before sending</Text>
                                    <Text size="xs" c="dimmed">Approve or edit replies before they’re sent</Text>
                                </div>
                                <Switch checked={requireReview} onChange={(e) => { const v = e.currentTarget.checked; setRequireReview(v); try { localStorage.setItem('coach.requireReview', String(v)) } catch { } }} />
                            </Group>
                            <Group justify="space-between">
                                <div>
                                    <Text size="sm" fw={500}>Safe mode</Text>
                                    <Text size="xs" c="dimmed">Extra filtering to avoid risky content</Text>
                                </div>
                                <Switch checked={guardrailLevel === 'strict'} onChange={(e) => { const on = e.currentTarget.checked; const lvl = on ? 'strict' : 'low'; setGuardrailLevel(lvl); try { localStorage.setItem('coach.guardrailLevel', lvl) } catch { } }} />
                            </Group>
                            <Group justify="space-between">
                                <div>
                                    <Text size="sm" fw={500}>Show responses instantly</Text>
                                    <Text size="xs" c="dimmed">Stream answers as they’re generated</Text>
                                </div>
                                <Switch checked={streamingMode} onChange={(e) => { const v = e.currentTarget.checked; setStreamingMode(v); try { localStorage.setItem('coach.streamingMode', String(v)) } catch { } }} />
                            </Group>
                        </Stack>
                    </Paper>

                    {/* 4. Data & sources */}
                    <div>
                        <Text fw={600} size="sm" mb="xs">Data sources</Text>
                        <MultiSelect
                            data={dataSources.filter(s => s.available).map(s => ({ value: s.id, label: s.name }))}
                            value={selectedDataSources.filter(id => dataSources.some(s => s.id === id && s.available))}
                            onChange={(vals) => onDataSourcesChange(vals)}
                            placeholder="Use all by default"
                            searchable
                            clearable
                            size="sm"
                        />
                        <Group gap="xs" mt="xs">
                            <Checkbox
                                checked={includeEvidence}
                                onChange={(e) => onIncludeEvidenceChange(e.currentTarget.checked)}
                                label={<div><Text size="sm" fw={500}>Show sources</Text><Text size="xs" c="dimmed">Citations under answers</Text></div>}
                            />
                            <Checkbox
                                checked={includeForecast}
                                onChange={(e) => onIncludeForecastChange(e.currentTarget.checked)}
                                label={<div><Text size="sm" fw={500}>Add forecasts</Text><Text size="xs" c="dimmed">Include simple predictions</Text></div>}
                            />
                        </Group>
                    </div>

                    {/* 5. Add documents (optional) */}
                    <div>
                        <Text fw={600} size="sm" mb="xs">Add documents (optional)</Text>
                        <FileButton onChange={handleFileSelect} accept=".pdf,.txt,.md,.doc,.docx">
                            {(props) => (
                                <Button {...props} variant="light" leftSection={<IconFileUpload size={16} />}>Upload</Button>
                            )}
                        </FileButton>
                        {uploadedFiles.length > 0 && (
                            <Stack gap="xs" mt="sm">
                                {uploadedFiles.map((file, idx) => (
                                    <Paper key={idx} p="sm" radius="md" withBorder>
                                        <Group justify="space-between">
                                            <div>
                                                <Text size="sm" fw={500}>{file.name}</Text>
                                                <Text size="xs" c="dimmed">{(file.size / 1024).toFixed(1)} KB • {file.uploadedAt.toLocaleDateString()}</Text>
                                            </div>
                                            <Button variant="subtle" color="red" size="compact-sm">
                                                <IconX size={14} />
                                            </Button>
                                        </Group>
                                    </Paper>
                                ))}
                            </Stack>
                        )}
                    </div>

                    {/* 6. Summary */}
                    {selectedPersonaData && (
                        <Paper p="md" radius="md" style={{ backgroundColor: '#f8fafc' }}>
                            <Text size="xs" c="dimmed" mb="xs">CURRENT SETUP</Text>
                            <Group gap="xs" wrap="wrap">
                                <Badge size="xs" variant="light">{selectedPersonaData.emoji} {selectedPersonaData.name}</Badge>
                                <Badge size="xs" variant="light">{preset}</Badge>
                                <Badge size="xs" variant="light">Specialists: {autoDelegate ? 'Auto' : 'Manual'}</Badge>
                                <Badge size="xs" variant="light">Review: {requireReview ? 'On' : 'Off'}</Badge>
                                <Badge size="xs" variant="light">Safe mode: {guardrailLevel === 'strict' ? 'On' : 'Off'}</Badge>
                                <Badge size="xs" variant="light">Instant: {streamingMode ? 'On' : 'Off'}</Badge>
                            </Group>
                            {selectedDataSources.length > 0 ? (
                                <Text size="xs" c="dimmed" mt="xs">Using {selectedDataSources.length} selected data source(s)</Text>
                            ) : (
                                <Text size="xs" c="dimmed" mt="xs">Using all connected data</Text>
                            )}
                        </Paper>
                    )}
                </Stack>
            </ScrollArea>
        </Modal>
    )
}

export default CoachSettings
