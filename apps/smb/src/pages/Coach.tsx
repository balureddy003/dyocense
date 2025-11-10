import {
    ActionIcon,
    Avatar,
    Badge,
    Button,
    Card,
    Container,
    Group,
    Loader,
    Paper,
    ScrollArea,
    Stack,
    Text,
    Textarea,
    Title,
} from '@mantine/core'
import { IconRobot, IconSend, IconSparkles, IconUser } from '@tabler/icons-react'
import { useState } from 'react'
import { post } from '../lib/api'
import { useAuthStore } from '../stores/auth'

interface Message {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp: Date
    suggestions?: string[]
}

interface Conversation {
    id: string
    title: string
    messages: Message[]
    category: 'general' | 'goal' | 'task' | 'metric'
}

export default function Coach() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)

    const [conversations] = useState<Conversation[]>([
        {
            id: '1',
            title: 'Business Coach',
            messages: [],
            category: 'general',
        },
    ])

    const [activeConversation, setActiveConversation] = useState<string>('1')
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '0',
            role: 'assistant',
            content: `Hi ${user?.name || 'there'}! 👋 I'm your AI Business Coach. I'm here to help you achieve your goals, answer questions about your business, and guide you on your journey to success.\n\nHow can I help you today?`,
            timestamp: new Date(),
            suggestions: [
                'How can I grow my revenue?',
                'What should I focus on this week?',
                'Why is my inventory turnover low?',
                'Help me break down this task',
            ],
        },
    ])

    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const quickActions = [
        {
            icon: '🎯',
            title: 'Set a Goal',
            description: 'Get help creating a new business goal',
            action: 'I want to set a new goal',
        },
        {
            icon: '📊',
            title: 'Analyze Metrics',
            description: 'Understand your business health score',
            action: 'Why is my health score at 78?',
        },
        {
            icon: '✅',
            title: 'Break Down Task',
            description: 'Get step-by-step guidance on a task',
            action: 'Help me break down my weekly tasks',
        },
        {
            icon: '💡',
            title: 'Business Advice',
            description: 'Ask about strategies and best practices',
            action: 'What should I focus on to improve cash flow?',
        },
    ]

    const handleSendMessage = async (content?: string) => {
        const messageContent = content || input
        if (!messageContent.trim() || isLoading) return

        // Add user message
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: messageContent,
            timestamp: new Date(),
        }

        setMessages([...messages, userMessage])
        setInput('')
        setIsLoading(true)

        try {
            // Call AI Coach API
            const conversationHistory = messages.slice(1).map(m => ({
                role: m.role,
                content: m.content,
                timestamp: m.timestamp.toISOString(),
            }))

            const response = await post(
                `/v1/tenants/${tenantId}/coach/chat`,
                {
                    message: messageContent,
                    conversation_history: conversationHistory,
                },
                apiToken
            )

            // Add AI response
            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date(response.timestamp),
            }

            setMessages((prev) => [...prev, aiMessage])
        } catch (error) {
            console.error('Coach error:', error)
            // Fallback message
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I apologize, but I'm having trouble connecting right now. Please try again in a moment.",
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Container size="xl" className="py-6">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Group gap="xs">
                        <IconSparkles size={24} color="#0ea5e9" />
                        <div>
                            <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                AI Assistant
                            </Text>
                            <Title order={1} size="h2" c="gray.9" mt={4}>
                                Business Coach
                            </Title>
                        </div>
                    </Group>
                    <Text size="sm" c="gray.6" mt={8}>
                        Get personalized guidance, ask questions, and refine your action plan
                    </Text>
                </div>

                <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
                    {/* Quick Actions Sidebar */}
                    <Stack gap="md">
                        <Card withBorder radius="md" p="md">
                            <Text fw={600} size="sm" mb="md">
                                Quick Actions
                            </Text>
                            <Stack gap="xs">
                                {quickActions.map((action) => (
                                    <Button
                                        key={action.title}
                                        variant="light"
                                        size="sm"
                                        fullWidth
                                        leftSection={<span style={{ fontSize: '18px' }}>{action.icon}</span>}
                                        onClick={() => handleSendMessage(action.action)}
                                        style={{ height: 'auto', padding: '12px' }}
                                    >
                                        <div style={{ textAlign: 'left', width: '100%' }}>
                                            <Text size="sm" fw={500}>
                                                {action.title}
                                            </Text>
                                            <Text size="xs" c="dimmed" style={{ whiteSpace: 'normal' }}>
                                                {action.description}
                                            </Text>
                                        </div>
                                    </Button>
                                ))}
                            </Stack>
                        </Card>

                        <Card withBorder radius="md" p="md">
                            <Text fw={600} size="sm" mb="md">
                                Context
                            </Text>
                            <Stack gap="xs">
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Business
                                    </Text>
                                    <Text size="sm" fw={500}>
                                        CycloneRake.com
                                    </Text>
                                </div>
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Health Score
                                    </Text>
                                    <Badge variant="light" color="teal" size="lg">
                                        78 - Strong
                                    </Badge>
                                </div>
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Active Goals
                                    </Text>
                                    <Text size="sm">3 goals</Text>
                                </div>
                                <div>
                                    <Text size="xs" c="dimmed">
                                        This Week
                                    </Text>
                                    <Text size="sm">2/5 tasks done</Text>
                                </div>
                            </Stack>
                        </Card>
                    </Stack>

                    {/* Chat Interface */}
                    <Card withBorder radius="md" p={0} style={{ height: '700px', display: 'flex', flexDirection: 'column' }}>
                        {/* Messages */}
                        <ScrollArea style={{ flex: 1 }} p="lg">
                            <Stack gap="md">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        style={{
                                            display: 'flex',
                                            gap: '12px',
                                            justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                                        }}
                                    >
                                        {message.role === 'assistant' && (
                                            <Avatar color="blue" radius="xl" size="md">
                                                <IconRobot size={20} />
                                            </Avatar>
                                        )}

                                        <div style={{ maxWidth: '70%' }}>
                                            <Paper
                                                p="md"
                                                radius="lg"
                                                style={{
                                                    backgroundColor:
                                                        message.role === 'user' ? '#0ea5e9' : '#f1f5f9',
                                                    color: message.role === 'user' ? 'white' : '#1e293b',
                                                }}
                                            >
                                                <Text
                                                    size="sm"
                                                    style={{
                                                        whiteSpace: 'pre-wrap',
                                                        color: message.role === 'user' ? 'white' : '#1e293b',
                                                    }}
                                                >
                                                    {message.content}
                                                </Text>
                                            </Paper>

                                            {message.suggestions && message.suggestions.length > 0 && (
                                                <Stack gap="xs" mt="xs">
                                                    <Text size="xs" c="dimmed">
                                                        Try asking:
                                                    </Text>
                                                    {message.suggestions.map((suggestion, idx) => (
                                                        <Button
                                                            key={idx}
                                                            variant="light"
                                                            size="xs"
                                                            onClick={() => handleSendMessage(suggestion)}
                                                            style={{ justifyContent: 'flex-start' }}
                                                        >
                                                            {suggestion}
                                                        </Button>
                                                    ))}
                                                </Stack>
                                            )}

                                            <Text size="xs" c="dimmed" mt={4}>
                                                {message.timestamp.toLocaleTimeString([], {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </Text>
                                        </div>

                                        {message.role === 'user' && (
                                            <Avatar color="gray" radius="xl" size="md">
                                                <IconUser size={20} />
                                            </Avatar>
                                        )}
                                    </div>
                                ))}

                                {isLoading && (
                                    <div style={{ display: 'flex', gap: '12px' }}>
                                        <Avatar color="blue" radius="xl" size="md">
                                            <IconRobot size={20} />
                                        </Avatar>
                                        <Paper p="md" radius="lg" style={{ backgroundColor: '#f1f5f9' }}>
                                            <Group gap="xs">
                                                <Loader size="xs" />
                                                <Text size="sm" c="dimmed">
                                                    Thinking...
                                                </Text>
                                            </Group>
                                        </Paper>
                                    </div>
                                )}
                            </Stack>
                        </ScrollArea>

                        {/* Input */}
                        <div style={{ borderTop: '1px solid #e5e7eb', padding: '16px' }}>
                            <Group align="flex-end" gap="sm">
                                <Textarea
                                    placeholder="Ask me anything about your business..."
                                    value={input}
                                    onChange={(e) => setInput(e.currentTarget.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault()
                                            handleSendMessage()
                                        }
                                    }}
                                    autosize
                                    minRows={1}
                                    maxRows={4}
                                    style={{ flex: 1 }}
                                />
                                <ActionIcon
                                    size="lg"
                                    variant="filled"
                                    color="blue"
                                    onClick={() => handleSendMessage()}
                                    disabled={!input.trim() || isLoading}
                                >
                                    <IconSend size={20} />
                                </ActionIcon>
                            </Group>
                            <Text size="xs" c="dimmed" mt="xs">
                                Press Enter to send, Shift+Enter for new line
                            </Text>
                        </div>
                    </Card>
                </div>
            </Stack>
        </Container>
    )
}
