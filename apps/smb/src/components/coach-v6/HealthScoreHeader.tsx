import { ActionIcon, Button, Card, Group, Progress, Stack, Text, useMantineTheme } from '@mantine/core';
import { IconAlertCircle, IconChartBar, IconChevronDown, IconSparkles, IconTrendingDown, IconTrendingUp } from '@tabler/icons-react';
import { useState } from 'react';
import type { HealthScoreHeaderProps } from './types';

/**
 * Health Score Header Component
 * 
 * Hero section showing business health score with critical alerts and positive signals.
 * Sticky on scroll, gradient background based on score.
 */
export function HealthScoreHeader({
    score,
    previousScore,
    trend,
    changeAmount,
    criticalAlerts,
    positiveSignals,
    onViewReport,
    onAskCoach,
    loading = false,
}: HealthScoreHeaderProps) {
    const theme = useMantineTheme();
    const [expanded, setExpanded] = useState(false);

    // Determine health color based on score (softer thresholds)
    const getHealthColor = (score: number): string => {
        if (score >= 86) return theme.colors.emerald[6];
        if (score >= 76) return theme.colors.emerald[5];
        if (score >= 61) return theme.colors.blue[5];
        if (score >= 46) return theme.colors.yellow[5];
        if (score >= 31) return theme.colors.orange?.[5] ?? '#fb923c';
        return theme.colors.red[4]; // softer red
    };

    // Use a gentler gradient with neutral handling when data is minimal
    const getHealthGradient = (score: number, criticalCount: number, positiveCount: number): string => {
        // Neutral if no signal and score missing/zero
        if ((score === 0 || !Number.isFinite(score)) && criticalCount === 0 && positiveCount === 0) {
            return 'linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%)'; // gray
        }
        if (score >= 86) return 'linear-gradient(135deg, #059669 0%, #10B981 100%)';
        if (score >= 76) return 'linear-gradient(135deg, #10B981 0%, #34D399 100%)';
        if (score >= 61) return 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)';
        if (score >= 46) return 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)';
        if (score >= 31) return 'linear-gradient(135deg, #FB923C 0%, #F59E0B 100%)'; // orange
        return 'linear-gradient(135deg, #EF4444 0%, #F87171 100%)'; // softer red
    };

    const healthColor = getHealthColor(score);
    const healthGradient = getHealthGradient(score, criticalAlerts.length, positiveSignals.length);

    // Limit visible alerts/signals
    const visibleAlerts = criticalAlerts.slice(0, 2);
    const visibleSignals = positiveSignals.slice(0, 2);

    return (
        <Card
            p={0}
            radius="md"
            shadow="sm"
            style={{
                background: healthGradient,
                color: 'white',
                position: 'sticky',
                top: 0,
                zIndex: 100,
            }}
        >
            <div style={{ padding: '16px 20px' }}>
                {/* Header Row */}
                <Group justify="space-between" align="center" mb="md">
                    <div>
                        <Text size="xs" fw={600} style={{ opacity: 0.9 }}>
                            TODAY'S BUSINESS HEALTH
                        </Text>
                        <Text size="xs" style={{ opacity: 0.7 }}>
                            {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                        </Text>
                    </div>

                    <Group gap="xs">
                        <Button
                            size="xs"
                            variant="white"
                            color="dark"
                            leftSection={<IconChartBar size={14} />}
                            onClick={onViewReport}
                        >
                            View Report
                        </Button>
                        <Button
                            size="xs"
                            variant="white"
                            color="dark"
                            leftSection={<IconSparkles size={14} />}
                            onClick={onAskCoach}
                        >
                            Ask Coach
                        </Button>
                    </Group>
                </Group>

                {/* Score Display */}
                <Group align="center" gap="xl" mb="md">
                    <div>
                        <Group align="baseline" gap={8}>
                            <Text
                                size="48px"
                                fw={700}
                                style={{ lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}
                            >
                                {loading ? '--' : score}
                            </Text>
                            <Text size="lg" fw={600} style={{ opacity: 0.9 }}>
                                / 100
                            </Text>
                        </Group>

                        <Group gap={6} mt={4}>
                            {trend === 'up' && <IconTrendingUp size={16} />}
                            {trend === 'down' && <IconTrendingDown size={16} />}
                            <Text size="sm" fw={500}>
                                {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}
                                {Math.abs(changeAmount)} points from last week
                            </Text>
                        </Group>
                    </div>

                    {/* Progress Bar */}
                    <div style={{ flex: 1, maxWidth: '300px' }}>
                        <Progress
                            value={score}
                            size="xl"
                            radius="xl"
                            styles={{
                                root: { backgroundColor: 'rgba(255, 255, 255, 0.3)' },
                                section: { backgroundColor: 'white' },
                            }}
                        />
                    </div>
                </Group>

                {/* Alerts and Signals Grid */}
                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '16px',
                    }}
                >
                    {/* Critical Alerts */}
                    <div>
                        <Group gap={6} mb={8}>
                            <IconAlertCircle size={14} />
                            <Text size="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                Needs Attention ({criticalAlerts.length})
                            </Text>
                        </Group>
                        <Stack gap={4}>
                            {visibleAlerts.map((alert) => (
                                <Text key={alert.id} size="xs" style={{ opacity: 0.95 }}>
                                    • {alert.title}
                                </Text>
                            ))}
                            {criticalAlerts.length > 2 && (
                                <Text size="xs" style={{ opacity: 0.7, fontStyle: 'italic' }}>
                                    +{criticalAlerts.length - 2} more issues
                                </Text>
                            )}
                        </Stack>
                    </div>

                    {/* Positive Signals */}
                    <div>
                        <Group gap={6} mb={8}>
                            <Text size="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                ✅ Doing Well ({positiveSignals.length})
                            </Text>
                        </Group>
                        <Stack gap={4}>
                            {visibleSignals.map((signal) => (
                                <Text key={signal.id} size="xs" style={{ opacity: 0.95 }}>
                                    • {signal.title}
                                </Text>
                            ))}
                            {positiveSignals.length > 2 && (
                                <Text size="xs" style={{ opacity: 0.7, fontStyle: 'italic' }}>
                                    +{positiveSignals.length - 2} more wins
                                </Text>
                            )}
                        </Stack>
                    </div>
                </div>

                {/* Expand/Collapse Button */}
                {(criticalAlerts.length > 2 || positiveSignals.length > 2) && (
                    <Group justify="center" mt="sm">
                        <ActionIcon
                            variant="white"
                            color="dark"
                            size="sm"
                            onClick={() => setExpanded(!expanded)}
                        >
                            <IconChevronDown
                                size={14}
                                style={{
                                    transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                    transition: 'transform 0.2s',
                                }}
                            />
                        </ActionIcon>
                    </Group>
                )}

                {/* Expanded View */}
                {expanded && (
                    <div
                        style={{
                            marginTop: '16px',
                            paddingTop: '16px',
                            borderTop: '1px solid rgba(255, 255, 255, 0.3)',
                        }}
                    >
                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr',
                                gap: '16px',
                            }}
                        >
                            <Stack gap={4}>
                                {criticalAlerts.slice(2).map((alert) => (
                                    <Text key={alert.id} size="xs" style={{ opacity: 0.95 }}>
                                        • {alert.title}
                                    </Text>
                                ))}
                            </Stack>
                            <Stack gap={4}>
                                {positiveSignals.slice(2).map((signal) => (
                                    <Text key={signal.id} size="xs" style={{ opacity: 0.95 }}>
                                        • {signal.title}
                                    </Text>
                                ))}
                            </Stack>
                        </div>
                    </div>
                )}
            </div>
        </Card>
    );
}
