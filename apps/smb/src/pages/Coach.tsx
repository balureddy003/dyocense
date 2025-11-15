// DEPRECATED: Legacy Coach page. The app uses CoachV5 for /coach. Do not import.
import {
    ActionIcon,
    Avatar,
    Badge,
    Button,
    Card,
    Container,
    FileButton,
    Group,
    Loader,
    MultiSelect,
    Paper,
    ScrollArea,
    Stack,
    Text,
    Textarea,
    Title,
    Tooltip
} from '@mantine/core'
import { IconDatabase, IconFileUpload, IconMicrophone, IconPaperclip, IconRobot, IconSend, IconSparkles, IconUser, IconX } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { AgentSelector } from '../components/AgentSelector'
import { CoachMessage } from '../components/CoachMessage'
import { DeepDivePanel, DeepDiveStep } from '../components/DeepDivePanel'
import { PlanSidebar } from '../components/PlanSidebar'
import { get, post } from '../lib/api'
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
    const location = useLocation()

    // Fetch business context for sidebar
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

    const { data: dataSourceInfo } = useQuery({
        queryKey: ['data-source', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/data-source`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    const [conversations] = useState<Conversation[]>([
        {
            id: '1',
            title: 'Business Coach',
            messages: [],
            category: 'general',
        },
    ])

    const [activeConversation, setActiveConversation] = useState<string>('1')

    // Per-agent conversation memory
    const [agentConversations, setAgentConversations] = useState<Record<string, Message[]>>({
        business_analyst: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your Business Analyst. I'll help you analyze KPIs, track metrics, and understand your business performance.\n\nWhat would you like to analyze today?`,
                timestamp: new Date(),
                suggestions: [
                    'What are my top KPIs?',
                    'How does this month compare to last?',
                    'Which metrics need attention?',
                ],
            },
        ],
        data_scientist: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your Data Scientist. I specialize in predictive analytics, forecasting, and statistical analysis.\n\nWhat predictions do you need?`,
                timestamp: new Date(),
                suggestions: [
                    'What will my revenue be next month?',
                    'Forecast demand for top products',
                    'Predict customer churn risk',
                ],
            },
        ],
        consultant: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your Business Consultant. I'll help you develop strategies, create action plans, and implement best practices.\n\nWhat strategy should we work on?`,
                timestamp: new Date(),
                suggestions: [
                    'Create a growth strategy',
                    'What are industry best practices?',
                    'How should I prioritize initiatives?',
                ],
            },
        ],
        operations_manager: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your Operations Manager. I focus on process optimization, inventory management, and operational efficiency.\n\nWhat operations can I help optimize?`,
                timestamp: new Date(),
                suggestions: [
                    'Optimize inventory levels',
                    'Reduce operational costs',
                    'Improve fulfillment efficiency',
                ],
            },
        ],
        growth_strategist: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your Growth Strategist. I'll help you scale your business, identify growth levers, and maximize revenue.\n\nHow can we accelerate your growth?`,
                timestamp: new Date(),
                suggestions: [
                    'How can I 10x my revenue?',
                    'What growth levers should I pull?',
                    'Increase customer lifetime value',
                ],
            },
        ],
    })

    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [deepDiveSteps, setDeepDiveSteps] = useState<DeepDiveStep[]>([
        { id: 'understand', label: 'Understanding Requirements', done: false },
        { id: 'confirm', label: 'Confirm Query Parameters', done: false },
        { id: 'retrieve', label: 'Search and Retrieve Resources', done: false },
        { id: 'draft', label: 'Synthesize & Draft Report', done: false },
    ])
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    // Coach settings state - simplified, no modal
    const [selectedPersona, setSelectedPersona] = useState('business_analyst')
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>([])
    const [uploadedFiles, setUploadedFiles] = useState<{ id: string; name: string; size: number; uploadedAt: Date }[]>([])

    // Current messages = messages for selected agent
    const messages = agentConversations[selectedPersona] || []
    // Track previous assistant message per agent for revert functionality
    const [previousAssistantByAgent, setPreviousAssistantByAgent] = useState<Record<string, Message | null>>({})
    const [pendingRevisionAgent, setPendingRevisionAgent] = useState<string | null>(null)

    // Chat history storage
    const [chatHistory, setChatHistory] = useState<Array<{
        id: string
        title: string
        agent: string
        timestamp: Date
        preview: string
    }>>([])

    // Load chat history from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem(`coach-history-${tenantId}`)
        if (saved) {
            const parsed = JSON.parse(saved)
            setChatHistory(parsed.map((h: any) => ({
                ...h,
                timestamp: new Date(h.timestamp)
            })))
        }

        // Load agent conversations from localStorage
        const savedConversations = localStorage.getItem(`agent-conversations-${tenantId}`)
        if (savedConversations) {
            const parsed = JSON.parse(savedConversations)
            const converted: Record<string, Message[]> = {}
            Object.keys(parsed).forEach(agent => {
                converted[agent] = parsed[agent].map((m: any) => ({
                    ...m,
                    timestamp: new Date(m.timestamp)
                }))
            })
            setAgentConversations(converted)
        }
    }, [tenantId])

    // Save conversations to localStorage whenever they change
    useEffect(() => {
        if (tenantId) {
            localStorage.setItem(`agent-conversations-${tenantId}`, JSON.stringify(agentConversations))
        }
    }, [agentConversations, tenantId])

    // Save chat history to localStorage
    useEffect(() => {
        if (tenantId && chatHistory.length > 0) {
            localStorage.setItem(`coach-history-${tenantId}`, JSON.stringify(chatHistory))
        }
    }, [chatHistory, tenantId])

    // Fetch coach personas
    const { data: personasData } = useQuery({
        queryKey: ['coach-personas'],
        queryFn: () => get('/v1/coach/personas', apiToken),
        enabled: !!apiToken,
    })

    // Fetch available data sources
    const { data: dataSourcesData } = useQuery({
        queryKey: ['data-sources', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/data-sources`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    const personas = personasData?.personas || []
    const dataSources = dataSourcesData?.data_sources || []
    const selectedPersonaData = personas.find((p: any) => p.id === selectedPersona)

    const handleFileUpload = async (file: File | null) => {
        if (!file) return

        // Add file with unique ID
        const newFile = {
            id: Date.now().toString(),
            name: file.name,
            size: file.size,
            uploadedAt: new Date(),
        }
        setUploadedFiles([...uploadedFiles, newFile])

        // TODO: Upload to backend for RAG processing
        // const formData = new FormData()
        // formData.append('file', file)
        // await post(`/v1/tenants/${tenantId}/coach/knowledge`, formData, apiToken)
    }

    const handleRemoveFile = (fileId: string) => {
        setUploadedFiles(uploadedFiles.filter(f => f.id !== fileId))
    }

    // Handle navigation with context (from insights or other pages)
    useEffect(() => {
        const state = location.state as { question?: string } | null
        if (state?.question) {
            setInput(state.question)
            // Clear the state so it doesn't auto-fill again on page refresh
            window.history.replaceState({}, document.title)

            // Auto-send the question
            setTimeout(() => {
                handleSendMessage(state.question)
            }, 500)
        }
    }, [location.state])

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (scrollAreaRef.current) {
            const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
            if (viewport) {
                viewport.scrollTop = viewport.scrollHeight
            }
        }
    }, [messages, isLoading])

    // Dynamic Quick Actions based on actual business data
    const quickActions = [
        ...(healthScore?.score && healthScore.score < 70 ? [{
            icon: '🚨',
            title: 'Improve Health Score',
            description: `Your score is ${healthScore.score}. Let's fix it`,
            action: `My health score is ${healthScore.score}. What should I prioritize to improve it?`,
        }] : []),
        ...(goalsData?.length > 0 ? [{
            icon: '🎯',
            title: 'Review My Goals',
            description: `You have ${goalsData.length} active goals`,
            action: `I have ${goalsData.length} active goals. Help me review and prioritize them.`,
        }] : [{
            icon: '🎯',
            title: 'Set a Goal',
            description: 'Create your first business goal',
            action: 'I want to set a new goal to grow my business',
        }]),
        ...(tasksData?.length > 0 ? [{
            icon: '✅',
            title: 'My Pending Tasks',
            description: `${tasksData.length} tasks need attention`,
            action: `I have ${tasksData.length} pending tasks. Help me break them down and prioritize.`,
        }] : []),
        {
            icon: '�',
            title: 'Analyze Performance',
            description: 'Review key metrics & insights',
            action: 'Show me my key performance metrics and what they mean for my business',
        },
        {
            icon: '💡',
            title: 'Growth Strategy',
            description: 'Get personalized advice',
            action: dataSourceInfo?.hasRealData
                ? `Based on my ${dataSourceInfo.orders} orders and ${dataSourceInfo.customers} customers, what should I focus on to accelerate growth?`
                : 'What are the top 3 things I should focus on to grow my business?',
        },
    ].slice(0, 4) // Keep only top 4 most relevant

    const handleSendMessage = async (content?: string) => {
        const messageContent = content || input
        if (!messageContent.trim() || isLoading) return

        // Add user message to current agent's conversation
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: messageContent,
            timestamp: new Date(),
        }

        // Update agent-specific conversation
        setAgentConversations(prev => ({
            ...prev,
            [selectedPersona]: [...(prev[selectedPersona] || []), userMessage]
        }))

        setInput('')
        setIsLoading(true)
        // reset steps
        setDeepDiveSteps([
            { id: 'understand', label: 'Understanding Requirements', done: true },
            { id: 'confirm', label: 'Confirm Query Parameters', done: false },
            { id: 'retrieve', label: 'Search and Retrieve Resources', done: false },
            { id: 'draft', label: 'Synthesize & Draft Report', done: false },
        ])

        try {
            // Call AI Coach API with agent-specific history
            const conversationHistory = (agentConversations[selectedPersona] || []).slice(1).map(m => ({
                role: m.role,
                content: m.content,
                timestamp: m.timestamp.toISOString(),
            }))

            // mark confirm
            setDeepDiveSteps(prev => prev.map(s => s.id === 'confirm' ? { ...s, done: true } : s))

            const response = await post(
                `/v1/tenants/${tenantId}/coach/chat`,
                {
                    message: messageContent,
                    conversation_history: conversationHistory,
                    persona: selectedPersona,
                    data_sources: selectedDataSources.length > 0 ? selectedDataSources : undefined,
                    uploaded_files: uploadedFiles.length > 0 ? uploadedFiles.map(f => f.id) : undefined,
                },
                apiToken
            )

            // mark retrieve
            setDeepDiveSteps(prev => prev.map(s => s.id === 'retrieve' ? { ...s, done: true } : s))

            // Add AI response to current agent's conversation
            // store previous assistant if exists
            const prevAssistant = (agentConversations[selectedPersona] || []).slice().reverse().find(m => m.role === 'assistant') || null
            setPreviousAssistantByAgent(prev => ({ ...prev, [selectedPersona]: prevAssistant }))

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date(response.timestamp),
            }

            setAgentConversations(prev => ({
                ...prev,
                [selectedPersona]: [...(prev[selectedPersona] || []), aiMessage]
            }))

            setPendingRevisionAgent(selectedPersona)

            // mark draft
            setDeepDiveSteps(prev => prev.map(s => s.id === 'draft' ? { ...s, done: true } : s))

            // Save to chat history
            const historyEntry = {
                id: Date.now().toString(),
                title: messageContent.substring(0, 50) + (messageContent.length > 50 ? '...' : ''),
                agent: selectedPersona,
                timestamp: new Date(),
                preview: response.message.substring(0, 100) + '...',
            }
            setChatHistory(prev => [historyEntry, ...prev].slice(0, 50)) // Keep last 50 chats

        } catch (error) {
            console.error('Coach error:', error)
            // Fallback message
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I apologize, but I'm having trouble connecting right now. Please try again in a moment.",
                timestamp: new Date(),
            }
            setAgentConversations(prev => ({
                ...prev,
                [selectedPersona]: [...(prev[selectedPersona] || []), errorMessage]
            }))
        } finally {
            setIsLoading(false)
        }
    }

    // Function to clear current agent's conversation
    const handleClearConversation = () => {
        const selectedAgent = personas.find((p: any) => p.id === selectedPersona)
        const initialMessage: Message = {
            id: '0',
            role: 'assistant',
            content: `Hi ${user?.name || 'there'}! 👋 I'm your ${selectedAgent?.name || 'Business Coach'}. How can I help you today?`,
            timestamp: new Date(),
        }
        setAgentConversations(prev => ({
            ...prev,
            [selectedPersona]: [initialMessage]
        }))
    }

    return (
        <Container size="xl" className="py-6">
            <Stack gap="xl">
                {/* Header - Simplified */}
                <div>
                    <Group gap="xs" justify="space-between">
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
                        {/* Data Source & File Upload - Inline */}
                        <Group gap="sm">
                            <MultiSelect
                                placeholder="Select data sources"
                                data={dataSources.map((ds: any) => ({ value: ds.id, label: ds.name }))}
                                value={selectedDataSources}
                                onChange={setSelectedDataSources}
                                leftSection={<IconDatabase size={16} />}
                                styles={{
                                    input: { minWidth: 200 },
                                }}
                                clearable
                                searchable
                            />
                            <FileButton onChange={handleFileUpload} accept=".pdf,.doc,.docx,.txt,.csv,.xlsx">
                                {(props) => (
                                    <Tooltip label="Upload files for context (RAG)">
                                        <Button {...props} variant="light" leftSection={<IconFileUpload size={18} />}>
                                            Upload Files
                                        </Button>
                                    </Tooltip>
                                )}
                            </FileButton>
                        </Group>
                    </Group>
                    <Text size="sm" c="gray.6" mt={8}>
                        Get personalized guidance, ask questions, and refine your action plan
                    </Text>

                    {/* Show uploaded files */}
                    {uploadedFiles.length > 0 && (
                        <Group gap="xs" mt="sm">
                            <Text size="xs" c="dimmed">Files:</Text>
                            {uploadedFiles.map((file) => (
                                <Badge
                                    key={file.id}
                                    variant="light"
                                    color="blue"
                                    rightSection={
                                        <ActionIcon size="xs" variant="transparent" onClick={() => handleRemoveFile(file.id)}>
                                            <IconX size={10} />
                                        </ActionIcon>
                                    }
                                >
                                    {file.name}
                                </Badge>
                            ))}
                        </Group>
                    )}
                </div>

                <div className="grid gap-6 xl:grid-cols-[300px_1fr_260px] lg:grid-cols-[300px_1fr]">
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
                                    <Badge
                                        variant="light"
                                        color={healthScore?.score >= 80 ? 'teal' : healthScore?.score >= 60 ? 'yellow' : 'red'}
                                        size="lg"
                                    >
                                        {healthScore?.score || 78} - {healthScore?.score >= 80 ? 'Strong' : healthScore?.score >= 60 ? 'Good' : 'Needs Work'}
                                    </Badge>
                                </div>
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Active Goals
                                    </Text>
                                    <Text size="sm">{goalsData?.length || 0} goals</Text>
                                </div>
                                <div>
                                    <Text size="xs" c="dimmed">
                                        Pending Tasks
                                    </Text>
                                    <Text size="sm">{tasksData?.length || 0} tasks</Text>
                                </div>
                                {dataSourceInfo && (
                                    <>
                                        <div>
                                            <Text size="xs" c="dimmed">
                                                Data Sources
                                            </Text>
                                            <Text size="sm">
                                                {dataSourceInfo.hasRealData ? (
                                                    <Badge size="sm" color="green">Connected</Badge>
                                                ) : (
                                                    <Badge size="sm" color="orange">Sample Data</Badge>
                                                )}
                                            </Text>
                                        </div>
                                        <div>
                                            <Text size="xs" c="dimmed">
                                                Records
                                            </Text>
                                            <Text size="xs">
                                                {dataSourceInfo.orders} orders, {dataSourceInfo.customers} customers
                                            </Text>
                                        </div>
                                    </>
                                )}
                            </Stack>
                        </Card>
                    </Stack>

                    {/* Chat Interface */}
                    <Card withBorder radius="md" p={0} style={{ height: '700px', display: 'flex', flexDirection: 'column' }}>
                        {/* Messages */}
                        <ScrollArea style={{ flex: 1 }} p="lg" viewportRef={scrollAreaRef}>
                            <Stack gap="md">
                                {/* DeepDive Panel */}
                                {isLoading || deepDiveSteps.some(s => s.done) && (
                                    <DeepDivePanel steps={deepDiveSteps} running={isLoading} />
                                )}
                                {messages.map((message, idx) => (
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
                                                        message.role === 'user' ? '#0ea5e9' : '#f8fafc',
                                                    color: message.role === 'user' ? 'white' : '#1e293b',
                                                    border: message.role === 'assistant' ? '1px solid #e2e8f0' : 'none',
                                                }}
                                            >
                                                <CoachMessage content={message.content} isUser={message.role === 'user'} />
                                            </Paper>

                                            {/* Revision Controls under the latest assistant message */}
                                            {message.role === 'assistant' && idx === messages.length - 1 && pendingRevisionAgent === selectedPersona && (
                                                <Group mt="xs" gap="xs">
                                                    <Button size="xs" variant="filled" color="blue" onClick={() => setPendingRevisionAgent(null)}>
                                                        Keep new version
                                                    </Button>
                                                    {previousAssistantByAgent[selectedPersona] && (
                                                        <Button size="xs" variant="light" color="gray" onClick={() => {
                                                            setAgentConversations(prev => ({
                                                                ...prev,
                                                                [selectedPersona]: [...(prev[selectedPersona] || []).slice(0, -1), previousAssistantByAgent[selectedPersona] as Message]
                                                            }))
                                                            setPendingRevisionAgent(null)
                                                        }}>
                                                            Return to previous version
                                                        </Button>
                                                    )}
                                                </Group>
                                            )}

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

                        {/* Modern Input Area */}
                        <div style={{ padding: '16px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0' }}>
                            {/* Agent Selector & Context Bar */}
                            <Group mb="sm" gap="xs">
                                <AgentSelector
                                    agents={personas}
                                    selectedAgent={selectedPersona}
                                    onAgentChange={setSelectedPersona}
                                    compact
                                />
                                {selectedDataSources.length > 0 && (
                                    <Badge size="sm" variant="light" color="blue" leftSection={<IconDatabase size={12} />}>
                                        {selectedDataSources.length} source{selectedDataSources.length > 1 ? 's' : ''}
                                    </Badge>
                                )}
                                {uploadedFiles.length > 0 && (
                                    <Badge size="sm" variant="light" color="teal" leftSection={<IconPaperclip size={12} />}>
                                        {uploadedFiles.length} file{uploadedFiles.length > 1 ? 's' : ''}
                                    </Badge>
                                )}
                            </Group>

                            {/* Input with Actions */}
                            <Group align="flex-start" gap="xs">
                                <FileButton onChange={handleFileUpload} accept=".pdf,.doc,.docx,.txt,.csv,.xlsx">
                                    {(props) => (
                                        <Tooltip label="Attach file">
                                            <ActionIcon
                                                {...props}
                                                size="lg"
                                                variant="subtle"
                                                color="gray"
                                                style={{ marginTop: 4 }}
                                            >
                                                <IconPaperclip size={20} />
                                            </ActionIcon>
                                        </Tooltip>
                                    )}
                                </FileButton>
                                <Textarea
                                    placeholder="@mention an agent or ask anything..."
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
                                    maxRows={6}
                                    styles={{
                                        input: {
                                            border: 'none',
                                            padding: '8px 12px',
                                            fontSize: '14px',
                                            backgroundColor: 'transparent',
                                        },
                                    }}
                                    style={{ flex: 1 }}
                                />
                                <Group gap="xs" style={{ marginTop: 4 }}>
                                    <ActionIcon
                                        size="lg"
                                        variant="subtle"
                                        color="gray"
                                    >
                                        <IconMicrophone size={20} />
                                    </ActionIcon>
                                    <ActionIcon
                                        size="lg"
                                        variant="filled"
                                        color="blue"
                                        radius="xl"
                                        onClick={() => handleSendMessage()}
                                        disabled={!input.trim() || isLoading}
                                    >
                                        <IconSend size={18} />
                                    </ActionIcon>
                                </Group>
                            </Group>
                        </div>
                    </Card>

                    {/* Plan Sidebar (only on wide screens) */}
                    <div className="hidden xl:block">
                        <PlanSidebar tenantId={tenantId} personaId={selectedPersona} content={messages.filter(m => m.role === 'assistant').slice(-1)[0]?.content} />
                    </div>
                </div>
            </Stack>
        </Container>
    )
}
