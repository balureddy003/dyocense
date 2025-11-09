import { ActionIcon, Card, Group, Stack, Text, Textarea } from '@mantine/core'
import { IconSend, IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'

interface Insight {
    id: string
    message: string
    type: 'suggestion' | 'alert' | 'insight'
    timestamp: string
}

interface AICopilotInsightsProps {
    insights: Insight[]
}

export default function AICopilotInsights({ insights }: AICopilotInsightsProps) {
    const [message, setMessage] = useState('')

    const getInsightIcon = (type: Insight['type']) => {
        switch (type) {
            case 'alert':
                return '⚠️'
            case 'suggestion':
                return '💡'
            case 'insight':
                return '✨'
        }
    }

    const getInsightBg = (type: Insight['type']) => {
        switch (type) {
            case 'alert':
                return 'bg-yellow-50 border-yellow-200'
            case 'suggestion':
                return 'bg-blue-50 border-blue-200'
            case 'insight':
                return 'bg-teal-50 border-teal-200'
        }
    }

    const handleSend = () => {
        if (!message.trim()) return
        // TODO: Send message to AI backend
        console.log('Sending message:', message)
        setMessage('')
    }

    return (
        <Stack gap="sm">
            <Group justify="space-between" align="center">
                <Group gap="xs">
                    <IconSparkles size={16} color="var(--mantine-color-brand-6)" />
                    <Text size="sm" fw={600} c="neutral.700" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        AI Copilot
                    </Text>
                </Group>
                <Text size="xs" c="neutral.500">
                    Powered by GPT-4
                </Text>
            </Group>

            <Card radius="md" withBorder p="md">
                <Stack gap="md">
                    {/* Insights */}
                    <Stack gap="sm">
                        {insights.map((insight) => (
                            <div
                                key={insight.id}
                                className={`p-3 rounded-lg border ${getInsightBg(insight.type)}`}
                            >
                                <Group gap="xs" align="flex-start" mb="xs">
                                    <Text size="sm">{getInsightIcon(insight.type)}</Text>
                                    <Text size="xs" c="neutral.600" fw={500}>
                                        {insight.timestamp}
                                    </Text>
                                </Group>
                                <Text size="sm" c="neutral.800">
                                    {insight.message}
                                </Text>
                            </div>
                        ))}
                    </Stack>

                    {/* Chat Input */}
                    <Group gap="xs" align="flex-end">
                        <Textarea
                            placeholder="Ask AI copilot anything..."
                            value={message}
                            onChange={(e) => setMessage(e.currentTarget.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault()
                                    handleSend()
                                }
                            }}
                            autosize
                            minRows={1}
                            maxRows={4}
                            radius="md"
                            style={{ flex: 1 }}
                            styles={{
                                input: { fontSize: '14px' },
                            }}
                        />
                        <ActionIcon
                            size="lg"
                            radius="md"
                            variant="filled"
                            color="brand"
                            onClick={handleSend}
                            disabled={!message.trim()}
                        >
                            <IconSend size={18} />
                        </ActionIcon>
                    </Group>
                </Stack>
            </Card>
        </Stack>
    )
}
