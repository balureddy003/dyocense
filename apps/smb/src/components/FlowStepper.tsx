import { Badge, Button, Group, Progress, Stack, Text } from '@mantine/core'
import { IconChevronRight, IconCircleCheck } from '@tabler/icons-react'
import { useNavigate } from 'react-router-dom'

export type FlowStep = {
    key: 'connect' | 'goals' | 'plan' | 'coach' | 'analytics'
    label: string
    href: string
}

export function defaultSteps(): FlowStep[] {
    return [
        { key: 'connect', label: 'Connect data', href: '/connectors' },
        { key: 'goals', label: 'Set goals', href: '/goals' },
        { key: 'plan', label: 'Build action plan', href: '/planner' },
        { key: 'coach', label: 'Ask your coach', href: '/coach' },
        { key: 'analytics', label: 'Review analytics', href: '/analytics' },
    ]
}

interface Props {
    currentIndex: number // 0-based index
    completedCount?: number // optional explicit completed count; defaults to currentIndex
    steps?: FlowStep[]
    nextLabel?: string
}

export default function FlowStepper({ currentIndex, completedCount, steps, nextLabel }: Props) {
    const items = steps ?? defaultSteps()
    const navigate = useNavigate()
    const completed = Math.max(0, Math.min(items.length, completedCount ?? currentIndex))
    const percent = Math.round((completed / (items.length - 1)) * 100)

    const next = items[Math.min(currentIndex + 1, items.length - 1)]

    return (
        <div className="rounded-xl border border-gray-200 bg-white p-12px md:p-4" style={{ padding: 12 }}>
            <Stack gap={8}
                style={{
                    ['--gap' as any]: '8px',
                }}
            >
                <Group justify="space-between" align="center">
                    <Text size="xs" c="gray.6" fw={600} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        Guided flow
                    </Text>
                    <Group gap={6}>
                        {items.map((step, idx) => (
                            <Group key={step.key} gap={6} align="center">
                                <Badge
                                    variant={idx < completed ? 'filled' : idx === currentIndex ? 'light' : 'outline'}
                                    color={idx < completed ? 'teal' : 'gray'}
                                    leftSection={idx < completed ? <IconCircleCheck size={12} /> : undefined}
                                >
                                    {step.label}
                                </Badge>
                                {idx < items.length - 1 && <IconChevronRight size={14} color="#94a3b8" />}
                            </Group>
                        ))}
                    </Group>
                </Group>
                <Progress value={percent} size="xs" radius="xl" color="teal" aria-label="Flow progress" />
                {next && currentIndex < items.length - 1 && (
                    <Group justify="flex-end">
                        <Button size="xs" variant="light" onClick={() => navigate(next.href)}>
                            {nextLabel || `Next: ${next.label}`}
                        </Button>
                    </Group>
                )}
            </Stack>
        </div>
    )
}
