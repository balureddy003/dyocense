import { ActionIcon, Box, Button, Card, Group, Loader, Paper, Skeleton, Stack, Text, Textarea } from '@mantine/core'
import { IconHelp, IconSparkles, IconX } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { askWhatIf, askWhy, type WhatIfAnalysisResponse, type WhyAnalysisResponse } from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { OptiGuideNarrative } from './OptiGuideNarrative'

type AnalysisType = 'what-if' | 'why'

interface OptiGuideQuickActionsProps {
    onClose?: () => void
    initialQuestion?: string
    initialMode?: AnalysisType
    // Optional: send the generated narrative to the main chat
    onSendToChat?: (content: string) => void
}

const WHAT_IF_EXAMPLES = [
    'What if order costs increase by 20%?',
    'What if holding costs double?',
    'What if we reduce safety stock by 30%?',
    'What if service level increases to 98%?',
]

const WHY_EXAMPLES = [
    'Why are inventory costs high?',
    'Why is WIDGET-001 overstocked?',
    'Why do we have so much excess inventory?',
    'Why are stockout risks increasing?',
]

export function OptiGuideQuickActions({ onClose, initialQuestion, initialMode, onSendToChat }: OptiGuideQuickActionsProps) {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const [analysisType, setAnalysisType] = useState<AnalysisType>(initialMode || 'what-if')
    const [question, setQuestion] = useState(initialQuestion || '')
    const [whatIfResult, setWhatIfResult] = useState<WhatIfAnalysisResponse | null>(null)
    const [whyResult, setWhyResult] = useState<WhyAnalysisResponse | null>(null)
    const [recent, setRecent] = useState<Array<{ type: AnalysisType; question: string; ts: number }>>([])

    const whatIfMutation = useMutation({
        mutationFn: async (q: string) => {
            if (!tenantId) throw new Error('No tenant ID')
            return askWhatIf(tenantId, q, undefined, apiToken)
        },
        onSuccess: (data) => {
            setWhatIfResult(data)
            setWhyResult(null)
            try {
                const key = `optiguide:history:${tenantId}`
                const prev = JSON.parse(localStorage.getItem(key) || '[]') as Array<{ type: AnalysisType; question: string; ts: number }>
                const next = [{ type: 'what-if' as AnalysisType, question, ts: Date.now() }, ...prev.filter((r) => r.question !== question)].slice(0, 5)
                localStorage.setItem(key, JSON.stringify(next))
                setRecent(next)
            } catch { /* noop */ }
        },
    })

    const whyMutation = useMutation({
        mutationFn: async (q: string) => {
            if (!tenantId) throw new Error('No tenant ID')
            return askWhy(tenantId, q, undefined, apiToken)
        },
        onSuccess: (data) => {
            setWhyResult(data)
            setWhatIfResult(null)
            try {
                const key = `optiguide:history:${tenantId}`
                const prev = JSON.parse(localStorage.getItem(key) || '[]') as Array<{ type: AnalysisType; question: string; ts: number }>
                const next = [{ type: 'why' as AnalysisType, question, ts: Date.now() }, ...prev.filter((r) => r.question !== question)].slice(0, 5)
                localStorage.setItem(key, JSON.stringify(next))
                setRecent(next)
            } catch { /* noop */ }
        },
    })

    const handleSubmit = () => {
        if (!question.trim()) return

        if (analysisType === 'what-if') {
            whatIfMutation.mutate(question)
        } else {
            whyMutation.mutate(question)
        }
    }

    const handleExampleClick = (exampleQuestion: string) => {
        setQuestion(exampleQuestion)
    }

    const isLoading = whatIfMutation.isPending || whyMutation.isPending
    const hasResult = whatIfResult || whyResult

    // Sync initial props into state when drawer opens with prefilled values
    useEffect(() => {
        if (initialMode) setAnalysisType(initialMode)
    }, [initialMode])

    useEffect(() => {
        if (initialQuestion !== undefined) setQuestion(initialQuestion)
    }, [initialQuestion])

    // Load recent history on mount
    useEffect(() => {
        if (!tenantId) return
        try {
            const key = `optiguide:history:${tenantId}`
            const prev = JSON.parse(localStorage.getItem(key) || '[]') as Array<{ type: AnalysisType; question: string; ts: number }>
            setRecent(prev)
        } catch { /* noop */ }
    }, [tenantId])

    return (
        <Card withBorder p="md" shadow="sm">
            <Group justify="space-between" mb="md">
                <Group gap="xs">
                    <IconSparkles size={20} color="#4c6ef5" />
                    <Text size="lg" fw={600}>
                        Scenario Analysis
                    </Text>
                </Group>
                {onClose && (
                    <ActionIcon variant="subtle" onClick={onClose}>
                        <IconX size={16} />
                    </ActionIcon>
                )}
            </Group>

            {/* Analysis Type Selector */}
            <Group mb="md">
                <Button
                    variant={analysisType === 'what-if' ? 'filled' : 'light'}
                    size="xs"
                    leftSection={<IconSparkles size={14} />}
                    onClick={() => {
                        setAnalysisType('what-if')
                        setQuestion('')
                        setWhatIfResult(null)
                        setWhyResult(null)
                    }}
                >
                    What-If Scenarios
                </Button>
                <Button
                    variant={analysisType === 'why' ? 'filled' : 'light'}
                    size="xs"
                    leftSection={<IconHelp size={14} />}
                    onClick={() => {
                        setAnalysisType('why')
                        setQuestion('')
                        setWhatIfResult(null)
                        setWhyResult(null)
                    }}
                >
                    Why Analysis
                </Button>
            </Group>

            {/* Question Input */}
            <Stack gap="md">
                <Box>
                    <Text size="sm" fw={500} mb="xs">
                        {analysisType === 'what-if' ? 'Ask a scenario question:' : 'Ask a why question:'}
                    </Text>
                    <Textarea
                        placeholder={
                            analysisType === 'what-if'
                                ? 'What if order costs increase by 20%?'
                                : 'Why are inventory costs high?'
                        }
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        minRows={2}
                        disabled={isLoading}
                    />
                </Box>

                {/* Example Questions */}
                <Box>
                    <Text size="xs" c="dimmed" mb="xs">
                        Try these examples:
                    </Text>
                    <Group gap="xs">
                        {(analysisType === 'what-if' ? WHAT_IF_EXAMPLES : WHY_EXAMPLES).map((example) => (
                            <Button
                                key={example}
                                size="xs"
                                variant="light"
                                onClick={() => handleExampleClick(example)}
                                disabled={isLoading}
                            >
                                {example}
                            </Button>
                        ))}
                    </Group>
                </Box>

                {/* Recent Scenarios */}
                {recent.length > 0 && (
                    <Box>
                        <Text size="xs" c="dimmed" mb="xs">
                            Recent:
                        </Text>
                        <Group gap="xs">
                            {recent.slice(0, 3).map((r) => (
                                <Button
                                    key={`${r.type}-${r.ts}`}
                                    size="xs"
                                    variant="subtle"
                                    color={r.type === 'what-if' ? 'violet' : 'blue'}
                                    onClick={() => {
                                        setAnalysisType(r.type)
                                        setQuestion(r.question)
                                    }}
                                    disabled={isLoading}
                                >
                                    {r.type === 'what-if' ? 'What-if: ' : 'Why: '}{r.question}
                                </Button>
                            ))}
                        </Group>
                    </Box>
                )}

                {/* Submit Button */}
                <Button
                    fullWidth
                    onClick={handleSubmit}
                    disabled={!question.trim() || isLoading}
                    leftSection={isLoading ? <Loader size="xs" /> : <IconSparkles size={16} />}
                >
                    {isLoading ? 'Analyzing...' : 'Run Analysis'}
                </Button>

                {/* Loading skeleton */}
                {isLoading && !hasResult && (
                    <Paper p="md" withBorder>
                        <Stack gap="sm">
                            <Skeleton height={12} width="70%" radius="xl" />
                            <Skeleton height={10} width="90%" radius="xl" />
                            <Skeleton height={10} width="85%" radius="xl" />
                            <Skeleton height={10} width="60%" radius="xl" />
                        </Stack>
                    </Paper>
                )}

                {/* Results */}
                {hasResult && !isLoading && (
                    <Paper p="md" withBorder style={{ background: '#f8f9fa' }}>
                        {whatIfResult && (
                            <OptiGuideNarrative
                                narrative={whatIfResult.narrative}
                                originalResult={whatIfResult.original_result}
                                modifiedResult={whatIfResult.modified_result}
                                modificationsApplied={whatIfResult.modifications_applied}
                                analysis={whatIfResult.analysis}
                            />
                        )}
                        {whyResult && (
                            <OptiGuideNarrative
                                narrative={whyResult.narrative}
                                originalResult={
                                    whyResult.supporting_data?.recommendations
                                        ? {
                                            solver_status: 'optimal',
                                            objective_value: 0,
                                            recommendations:
                                                whyResult.supporting_data.recommendations || [],
                                            total_potential_savings: 0,
                                        }
                                        : undefined
                                }
                            />
                        )}
                        {/* Actions */}
                        <Group justify="space-between" mt="md">
                            <Group gap="xs">
                                <Button
                                    size="xs"
                                    variant="light"
                                    onClick={() => {
                                        const content = whatIfResult?.narrative || whyResult?.narrative
                                        if (!content) return
                                        try {
                                            navigator.clipboard.writeText(content)
                                        } catch {
                                            // ignore clipboard errors silently
                                        }
                                    }}
                                >
                                    Copy narrative
                                </Button>
                                <Button
                                    size="xs"
                                    variant="light"
                                    onClick={() => {
                                        const content = whatIfResult?.narrative || whyResult?.narrative
                                        if (!content) return
                                        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
                                        const url = URL.createObjectURL(blob)
                                        const a = document.createElement('a')
                                        a.href = url
                                        a.download = `scenario-analysis-${Date.now()}.md`
                                        document.body.appendChild(a)
                                        a.click()
                                        a.remove()
                                        URL.revokeObjectURL(url)
                                    }}
                                >
                                    Export .md
                                </Button>
                            </Group>
                            {onSendToChat && (
                                <Group>
                                    <Button
                                        size="xs"
                                        variant="filled"
                                        color="violet"
                                        onClick={() => {
                                            const content = whatIfResult?.narrative || whyResult?.narrative
                                            if (content) onSendToChat(content)
                                        }}
                                    >
                                        Send to chat
                                    </Button>
                                </Group>
                            )}
                        </Group>
                    </Paper>
                )}

                {/* Error State */}
                {(whatIfMutation.isError || whyMutation.isError) && (
                    <Paper p="md" withBorder style={{ background: '#fff5f5', borderColor: '#ff6b6b' }}>
                        <Stack gap="xs">
                            <Text size="sm" c="red">
                                Error:{' '}
                                {String(
                                    whatIfMutation.error?.message || whyMutation.error?.message || 'Unknown error'
                                )}
                            </Text>
                            <Group>
                                <Button size="xs" variant="light" onClick={handleSubmit}>Retry</Button>
                            </Group>
                        </Stack>
                    </Paper>
                )}
            </Stack>
        </Card>
    )
}
