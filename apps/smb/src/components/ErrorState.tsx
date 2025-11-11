import { Alert, Button, Group, Stack, Text } from '@mantine/core'
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react'

interface ErrorStateProps {
    title?: string
    message: string
    onRetry?: () => void
    variant?: 'inline' | 'card'
}

export default function ErrorState({
    title = 'Something went wrong',
    message,
    onRetry,
    variant = 'inline'
}: ErrorStateProps) {
    const content = (
        <Stack gap="sm">
            <Group gap="xs">
                <IconAlertCircle size={20} color="var(--mantine-color-red-6)" />
                <Text fw={600} c="red.6">{title}</Text>
            </Group>
            <Text size="sm" c="dimmed">{message}</Text>
            {onRetry && (
                <Button
                    leftSection={<IconRefresh size={16} />}
                    onClick={onRetry}
                    variant="light"
                    color="red"
                    size="sm"
                >
                    Try Again
                </Button>
            )}
        </Stack>
    )

    if (variant === 'card') {
        return (
            <Alert
                color="red"
                variant="light"
                p="lg"
            >
                {content}
            </Alert>
        )
    }

    return content
}
