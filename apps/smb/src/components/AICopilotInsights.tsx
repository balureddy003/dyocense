import { ActionIcon, Card, Group, Loader, Stack, Text, Textarea } from '@mantine/core'
import { IconSend, IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'
import { useAuthStore } from '../stores/auth'

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
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)

    const [message, setMessage] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [chatMessages, setChatMessages] = useState<Insight[]>(insights)

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

    const handleSend = async () => {
        if (!message.trim() || isLoading) return

        const userMessage = message
        setMessage('')
        setIsLoading(true)

        // Add user message to chat
        const timestamp = new Date().toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        })

        setChatMessages(prev => [...prev, {
            id: Date.now().toString(),
            message: userMessage,
            type: 'insight',
            timestamp: timestamp
        }])

        // Add empty AI message that we'll stream into
        const aiMessageId = (Date.now() + 1).toString()
        setChatMessages(prev => [...prev, {
            id: aiMessageId,
            message: '',
            type: 'suggestion',
            timestamp: new Date().toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            })
        }])

        try {
            // Use EventSource for streaming
            const url = new URL(`/v1/tenants/${tenantId}/coach/chat/stream`, window.location.origin)

            // Send request with fetch first to initiate streaming
            const response = await fetch(url.toString(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiToken}`
                },
                body: JSON.stringify({
                    message: userMessage,
                    conversation_history: [],
                })
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            // Read the stream
            const reader = response.body?.getReader()
            const decoder = new TextDecoder()

            if (!reader) {
                throw new Error('No response body')
            }

            let accumulatedMessage = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                // Decode the chunk
                const chunk = decoder.decode(value, { stream: true })

                // Parse SSE data (format: "data: {...}\n\n")
                const lines = chunk.split('\n')
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6))
                            if (!data.done) {
                                accumulatedMessage += data.delta
                                // Update the AI message in real-time
                                setChatMessages(prev => prev.map(msg =>
                                    msg.id === aiMessageId
                                        ? { ...msg, message: accumulatedMessage }
                                        : msg
                                ))
                            }
                        } catch (e) {
                            console.error('Failed to parse SSE chunk:', e)
                        }
                    }
                }
            }
        } catch (error) {
            console.error('AI Coach error:', error)
            // Update AI message with error
            setChatMessages(prev => prev.map(msg =>
                msg.id === aiMessageId
                    ? {
                        ...msg,
                        message: "I'm having trouble connecting right now. Please try again in a moment.",
                        type: 'alert'
                    }
                    : msg
            ))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Stack gap="sm">
            <Group justify="space-between" align="center">
                <Group gap="xs">
                    <IconSparkles size={16} color="var(--mantine-color-brand-6)" />
                    <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        AI Coach
                    </Text>
                </Group>
                <Text size="xs" c="gray.5">
                    Powered by GPT-4
                </Text>
            </Group>

            <Card radius="md" withBorder p="md">
                <Stack gap="md">
                    {/* Insights */}
                    <Stack gap="sm">
                        {chatMessages.map((insight) => (
                            <div
                                key={insight.id}
                                className={`p-3 rounded-lg border ${getInsightBg(insight.type)}`}
                            >
                                <Group gap="xs" align="flex-start" mb="xs">
                                    <Text size="sm">{getInsightIcon(insight.type)}</Text>
                                    <Text size="xs" c="gray.6" fw={500}>
                                        {insight.timestamp}
                                    </Text>
                                </Group>
                                <Text size="sm" c="gray.8">
                                    {insight.message}
                                </Text>
                            </div>
                        ))}

                        {/* Loading indicator */}
                        {isLoading && (
                            <Group gap="xs" justify="center" py="sm">
                                <Loader size="sm" />
                                <Text size="sm" c="dimmed">AI Coach is thinking...</Text>
                            </Group>
                        )}
                    </Stack>

                    {/* Chat Input */}
                    <Group gap="xs" align="flex-end">
                        <Textarea
                            placeholder="Ask AI coach anything..."
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
