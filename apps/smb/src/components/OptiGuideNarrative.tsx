import { Alert, Badge, Box, Card, Group, Paper, Stack, Text, ThemeIcon } from '@mantine/core'
import {
    IconArrowDown,
    IconArrowUp,
    IconInfoCircle,
    IconMinus,
    IconTrendingDown,
    IconTrendingUp
} from '@tabler/icons-react'
import type { OptimizationRecommendation, OptimizationResult } from '../lib/api'
import { Markdown } from './Markdown'

interface OptiGuideNarrativeProps {
    narrative: string
    originalResult?: OptimizationResult
    modifiedResult?: OptimizationResult
    modificationsApplied?: Record<string, any>
    analysis?: string
}

export function OptiGuideNarrative({
    narrative,
    originalResult,
    modifiedResult,
    modificationsApplied,
    analysis,
}: OptiGuideNarrativeProps) {
    const hasComparison = originalResult && modifiedResult

    return (
        <Stack gap="md">
            {/* Outcome Banner */}
            {hasComparison && (
                <Card withBorder p="sm" radius="md" style={{ background: '#f6f7ff' }}>
                    <Group justify="space-between" align="center">
                        <Group gap="sm" align="center">
                            <Text size="sm" fw={600}>Net impact:</Text>
                            <CostChange
                                original={originalResult!.objective_value}
                                modified={modifiedResult!.objective_value}
                            />
                        </Group>
                        <Group gap="sm" align="center">
                            <Badge size="sm" variant="light" color={modifiedResult!.solver_status === 'optimal' ? 'teal' : 'yellow'}>
                                Confidence: {modifiedResult!.solver_status === 'optimal' ? 'High' : 'Medium'}
                            </Badge>
                        </Group>
                    </Group>
                </Card>
            )}

            {/* Main Narrative */}
            <Paper p="md" withBorder>
                <Markdown content={narrative} size="sm" />
            </Paper>

            {/* Modifications Applied */}
            {modificationsApplied && Object.keys(modificationsApplied).length > 0 && (
                <Alert icon={<IconInfoCircle size={16} />} title="Scenario Parameters" color="blue">
                    <Stack gap="xs">
                        {Object.entries(modificationsApplied).map(([key, value]) => (
                            <Group key={key} gap="xs">
                                <Text size="sm" fw={500}>
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                                </Text>
                                <Badge variant="light" size="sm">
                                    {typeof value === 'number' ? value.toFixed(2) : String(value)}
                                </Badge>
                            </Group>
                        ))}
                    </Stack>
                </Alert>
            )}

            {/* Cost Comparison */}
            {hasComparison && (
                <Card withBorder p="md">
                    <Text size="sm" fw={600} mb="md">
                        Cost Impact Analysis
                    </Text>
                    <Stack gap="md">
                        {/* Cost Metrics */}
                        <Group grow>
                            <Box>
                                <Text size="xs" c="dimmed" mb={4}>
                                    Original Cost
                                </Text>
                                <Text size="xl" fw={700}>
                                    ${originalResult.objective_value.toFixed(2)}
                                </Text>
                            </Box>
                            <Box>
                                <Text size="xs" c="dimmed" mb={4}>
                                    Modified Cost
                                </Text>
                                <Text size="xl" fw={700}>
                                    ${modifiedResult.objective_value.toFixed(2)}
                                </Text>
                            </Box>
                            <Box>
                                <Text size="xs" c="dimmed" mb={4}>
                                    Change
                                </Text>
                                <CostChange
                                    original={originalResult.objective_value}
                                    modified={modifiedResult.objective_value}
                                />
                            </Box>
                        </Group>

                        {/* Savings Comparison */}
                        <Group grow>
                            <Box>
                                <Text size="xs" c="dimmed" mb={4}>
                                    Original Potential Savings
                                </Text>
                                <Text size="lg" fw={600} c="green">
                                    ${originalResult.total_potential_savings.toFixed(2)}
                                </Text>
                            </Box>
                            <Box>
                                <Text size="xs" c="dimmed" mb={4}>
                                    Modified Potential Savings
                                </Text>
                                <Text size="lg" fw={600} c="green">
                                    ${modifiedResult.total_potential_savings.toFixed(2)}
                                </Text>
                            </Box>
                        </Group>
                    </Stack>
                </Card>
            )}

            {/* Recommendations Comparison */}
            {hasComparison && originalResult.recommendations.length > 0 && (
                <Card withBorder p="md">
                    <Text size="sm" fw={600} mb="md">
                        SKU-Level Impact
                    </Text>
                    <Stack gap="xs">
                        {originalResult.recommendations.slice(0, 5).map((rec, idx) => {
                            const modifiedRec = modifiedResult.recommendations.find(
                                (r) => r.sku === rec.sku
                            )
                            return (
                                <RecommendationComparison
                                    key={rec.sku}
                                    original={rec}
                                    modified={modifiedRec}
                                />
                            )
                        })}
                    </Stack>
                </Card>
            )}

            {/* Technical Analysis (collapsible) */}
            {analysis && (
                <Card withBorder p="md" style={{ background: '#f8f9fa' }}>
                    <Text size="xs" c="dimmed" mb="xs">
                        Technical Analysis
                    </Text>
                    <Text size="xs" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                        {analysis}
                    </Text>
                </Card>
            )}
        </Stack>
    )
}

function CostChange({ original, modified }: { original: number; modified: number }) {
    const diff = modified - original
    const pct = ((diff / original) * 100).toFixed(1)
    const isIncrease = diff > 0
    const isNeutral = Math.abs(diff) < 0.01

    if (isNeutral) {
        return (
            <Group gap={4}>
                <ThemeIcon size="sm" variant="light" color="gray">
                    <IconMinus size={14} />
                </ThemeIcon>
                <Text size="lg" fw={600} c="dimmed">
                    No Change
                </Text>
            </Group>
        )
    }

    return (
        <Stack gap={4}>
            <Group gap={4}>
                <ThemeIcon size="sm" variant="light" color={isIncrease ? 'red' : 'green'}>
                    {isIncrease ? <IconArrowUp size={14} /> : <IconArrowDown size={14} />}
                </ThemeIcon>
                <Text size="lg" fw={700} c={isIncrease ? 'red' : 'green'}>
                    ${Math.abs(diff).toFixed(2)}
                </Text>
            </Group>
            <Text size="xs" c="dimmed">
                {isIncrease ? '+' : ''}
                {pct}%
            </Text>
        </Stack>
    )
}

function RecommendationComparison({
    original,
    modified,
}: {
    original: OptimizationRecommendation
    modified?: OptimizationRecommendation
}) {
    const savingsChange = modified
        ? (modified.potential_saving || 0) - (original.potential_saving || 0)
        : 0
    const hasChange = Math.abs(savingsChange) > 0.01

    return (
        <Paper p="sm" withBorder style={{ background: 'white' }}>
            <Group justify="space-between" wrap="nowrap">
                <Box style={{ flex: 1 }}>
                    <Text size="sm" fw={600} mb={2}>
                        {original.sku}
                    </Text>
                    <Text size="xs" c="dimmed">
                        {original.action.replace(/_/g, ' ')}
                    </Text>
                </Box>

                <Group gap="md">
                    {/* Original Savings */}
                    <Box>
                        <Text size="xs" c="dimmed">
                            Original
                        </Text>
                        <Text size="sm" fw={600} c="green">
                            ${(original.potential_saving || 0).toFixed(2)}
                        </Text>
                    </Box>

                    {/* Modified Savings */}
                    {modified && (
                        <>
                            <Box>
                                <Text size="xs" c="dimmed">
                                    Modified
                                </Text>
                                <Text size="sm" fw={600} c="green">
                                    ${(modified.potential_saving || 0).toFixed(2)}
                                </Text>
                            </Box>

                            {/* Change Indicator */}
                            {hasChange && (
                                <ThemeIcon
                                    size="sm"
                                    variant="light"
                                    color={savingsChange > 0 ? 'green' : 'red'}
                                >
                                    {savingsChange > 0 ? (
                                        <IconTrendingUp size={14} />
                                    ) : (
                                        <IconTrendingDown size={14} />
                                    )}
                                </ThemeIcon>
                            )}
                        </>
                    )}
                </Group>
            </Group>
        </Paper>
    )
}
