import { Badge, Button, Card, Code, Collapse, Group, Stack, Text } from '@mantine/core'
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react'
import { useState } from 'react'

interface Evidence {
    claim: string
    source: string
    confidence: number
    data: any
    timestamp?: string
    sampleSize?: number
}

interface EvidencePanelProps {
    evidence: Evidence[]
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
    const [expanded, setExpanded] = useState(false)

    if (!evidence || evidence.length === 0) return null

    return (
        <div style={{ marginTop: 12 }}>
            <Button
                size="xs"
                variant="subtle"
                onClick={() => setExpanded(!expanded)}
                rightSection={expanded ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
                styles={{
                    root: {
                        fontSize: '11px',
                        fontWeight: 500,
                        color: '#6b7280',
                        padding: '4px 8px'
                    }
                }}
            >
                📊 View Evidence ({evidence.length})
            </Button>

            <Collapse in={expanded}>
                <Card mt={8} withBorder padding="sm" radius="md" style={{ background: '#fafbfc', borderColor: '#e5e7eb' }}>
                    <Stack gap={12}>
                        {evidence.map((e, i) => (
                            <div key={i}>
                                <Group gap={8} mb={6}>
                                    <Badge
                                        size="sm"
                                        color={e.confidence > 0.8 ? 'green' : e.confidence > 0.6 ? 'yellow' : 'orange'}
                                        variant="filled"
                                    >
                                        {Math.round(e.confidence * 100)}% confident
                                    </Badge>
                                    <Badge size="sm" variant="outline" color="gray">
                                        {e.source}
                                    </Badge>
                                    {e.sampleSize && (
                                        <Text size="10px" c="dimmed">
                                            n={e.sampleSize}
                                        </Text>
                                    )}
                                </Group>

                                <Text size="13px" fw={500} mb={6} c="#202123">
                                    {e.claim}
                                </Text>

                                {e.data && (
                                    <Code block style={{ fontSize: '10px', maxHeight: '150px', overflow: 'auto' }}>
                                        {JSON.stringify(e.data, null, 2)}
                                    </Code>
                                )}

                                {e.timestamp && (
                                    <Text size="10px" c="dimmed" mt={4}>
                                        {new Date(e.timestamp).toLocaleString('en-US', {
                                            month: 'short',
                                            day: 'numeric',
                                            hour: 'numeric',
                                            minute: '2-digit'
                                        })}
                                    </Text>
                                )}

                                {i < evidence.length - 1 && (
                                    <div style={{ height: 1, background: '#e5e7eb', marginTop: 12 }} />
                                )}
                            </div>
                        ))}
                    </Stack>
                </Card>
            </Collapse>
        </div>
    )
}
