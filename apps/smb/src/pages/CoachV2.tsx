import {
    ActionIcon,
    Badge,
    Box,
    Button,
    Card,
    Group,
    Paper,
    ScrollArea,
    Stack,
    Text,
    Textarea,
    Title
} from '@mantine/core'
import {
    IconChartBar,
    IconChecklist,
    IconDatabase,
    IconSend,
    IconSparkles,
    IconTarget
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useNavigate } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import { AgentSelector } from '../components/AgentSelector'
import { get, post } from '../lib/api'
import { useAuthStore } from '../stores/auth'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

export default function CoachV2() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()

    // Fetch business context
    const { data: healthScore } = useQuery({
        queryKey: ['health-score', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/health-score`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    const { data: goalsData } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/goals`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    const { data: tasksData } = useQuery({
        queryKey: ['tasks', tenantId, 'todo'],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    // State
    const [selectedPersona, setSelectedPersona] = useState('business_analyst')
    const [agentConversations, setAgentConversations] = useState<Record<string, Message[]>>({
        business_analyst: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Business Analyst** — think of me as your fitness coach for business growth.\n\nJust like a fitness tracker monitors your health rings, I track your **Business Health Score** across Revenue, Operations, and Customer metrics.\n\n**How I help:**\n- 📊 Analyze your business health in real-time\n- 🎯 Break down big goals into weekly action plans\n- ✅ Track your progress and celebrate milestones\n- 💡 Provide data-driven recommendations\n\nWhat would you like to work on today?`,
                timestamp: new Date(),
            },
        ],
        data_scientist: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Data Scientist** — your analytics coach.\n\nI help you understand patterns in your business data, forecast future trends, and make data-driven decisions to improve your Business Health Score.\n\n**What I can do:**\n- 📈 Forecast sales, inventory, and customer trends\n- 🔍 Identify patterns and anomalies in your data\n- 📉 Predict risks before they become problems\n- 💰 Optimize pricing and inventory strategies\n\nWhat predictions or insights do you need?`,
                timestamp: new Date(),
            },
        ],
        consultant: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Business Consultant** — your strategic fitness coach.\n\nI help you develop winning strategies, implement best practices, and build sustainable competitive advantages.\n\n**My expertise:**\n- 🎯 Strategic planning and goal setting\n- 💼 Best practices from successful SMBs\n- 🚀 Growth strategies and market positioning\n- ⚙️ Process optimization and efficiency\n\nWhat strategy should we work on?`,
                timestamp: new Date(),
            },
        ],
        operations_manager: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Operations Manager** — your efficiency coach.\n\nI help you streamline operations, reduce waste, and improve your operational health score.\n\n**Focus areas:**\n- ⚡ Process optimization and automation\n- 📦 Inventory management and fulfillment\n- 💵 Cash flow and working capital\n- 🎯 Resource allocation and productivity\n\nWhich operations should we improve?`,
                timestamp: new Date(),
            },
        ],
        growth_strategist: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Growth Strategist** — your revenue fitness coach.\n\nI help you scale sustainably, maximize revenue, and improve your customer health metrics.\n\n**Growth levers:**\n- 💰 Revenue optimization and pricing\n- 🎯 Customer acquisition and retention\n- 📈 Market expansion strategies\n- 🚀 Scaling operations efficiently\n\nHow can we accelerate your growth this quarter?`,
                timestamp: new Date(),
            },
        ],
    })

    const [isLoading, setIsLoading] = useState(false)
    const [input, setInput] = useState('')
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>([])
    const [showQuickActions, setShowQuickActions] = useState(true)
    const [showPlanDrawer, setShowPlanDrawer] = useState(false)
    const [showContextBar, setShowContextBar] = useState(false)

    const scrollAreaRef = useRef<HTMLDivElement>(null)
    const messages = agentConversations[selectedPersona] || []

    // Load conversations from localStorage
    useEffect(() => {
        const saved = localStorage.getItem(`agent-conversations-${tenantId}`)
        if (saved) {
            const parsed = JSON.parse(saved)
            const converted: Record<string, Message[]> = {}
            Object.keys(parsed).forEach((agent) => {
                converted[agent] = parsed[agent].map((m: any) => ({
                    ...m,
                    timestamp: new Date(m.timestamp),
                }))
            })
            setAgentConversations(converted)
        }
    }, [tenantId])

    // Save conversations
    useEffect(() => {
        if (tenantId) {
            localStorage.setItem(`agent-conversations-${tenantId}`, JSON.stringify(agentConversations))
        }
    }, [agentConversations, tenantId])

    // Auto-scroll to latest message
    useEffect(() => {
        if (scrollAreaRef.current) {
            const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
            if (viewport) {
                viewport.scrollTop = viewport.scrollHeight
            }
        }
    }, [messages])

    // Smart quick actions based on business state
    const quickActions = [
        ...(healthScore?.score && healthScore.score < 70
            ? [
                {
                    icon: '🚨',
                    label: 'Fix Health Issues',
                    prompt: `My health score is ${healthScore.score}. What's the quickest way to improve it?`,
                    color: 'red',
                },
            ]
            : []),
        ...(tasksData?.length > 0
            ? [
                {
                    icon: '✅',
                    label: `${tasksData.length} Pending Tasks`,
                    prompt: `I have ${tasksData.length} tasks. Help me prioritize and create a plan.`,
                    color: 'blue',
                },
            ]
            : []),
        {
            icon: '📊',
            label: 'Analyze Performance',
            prompt: 'Show me my key metrics and what actions I should take.',
            color: 'grape',
        },
        {
            icon: '🎯',
            label: goalsData?.length > 0 ? 'Review Goals' : 'Set First Goal',
            prompt:
                goalsData?.length > 0
                    ? `I have ${goalsData.length} goals. Help me review progress and next steps.`
                    : 'Help me set my first business goal.',
            color: 'teal',
        },
        {
            icon: '🚀',
            label: 'Growth Strategy',
            prompt: 'What are the top 3 actions I should take to grow my business this month?',
            color: 'indigo',
        },
    ].slice(0, 4)

    const handleSendMessage = async (message: string) => {
        if (!message.trim() || isLoading) return

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: message,
            timestamp: new Date(),
        }

        setAgentConversations((prev) => ({
            ...prev,
            [selectedPersona]: [...(prev[selectedPersona] || []), userMessage],
        }))

        setIsLoading(true)
        setShowQuickActions(false)

        try {
            const conversationHistory = (agentConversations[selectedPersona] || []).slice(1).map((m) => ({
                role: m.role,
                content: m.content,
                timestamp: m.timestamp.toISOString(),
            }))

            const response = await post(
                `/v1/tenants/${tenantId}/coach/chat`,
                {
                    message,
                    conversation_history: conversationHistory,
                    persona: selectedPersona,
                    data_sources: selectedDataSources.length > 0 ? selectedDataSources : undefined,
                },
                apiToken
            )

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date(response.timestamp),
            }

            setAgentConversations((prev) => ({
                ...prev,
                [selectedPersona]: [...(prev[selectedPersona] || []), aiMessage],
            }))
        } catch (error) {
            console.error('Chat error:', error)
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date(),
            }
            setAgentConversations((prev) => ({
                ...prev,
                [selectedPersona]: [...(prev[selectedPersona] || []), errorMessage],
            }))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)', background: '#f8f9fa' }}>
            {/* Header */}
            <div style={{ borderBottom: '1px solid #e9ecef', background: 'white', padding: '12px 16px', flexShrink: 0 }}>
                <Group justify="space-between" wrap="wrap" gap="xs">
                    <div style={{ flex: '1 1 auto', minWidth: 200 }}>
                        <Group gap="xs" mb={2}>
                            <IconSparkles size={20} color="#4c6ef5" />
                            <Title order={4}>Business Coach</Title>
                        </Group>
                        <Text size="xs" c="dimmed">
                            Get personalized guidance
                        </Text>
                    </div>
                    <Group gap="xs">
                        <Button
                            size="xs"
                            variant="light"
                            leftSection={<IconDatabase size={14} />}
                            onClick={() => setShowContextBar(!showContextBar)}
                        >
                            {showContextBar ? 'Hide' : 'Show'} Context
                        </Button>
                        <Button
                            size="xs"
                            variant="light"
                            leftSection={<IconChartBar size={14} />}
                            onClick={() => setShowPlanDrawer(true)}
                        >
                            Plan
                        </Button>
                    </Group>
                </Group>
            </div>

            {/* Main Content */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
                {/* Context Sidebar (Collapsible) */}
                <Collapse in={showContextBar} style={{ borderRight: '1px solid #e9ecef', background: 'white' }}>
                    <div style={{ width: 280, padding: 16 }}>
                        <Stack gap="md">
                            <div>
                                <Text size="xs" fw={600} tt="uppercase" c="dimmed" mb="xs">
                                    Business Context
                                </Text>
                                <Card withBorder padding="sm">
                                    <Text size="sm" fw={500} mb={4}>
                                        CycloneRake.com
                                    </Text>
                                    <Badge size="sm" color={healthScore?.score >= 70 ? 'green' : 'red'}>
                                        Health: {healthScore?.score || 42}/100
                                    </Badge>
                                </Card>
                            </div>

                            {goalsData?.length > 0 && (
                                <div>
                                    <Group justify="space-between" mb="xs">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed">
                                            Active Goals
                                        </Text>
                                        <ActionIcon size="sm" variant="subtle" onClick={() => navigate('/goals')}>
                                            <IconTarget size={14} />
                                        </ActionIcon>
                                    </Group>
                                    <Badge size="lg" variant="light" color="teal">
                                        {goalsData.length} goals
                                    </Badge>
                                </div>
                            )}

                            {tasksData?.length > 0 && (
                                <div>
                                    <Group justify="space-between" mb="xs">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed">
                                            Pending Tasks
                                        </Text>
                                        <ActionIcon size="sm" variant="subtle" onClick={() => navigate('/tasks')}>
                                            <IconChecklist size={14} />
                                        </ActionIcon>
                                    </Group>
                                    <Badge size="lg" variant="light" color="blue">
                                        {tasksData.length} tasks
                                    </Badge>
                                </div>
                            )}

                            <div>
                                <Text size="xs" fw={600} tt="uppercase" c="dimmed" mb="xs">
                                    Data Sources
                                </Text>
                                <Group gap={4}>
                                    {selectedDataSources.length > 0 ? (
                                        selectedDataSources.map((ds) => (
                                            <Badge key={ds} size="sm" variant="dot" color="green">
                                                {ds}
                                            </Badge>
                                        ))
                                    ) : (
                                        <Text size="xs" c="dimmed">
                                            Sample data
                                        </Text>
                                    )}
                                </Group>
                            </div>
                        </Stack>
                    </div>
                </Collapse>

                {/* Chat Area */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', minWidth: 0 }}>
                    {/* Quick Actions (Floating) */}
                    {showQuickActions && messages.length <= 1 && (
                        <div
                            style={{
                                position: 'absolute',
                                top: 16,
                                left: 16,
                                right: 16,
                                zIndex: 10,
                                maxWidth: 800,
                                margin: '0 auto',
                            }}
                        >
                            <Card shadow="sm" padding="md" radius="md" withBorder>
                                <Group justify="space-between" mb="sm">
                                    <Text fw={600} size="sm">
                                        Quick Actions
                                    </Text>
                                    <ActionIcon
                                        size="xs"
                                        variant="subtle"
                                        onClick={() => setShowQuickActions(false)}
                                    >
                                        <IconX size={14} />
                                    </ActionIcon>
                                </Group>
                                <Group gap="xs" style={{ flexWrap: 'wrap' }}>
                                    {quickActions.map((action, idx) => (
                                        <UnstyledButton
                                            key={idx}
                                            onClick={() => handleSendMessage(action.prompt)}
                                            style={{
                                                padding: '8px 12px',
                                                borderRadius: 8,
                                                border: '1px solid #e9ecef',
                                                background: 'white',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s',
                                                flex: '1 1 auto',
                                                minWidth: 140,
                                                maxWidth: 200,
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.borderColor = '#4c6ef5'
                                                e.currentTarget.style.background = '#f8f9ff'
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.borderColor = '#e9ecef'
                                                e.currentTarget.style.background = 'white'
                                            }}
                                        >
                                            <Text size="md" mb={2}>
                                                {action.icon}
                                            </Text>
                                            <Text size="xs" fw={500} style={{ lineHeight: 1.3 }}>
                                                {action.label}
                                            </Text>
                                        </UnstyledButton>
                                    ))}
                                </Group>
                            </Card>
                        </div>
                    )}

                    {/* Chat Messages Area */}
                    <ScrollArea
                        style={{ flex: 1, minHeight: 0 }}
                        viewportRef={scrollAreaRef}
                        offsetScrollbars
                    >
                        <Stack gap="md" p="md">
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    style={{
                                        display: 'flex',
                                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    }}
                                >
                                    <Paper
                                        p="md"
                                        radius="lg"
                                        style={{
                                            maxWidth: '85%',
                                            background: msg.role === 'user' ? '#4c6ef5' : 'white',
                                            color: msg.role === 'user' ? 'white' : '#1a1b1e',
                                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                                        }}
                                    >
                                        {msg.role === 'assistant' ? (
                                            <Box
                                                style={{
                                                    '& h1, & h2, & h3': {
                                                        marginTop: '1rem',
                                                        marginBottom: '0.5rem',
                                                        fontWeight: 600,
                                                    },
                                                    '& h1': { fontSize: '1.5rem' },
                                                    '& h2': { fontSize: '1.25rem' },
                                                    '& h3': { fontSize: '1.1rem' },
                                                    '& p': { marginBottom: '0.75rem' },
                                                    '& ul, & ol': {
                                                        marginLeft: '1.5rem',
                                                        marginBottom: '0.75rem',
                                                    },
                                                    '& li': { marginBottom: '0.25rem' },
                                                    '& strong': { fontWeight: 600 },
                                                    '& code': {
                                                        background: '#f1f3f5',
                                                        padding: '0.125rem 0.375rem',
                                                        borderRadius: '0.25rem',
                                                        fontSize: '0.875em',
                                                    },
                                                    '& pre': {
                                                        background: '#f1f3f5',
                                                        padding: '1rem',
                                                        borderRadius: '0.5rem',
                                                        overflow: 'auto',
                                                    },
                                                }}
                                            >
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </Box>
                                        ) : (
                                            <Text size="sm">{msg.content}</Text>
                                        )}
                                    </Paper>
                                </div>
                            ))}
                            {isLoading && (
                                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                                    <Paper p="md" radius="lg" style={{ background: 'white' }}>
                                        <Group gap="xs">
                                            <Text size="sm" c="dimmed">Thinking</Text>
                                            <span className="typing-dots">
                                                <span>.</span><span>.</span><span>.</span>
                                            </span>
                                        </Group>
                                    </Paper>
                                </div>
                            )}
                        </Stack>
                    </ScrollArea>

                    {/* Message Input */}
                    <Paper
                        p="md"
                        style={{
                            borderTop: '1px solid #e9ecef',
                            background: 'white',
                            flexShrink: 0,
                        }}
                    >
                        <form
                            onSubmit={(e) => {
                                e.preventDefault()
                                if (input.trim() && !isLoading) {
                                    handleSendMessage(input)
                                    setInput('')
                                }
                            }}
                        >
                            <Group gap="xs" align="flex-end">
                                {/* Agent Selector */}
                                <div>
                                    <AgentSelector
                                        agents={[
                                            { id: 'business_analyst', name: 'Business Analyst' },
                                            { id: 'data_scientist', name: 'Data Scientist' },
                                            { id: 'consultant', name: 'Consultant' },
                                            { id: 'operations_manager', name: 'Operations Manager' },
                                            { id: 'growth_strategist', name: 'Growth Strategist' },
                                        ]}
                                        selectedAgent={selectedPersona}
                                        onAgentChange={setSelectedPersona}
                                        compact
                                    />
                                </div>

                                <Textarea
                                    placeholder="Ask me anything about your business..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault()
                                            if (input.trim() && !isLoading) {
                                                handleSendMessage(input)
                                                setInput('')
                                            }
                                        }
                                    }}
                                    minRows={1}
                                    maxRows={4}
                                    autosize
                                    disabled={isLoading}
                                    style={{ flex: 1 }}
                                    styles={{
                                        input: {
                                            border: '1px solid #e9ecef',
                                            borderRadius: '12px',
                                            padding: '12px 16px',
                                        },
                                    }}
                                />

                                <Button
                                    type="submit"
                                    disabled={!input.trim() || isLoading}
                                    leftSection={<IconSend size={16} />}
                                    size="md"
                                    radius="xl"
                                >
                                    Send
                                </Button>
                            </Group>
                        </form>
                    </Paper>
                </div>
            </div>

            {/* Plan Inspector Drawer */}
            <Drawer
                opened={showPlanDrawer}
                onClose={() => setShowPlanDrawer(false)}
                position="right"
                size="md"
                title="Plan Inspector"
            >
                <PlanSidebar
                    tenantId={tenantId}
                    personaId={selectedPersona}
                    content={messages.filter((m) => m.role === 'assistant').slice(-1)[0]?.content}
                />
            </Drawer>
        </div>
    )
}
