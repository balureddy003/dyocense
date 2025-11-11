import { Card, Group, Skeleton, Stack } from '@mantine/core'

interface LoadingSkeletonProps {
    type: 'health' | 'goals' | 'message' | 'sidebar'
}

export default function LoadingSkeleton({ type }: LoadingSkeletonProps) {
    if (type === 'health') {
        return (
            <Card p="lg" withBorder>
                <Stack gap="md">
                    <Group justify="space-between">
                        <Skeleton height={24} width={120} />
                        <Skeleton height={40} width={60} radius="md" />
                    </Group>
                    <Skeleton height={8} radius="xl" />
                    <Group gap="xs">
                        <Skeleton height={24} width={80} radius="sm" />
                        <Skeleton height={24} width={80} radius="sm" />
                        <Skeleton height={24} width={80} radius="sm" />
                    </Group>
                </Stack>
            </Card>
        )
    }

    if (type === 'goals') {
        return (
            <Stack gap="xs">
                {[1, 2, 3].map((i) => (
                    <Card key={i} p="sm" withBorder>
                        <Group justify="space-between">
                            <Stack gap={4} style={{ flex: 1 }}>
                                <Skeleton height={16} width="60%" />
                                <Skeleton height={12} width="40%" />
                            </Stack>
                            <Skeleton height={12} width={40} />
                        </Group>
                    </Card>
                ))}
            </Stack>
        )
    }

    if (type === 'message') {
        return (
            <Stack gap="sm">
                <Skeleton height={16} width="80%" />
                <Skeleton height={16} width="90%" />
                <Skeleton height={16} width="70%" />
            </Stack>
        )
    }

    if (type === 'sidebar') {
        return (
            <Stack gap="lg">
                <Stack gap="xs">
                    <Skeleton height={20} width={100} />
                    <Skeleton height={60} radius="md" />
                </Stack>
                <Stack gap="xs">
                    <Skeleton height={20} width={80} />
                    {[1, 2, 3, 4].map((i) => (
                        <Skeleton key={i} height={40} />
                    ))}
                </Stack>
            </Stack>
        )
    }

    return null
}
