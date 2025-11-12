import { Alert, Badge, Box, Button, Card, Chip, Collapse, Group, Progress, ScrollArea, Stack, Text, Textarea, TextInput, Title, Tooltip } from '@mantine/core'
import {
    IconArrowRight,
    IconChecklist,
    IconSearch,
    IconSend,
    IconSparkles,
    IconTarget
} from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useNavigate } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import CoachSettings from '../components/CoachSettings'
import { ModelSettingsPopover } from '../components/ModelSettingsPopover'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { get, post } from '../lib/api'
import { getTenantToolsAndPrompts } from '../lib/toolSuggestions'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    intent?: string
    goal_id?: string | null
    persona?: string
    streaming?: boolean
    // Phase 1 observability & feedback
    runUrl?: string
    tracingEnabled?: boolean
    toolEvents?: Array<{ type: string; name?: string; ts?: string; latency_ms?: number }>
    feedback?: 'up' | 'down'
}

export default function CoachV3() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()
    const { selectedTemplate } = useTemplateStore()

    // Check if coming from goals page
    const [showWelcomeBanner, setShowWelcomeBanner] = useState(() => {
        const fromGoals = sessionStorage.getItem('fromGoalsPage')
        if (fromGoals === 'true') {
            sessionStorage.removeItem('fromGoalsPage')
            return true
        }
        return false
    })

    // Success banner after creating plan from Coach
    const [showPlanCreatedBanner, setShowPlanCreatedBanner] = useState(false)
    const [errorBanner, setErrorBanner] = useState<string | null>(null)

    const queryClient = useQueryClient()
    // Telemetry helper bound to current auth token
    const logAnalyticsEvent = (eventType: string, payload: Record<string, any>) => {
        try {
            if (!apiToken) return
            post('/v1/analytics/events', { event_type: eventType, payload }, apiToken)
        } catch (e) {
            console.warn('Telemetry emit failed', e)
        }
    }
    const [selectedGoalId, setSelectedGoalId] = useState<string | null>(null)
    const [settingsOpen, setSettingsOpen] = useState(false)
    const [streamingMode, setStreamingMode] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.streamingMode')
            return v ? v === 'true' : true
        } catch {
            return true
        }
    })
    const [showAgentLabels, setShowAgentLabels] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.showAgentLabels')
            return v ? v === 'true' : true
        } catch {
            return true
        }
    })
    // Sidebar & search state (persisted)
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(() => {
        try {
            const v = localStorage.getItem('coach.sidebarOpen')
            return v ? v === 'true' : true
        } catch { return true }
    })
    const [chatSearch, setChatSearch] = useState<string>(() => {
        try {
            return localStorage.getItem('coach.chatSearch') || ''
        } catch { return '' }
    })
    useEffect(() => {
        localStorage.setItem('coach.sidebarOpen', String(sidebarOpen))
    }, [sidebarOpen])
    useEffect(() => {
        localStorage.setItem('coach.chatSearch', chatSearch)
    }, [chatSearch])

    // Phase 2: Model settings (power users, collapsed by default)
    const [modelSettings, setModelSettings] = useState(() => {
        try {
            const stored = localStorage.getItem('coach.modelSettings')
            return stored ? JSON.parse(stored) : { temperature: 0.7, maxTokens: 2048, model: 'llama3.1' }
        } catch {
            return { temperature: 0.7, maxTokens: 2048, model: 'llama3.1' }
        }
    })
    useEffect(() => {
        localStorage.setItem('coach.modelSettings', JSON.stringify(modelSettings))
    }, [modelSettings])

    // Keep settings in sync if changed elsewhere (e.g., CoachSettings modal)
    useEffect(() => {
        const onStorage = (e: StorageEvent) => {
            if (e.key === 'coach.streamingMode' && e.newValue != null) {
                setStreamingMode(e.newValue === 'true')
            }
            if (e.key === 'coach.showAgentLabels' && e.newValue != null) {
                setShowAgentLabels(e.newValue === 'true')
            }
        }
        window.addEventListener('storage', onStorage)
        return () => window.removeEventListener('storage', onStorage)
    }, [])

    // Create plan directly from Coach (links to latest goal if available)
    const createPlanMutation = useMutation({
        mutationFn: async () => {
            let latestGoalId: string | undefined
            // Prefer explicitly selected goal
            if (selectedGoalId) {
                latestGoalId = selectedGoalId
            } else {
                try {
                    latestGoalId = sessionStorage.getItem('latestGoalId') || undefined
                } catch { }
                // Fallback: first active goal
                if (!latestGoalId && Array.isArray(goalsData) && goalsData.length > 0) {
                    latestGoalId = goalsData[0].id
                }
            }

            return await post<any>(
                `/v1/tenants/${encodeURIComponent(tenantId!)}/plans`,
                {
                    goal_id: latestGoalId,
                    archetype_id: selectedTemplate?.archetypeId,
                    regenerate: true,
                },
                apiToken,
            )
        },
        onSuccess: (plan) => {
            sessionStorage.setItem('fromCoachPage', 'true')
            setShowPlanCreatedBanner(true)
            setTimeout(() => setShowPlanCreatedBanner(false), 10000)
            // Optimistically prime planner cache
            if (plan) {
                try {
                    queryClient.setQueryData(['plan', tenantId], plan)
                } catch (e) {
                    console.warn('Failed to seed plan cache', e)
                }
            }
            // Telemetry: plan creation success
            logAnalyticsEvent('plan_creation_success', {
                goal_id: selectedGoalId,
                archetype_id: selectedTemplate?.archetypeId,
                source: 'coach_v3',
                has_goals: Array.isArray(goalsData) ? goalsData.length : 0,
            })
        },
        onError: (err: any) => {
            console.error('Plan creation error:', err)
            setErrorBanner('Unable to create action plan. Please try again.')
            setTimeout(() => setErrorBanner(null), 12000)
            // Telemetry: plan creation failure with sanitized error details
            logAnalyticsEvent('plan_creation_failed', {
                goal_id: selectedGoalId,
                archetype_id: selectedTemplate?.archetypeId,
                source: 'coach_v3',
                error_class: err?.name || typeof err,
                error_message: (err?.message || '').slice(0, 300),
            })
        },
    })

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

    // Initialize selected goal from sessionStorage or first available once goals load
    useEffect(() => {
        if (!goalsData || goalsData.length === 0) return
        const stored = sessionStorage.getItem('latestGoalId')
        const initial = stored && goalsData.some((g: any) => g.id === stored) ? stored : goalsData[0].id
        setSelectedGoalId(initial)
    }, [goalsData])

    // State
    const [selectedPersona, setSelectedPersona] = useState('business_analyst')
    // Settings state for modal
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>(() => {
        try { return JSON.parse(localStorage.getItem('coach.selectedDataSources') || '[]') } catch { return [] }
    })
    const [includeEvidence, setIncludeEvidence] = useState<boolean>(() => {
        try { return (localStorage.getItem('coach.includeEvidence') || 'true') === 'true' } catch { return true }
    })
    const [includeForecast, setIncludeForecast] = useState<boolean>(() => {
        try { return (localStorage.getItem('coach.includeForecast') || 'false') === 'true' } catch { return false }
    })
    // Adapter: define personas for settings modal
    const personas = [
        { id: 'business_analyst', name: 'Business Analyst', emoji: '📊', description: 'Analyzes KPIs and performance', expertise: ['KPIs', 'Dashboards'], tone: 'professional' },
        { id: 'data_scientist', name: 'Data Scientist', emoji: '📈', description: 'Forecasts and predictions', expertise: ['Forecasting', 'Stats'], tone: 'analytical' },
        { id: 'consultant', name: 'Consultant', emoji: '💼', description: 'Strategy and execution plans', expertise: ['Strategy', 'Execution'], tone: 'confident' },
        { id: 'operations_manager', name: 'Operations Manager', emoji: '⚙️', description: 'Processes and efficiency', expertise: ['Ops', 'Inventory'], tone: 'practical' },
        { id: 'growth_strategist', name: 'Growth Strategist', emoji: '🚀', description: 'Revenue and growth levers', expertise: ['Growth', 'Marketing'], tone: 'energetic' },
    ]
    // Adapter: dataSources placeholder; can be wired to API later
    const dataSources: Array<{ id: string; name: string; connector: string; record_count: number; available: boolean }> = []
    const handlePersonaChange = (personaId: string) => setSelectedPersona(personaId)
    const handleDataSourcesChange = (sources: string[]) => {
        setSelectedDataSources(sources)
        try { localStorage.setItem('coach.selectedDataSources', JSON.stringify(sources)) } catch { }
    }
    const handleIncludeEvidenceChange = (v: boolean) => { setIncludeEvidence(v); try { localStorage.setItem('coach.includeEvidence', String(v)) } catch { } }
    const handleIncludeForecastChange = (v: boolean) => { setIncludeForecast(v); try { localStorage.setItem('coach.includeForecast', String(v)) } catch { } }
    const [agentConversations, setAgentConversations] = useState<Record<string, Message[]>>({
        business_analyst: [
            {
                id: '0',
                role: 'assistant',
                content: `Hi ${user?.name || 'there'}! 👋 I'm your **Business Analyst** — your fitness coach for business growth.\n\nJust like a fitness tracker monitors your health rings, I track your **Business Health Score** across Revenue, Operations, and Customer metrics.\n\n**How I help:**\n- 📊 Analyze your business health in real-time\n- 🎯 Break down big goals into weekly action plans\n- ✅ Track your progress and celebrate milestones\n- 💡 Provide data-driven recommendations\n\nWhat would you like to work on today?`,
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
    const [showContextPanel, setShowContextPanel] = useState(false)
    // Connector-aware suggestions
    const connectorsQuery = useConnectorsQuery(apiToken, tenantId, { enabled: Boolean(apiToken && tenantId) })
    const { tools: suggestedTools, prompts: suggestedPrompts } = getTenantToolsAndPrompts(connectorsQuery.data)
    const handleInsertPrompt = (text: string) => {
        setInput((prev) => (prev && !prev.endsWith(' ') ? prev + ' ' + text : prev + text))
    }

    const scrollAreaRef = useRef<HTMLDivElement>(null)
    const messages = agentConversations[selectedPersona] || []
    const visibleMessages = chatSearch.trim()
        ? messages.filter(m => m.content.toLowerCase().includes(chatSearch.toLowerCase()))
        : messages

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
    }, [visibleMessages])

    // Basic client-side intent classification (lightweight, keyword based)
    const classifyIntent = (text: string): string | undefined => {
        const t = text.toLowerCase()
        if (/forecast|predict|projection|next month|next quarter/.test(t)) return 'forecast'
        if (/inventory|stock|optimize inventory|low-stock|replenish/.test(t)) return 'optimize_inventory'
        if (/compliance|policy|a1facts|regulation|align/.test(t)) return 'compliance_check'
        if (/plan|tasks|weekly action|action plan/.test(t)) return 'plan_generation'
        if (/goal|prioritize|break down/.test(t)) return 'goal_refinement'
        return undefined
    }

    const handleSendMessage = async (message: string) => {
        if (!message.trim() || isLoading) return

        const intent = classifyIntent(message)
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: message,
            timestamp: new Date(),
            intent,
            goal_id: selectedGoalId,
            persona: selectedPersona,
        }

        setAgentConversations((prev) => ({
            ...prev,
            [selectedPersona]: [...(prev[selectedPersona] || []), userMessage],
        }))

        setIsLoading(true)

        const conversationHistory = (agentConversations[selectedPersona] || []).slice(1).map((m) => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp.toISOString(),
        }))

        // Provide latest goal context if present (helps backend ground the conversation)
        let latestGoalContext: any = undefined
        try {
            const g = sessionStorage.getItem('latestGoal')
            if (g) latestGoalContext = JSON.parse(g)
        } catch { }

        const basePayload = {
            message,
            conversation_history: conversationHistory,
            persona: selectedPersona,
            goal_context: latestGoalContext,
            goal_id: selectedGoalId,
            intent,
            temperature: modelSettings.temperature,
            max_tokens: modelSettings.maxTokens,
            model: modelSettings.model,
        }

        if (streamingMode) {
            // Attempt streaming via SSE endpoint
            try {
                const url = `/v1/tenants/${tenantId}/coach/chat/stream`
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${apiToken}`,
                    },
                    body: JSON.stringify(basePayload),
                })
                if (!resp.ok || !resp.body) throw new Error(`Streaming not available (${resp.status})`)
                const reader = resp.body.getReader()
                const decoder = new TextDecoder()
                let assistantContent = ''
                const assistantMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: '',
                    timestamp: new Date(),
                    intent,
                    goal_id: selectedGoalId,
                    persona: selectedPersona,
                    streaming: true,
                }
                setAgentConversations((prev) => ({
                    ...prev,
                    [selectedPersona]: [...(prev[selectedPersona] || []), assistantMsg],
                }))
                let done = false
                while (!done) {
                    const { value, done: streamDone } = await reader.read()
                    if (streamDone) break
                    const chunk = decoder.decode(value, { stream: true })
                    for (const line of chunk.split('\n')) {
                        if (!line.startsWith('data:')) continue
                        const dataLine = line.slice(5).trim()
                        if (!dataLine) continue
                        try {
                            const parsed = JSON.parse(dataLine)
                            if (parsed.delta) {
                                assistantContent += parsed.delta
                                // Update the last message
                                setAgentConversations((prev) => ({
                                    ...prev,
                                    [selectedPersona]: prev[selectedPersona].map((m) =>
                                        m.id === assistantMsg.id ? { ...m, content: assistantContent } : m,
                                    ),
                                }))
                            }
                            // If backend provides metadata (e.g., resolved agent/intent), capture it
                            if (parsed.metadata) {
                                setAgentConversations((prev) => ({
                                    ...prev,
                                    [selectedPersona]: prev[selectedPersona].map((m) =>
                                        m.id === assistantMsg.id
                                            ? {
                                                ...m,
                                                persona: parsed.metadata.agent || m.persona,
                                                intent: parsed.metadata.intent || m.intent,
                                                // tracing
                                                runUrl: parsed.metadata.run_url || m.runUrl,
                                                tracingEnabled: typeof parsed.metadata.tracing_enabled === 'boolean' ? parsed.metadata.tracing_enabled : m.tracingEnabled,
                                                toolEvents: parsed.metadata.tool_event
                                                    ? [...(m.toolEvents || []), parsed.metadata.tool_event]
                                                    : m.toolEvents,
                                            }
                                            : m,
                                    ),
                                }))
                            }
                            if (parsed.done) {
                                done = true
                            }
                        } catch {
                            // ignore malformed JSON lines
                        }
                    }
                }
                // Finalize message (remove streaming flag)
                setAgentConversations((prev) => ({
                    ...prev,
                    [selectedPersona]: prev[selectedPersona].map((m) =>
                        m.id === assistantMsg.id ? { ...m, streaming: false, content: assistantContent } : m,
                    ),
                }))
            } catch (error) {
                console.warn('Streaming failed, falling back to standard chat:', error)
                // Fallback to non-streaming POST
                try {
                    const response = await post(`/v1/tenants/${tenantId}/coach/chat`, basePayload, apiToken)
                    const aiMessage: Message = {
                        id: (Date.now() + 1).toString(),
                        role: 'assistant',
                        content: response.message,
                        timestamp: new Date(response.timestamp),
                        intent,
                        goal_id: selectedGoalId,
                        persona: selectedPersona,
                    }
                    setAgentConversations((prev) => ({
                        ...prev,
                        [selectedPersona]: [...(prev[selectedPersona] || []), aiMessage],
                    }))
                } catch (fallbackErr) {
                    console.error('Chat error:', fallbackErr)
                    const errorMessage: Message = {
                        id: (Date.now() + 1).toString(),
                        role: 'assistant',
                        content: 'Sorry, I encountered an error. Please try again.',
                        timestamp: new Date(),
                        intent: 'error',
                        goal_id: selectedGoalId,
                        persona: selectedPersona,
                    }
                    setAgentConversations((prev) => ({
                        ...prev,
                        [selectedPersona]: [...(prev[selectedPersona] || []), errorMessage],
                    }))
                    logAnalyticsEvent('coach_chat_failed', {
                        persona: selectedPersona,
                        goal_id: selectedGoalId,
                        error_message: (fallbackErr as any)?.message?.slice(0, 200) || 'unknown',
                        streaming_attempted: true,
                    })
                }
            } finally {
                setIsLoading(false)
            }
        } else {
            // Non-streaming path
            try {
                const response = await post(`/v1/tenants/${tenantId}/coach/chat`, basePayload, apiToken)
                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: response.message,
                    timestamp: new Date(response.timestamp),
                    intent,
                    goal_id: selectedGoalId,
                    persona: selectedPersona,
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
                    intent: 'error',
                    goal_id: selectedGoalId,
                    persona: selectedPersona,
                }
                setAgentConversations((prev) => ({
                    ...prev,
                    [selectedPersona]: [...(prev[selectedPersona] || []), errorMessage],
                }))
                logAnalyticsEvent('coach_chat_failed', {
                    persona: selectedPersona,
                    goal_id: selectedGoalId,
                    error_message: (error as any)?.message?.slice(0, 200) || 'unknown',
                    streaming_attempted: false,
                })
            } finally {
                setIsLoading(false)
            }
        }
    }

    // Get latest AI plan from messages
    const latestPlan = messages
        .filter((m) => m.role === 'assistant')
        .reverse()
        .find((m) => m.content.includes('action') || m.content.includes('plan') || m.content.includes('task'))

    return (
        <div style={{ display: 'flex', height: 'calc(100vh - 80px)', background: '#ffffff' }}>
            {/* Sidebar */}
            {sidebarOpen && (
                <div style={{ width: 280, borderRight: '1px solid #e5e7eb', background: '#fafafa', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb' }}>
                        <Group justify="space-between" gap="xs">
                            <Text fw={600} size="sm">Chats & Context</Text>
                            <Button size="compact-xs" variant="subtle" onClick={() => setSidebarOpen(false)}>Hide</Button>
                        </Group>
                        <TextInput
                            mt="xs"
                            size="xs"
                            placeholder="Search chat..."
                            leftSection={<IconSearch size={14} />}
                            value={chatSearch}
                            onChange={(e) => setChatSearch(e.currentTarget.value)}
                            rightSection={chatSearch && (
                                <Button size="compact-xs" variant="subtle" onClick={() => setChatSearch('')}>Clear</Button>
                            )}
                        />
                    </div>
                    <ScrollArea style={{ flex: 1 }}>
                        <Stack p="sm" gap="sm">
                            <div>
                                <Text tt="uppercase" c="dimmed" fw={600} size="xs" mb={4}>Active Goals</Text>
                                {goalsData && goalsData.length > 0 ? (
                                    <Stack gap={6}>
                                        {goalsData.slice(0, 6).map((g: any) => (
                                            <Card key={g.id} withBorder padding="xs" radius="sm" style={{ cursor: 'pointer' }} onClick={() => { setSelectedGoalId(g.id); sessionStorage.setItem('latestGoalId', g.id) }}>
                                                <Text size="xs" fw={500} lineClamp={1}>{g.title}</Text>
                                                <Progress value={(g.current / g.target) * 100} size="xs" radius="xl" mt={4} />
                                            </Card>
                                        ))}
                                    </Stack>
                                ) : (
                                    <Text size="xs" c="dimmed">No goals yet</Text>
                                )}
                            </div>
                            <div>
                                <Text tt="uppercase" c="dimmed" fw={600} size="xs" mb={4}>Context</Text>
                                <Card withBorder padding="xs" radius="sm">
                                    <Group justify="space-between" mb={4}>
                                        <Text size="xs">Health</Text>
                                        <Badge size="sm" color={healthScore?.score >= 70 ? 'teal' : healthScore?.score >= 50 ? 'yellow' : 'red'}>{healthScore?.score || 0}</Badge>
                                    </Group>
                                    <Text size="xs" c="dimmed">Tasks: {tasksData?.length || 0}</Text>
                                </Card>
                            </div>
                        </Stack>
                    </ScrollArea>
                </div>
            )}
            {!sidebarOpen && (
                <div style={{ width: 28, borderRight: '1px solid #e5e7eb', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Button variant="subtle" size="compact-xs" onClick={() => setSidebarOpen(true)}>▶</Button>
                </div>
            )}
            {/* Main Column */}
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                {/* ChatGPT-Style Header */}
                <div style={{ borderBottom: '1px solid #e5e7eb', background: 'white', padding: '12px 0', flexShrink: 0 }}>
                    <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px' }}>
                        <Group justify="space-between" align="center">
                            <Group gap="xs">
                                <IconSparkles size={24} color="#6366f1" />
                                <div>
                                    <Title order={4} style={{ marginBottom: 0, fontSize: 18 }}>
                                        AI Business Coach
                                    </Title>
                                    <Text size="xs" c="dimmed">
                                        Powered by LangGraph
                                    </Text>
                                </div>
                            </Group>

                            <Group gap="xs">
                                <ModelSettingsPopover
                                    settings={modelSettings}
                                    onChange={setModelSettings}
                                    provider="ollama"
                                />
                                <Button size="sm" variant="subtle" onClick={() => setSettingsOpen(true)}>
                                    Settings
                                </Button>
                                <Button
                                    size="sm"
                                    variant="subtle"
                                    onClick={() => setShowContextPanel(!showContextPanel)}
                                    color={showContextPanel ? 'blue' : 'gray'}
                                >
                                    {showContextPanel ? 'Hide' : 'Show'} Context
                                </Button>
                                <Button size="sm" variant="subtle" leftSection={<IconTarget size={16} />} onClick={() => navigate('/goals')}>
                                    Goals
                                </Button>
                                <Button size="sm" variant="subtle" leftSection={<IconChecklist size={16} />} onClick={() => navigate('/planner')}>
                                    Tasks
                                </Button>
                            </Group>
                        </Group>
                    </div>
                </div>

                {/* Welcome Banner */}
                {showWelcomeBanner && (
                    <div style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <div style={{ maxWidth: 900, margin: '0 auto', padding: '12px 24px' }}>
                            <Alert
                                variant="light"
                                color="blue"
                                title="Ready to refine your goal! 💪"
                                withCloseButton
                                onClose={() => setShowWelcomeBanner(false)}
                                icon={<IconSparkles size={20} />}
                            >
                                <Text size="sm" mb="sm">
                                    Ask your coach to break down your goal into steps, identify risks, or create a weekly action plan.
                                </Text>
                                <Group gap="xs">
                                    <Button
                                        size="xs"
                                        variant="light"
                                        onClick={() => {
                                            setInput('Help me break down my latest goal into weekly action steps')
                                            setShowWelcomeBanner(false)
                                        }}
                                    >
                                        Break into steps
                                    </Button>
                                    <Button
                                        size="xs"
                                        variant="light"
                                        onClick={() => {
                                            setShowWelcomeBanner(false)
                                            createPlanMutation.mutate()
                                        }}
                                        loading={createPlanMutation.isPending}
                                        rightSection={<IconArrowRight size={14} />}
                                    >
                                        Create Action Plan
                                    </Button>
                                </Group>
                            </Alert>
                        </div>
                    </div>
                )}

                {/* Success/Error Banners */}
                {showPlanCreatedBanner && (
                    <div style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <div style={{ maxWidth: 900, margin: '0 auto', padding: '12px 24px' }}>
                            <Alert
                                variant="light"
                                color="green"
                                title="Action plan created! 🎉"
                                withCloseButton
                                onClose={() => setShowPlanCreatedBanner(false)}
                                icon={<IconSparkles size={20} />}
                            >
                                <Text size="sm" mb="sm">
                                    Your weekly action plan is ready.
                                </Text>
                                <Button
                                    size="xs"
                                    variant="light"
                                    color="green"
                                    onClick={() => navigate('/planner')}
                                    rightSection={<IconArrowRight size={14} />}
                                >
                                    Open Planner
                                </Button>
                            </Alert>
                        </div>
                    </div>
                )}

                {errorBanner && (
                    <div style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <div style={{ maxWidth: 900, margin: '0 auto', padding: '12px 24px' }}>
                            <Alert
                                variant="light"
                                color="red"
                                title="Action plan failed"
                                withCloseButton
                                onClose={() => setErrorBanner(null)}
                            >
                                <Text size="sm" mb="xs">{errorBanner}</Text>
                                <Button
                                    size="xs"
                                    variant="light"
                                    color="red"
                                    onClick={() => createPlanMutation.mutate()}
                                    loading={createPlanMutation.isPending}
                                >
                                    Retry
                                </Button>
                            </Alert>
                        </div>
                    </div>
                )}

                {/* Connector-aware Tools & Suggested Prompts */}
                <div style={{ borderBottom: '1px solid #e5e7eb', background: '#ffffff' }}>
                    <div style={{ maxWidth: 900, margin: '0 auto', padding: '16px 24px' }}>
                        <Group align="flex-start" grow>
                            <Card withBorder radius="md" p="md">
                                <Group justify="space-between" mb="xs">
                                    <Group gap="xs">
                                        <Text fw={600} size="sm">Available tools</Text>
                                        {connectorsQuery.isFetching && <Badge size="xs" variant="light">Refreshing…</Badge>}
                                    </Group>
                                    <Badge size="xs" color={suggestedTools.length ? 'green' : 'gray'} variant="light">
                                        {suggestedTools.length} tool{suggestedTools.length === 1 ? '' : 's'}
                                    </Badge>
                                </Group>
                                {suggestedTools.length ? (
                                    <Group gap="xs" wrap="wrap">
                                        {suggestedTools.map((t) => (
                                            <Chip key={t.id} radius="xl" variant="light">
                                                <Tooltip label={t.description || ''}>{t.label}</Tooltip>
                                            </Chip>
                                        ))}
                                    </Group>
                                ) : (
                                    <Text size="xs" c="dimmed">Connect ERPNext or upload a CSV to unlock data-aware actions.</Text>
                                )}
                            </Card>
                            <Card withBorder radius="md" p="md">
                                <Group justify="space-between" mb="xs">
                                    <Text fw={600} size="sm">Suggested prompts</Text>
                                    <Badge size="xs" color={suggestedPrompts.length ? 'blue' : 'gray'} variant="light">
                                        {suggestedPrompts.length} suggestion{suggestedPrompts.length === 1 ? '' : 's'}
                                    </Badge>
                                </Group>
                                <Stack gap="xs">
                                    {suggestedPrompts.length ? suggestedPrompts.map((p) => (
                                        <Group key={p.id} justify="space-between" align="flex-start" gap="xs">
                                            <div style={{ flex: 1 }}>
                                                <Text fw={500} size="xs">{p.title}</Text>
                                                <Text size="xs" c="dimmed" lineClamp={3}>{p.text}</Text>
                                            </div>
                                            <Button size="xs" variant="light" onClick={() => handleInsertPrompt(p.text)}>Use</Button>
                                        </Group>
                                    )) : (
                                        <Text size="xs" c="dimmed">Connect a data source to get contextual one-click prompts.</Text>
                                    )}
                                </Stack>
                            </Card>
                        </Group>
                    </div>
                </div>

                {/* Coach Settings Modal */}
                <CoachSettings
                    opened={settingsOpen}
                    onClose={() => setSettingsOpen(false)}
                    selectedPersona={selectedPersona}
                    onPersonaChange={handlePersonaChange}
                    selectedDataSources={selectedDataSources}
                    onDataSourcesChange={handleDataSourcesChange}
                    includeEvidence={includeEvidence}
                    onIncludeEvidenceChange={handleIncludeEvidenceChange}
                    includeForecast={includeForecast}
                    onIncludeForecastChange={handleIncludeForecastChange}
                    personas={personas}
                    dataSources={dataSources}
                />

                {/* Context Panel - Collapsible */}
                <Collapse in={showContextPanel}>
                    <div style={{ borderBottom: '1px solid #e5e7eb', background: '#f9fafb', padding: '16px 0' }}>
                        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px' }}>
                            <Group align="flex-start" gap="lg">
                                {/* Health Score */}
                                <Card withBorder radius="md" p="md" style={{ flex: 1 }}>
                                    <Group justify="space-between" mb="xs">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed">
                                            Business Health
                                        </Text>
                                        <Badge
                                            size="lg"
                                            color={healthScore?.score >= 70 ? 'teal' : healthScore?.score >= 50 ? 'yellow' : 'red'}
                                        >
                                            {healthScore?.score || 0}/100
                                        </Badge>
                                    </Group>
                                    {healthScore?.breakdown && (
                                        <Stack gap="xs" mt="sm">
                                            <Group justify="space-between">
                                                <Text size="xs" c="dimmed">💰 Revenue</Text>
                                                <Progress value={healthScore.breakdown.revenue} size="sm" style={{ width: 60 }} />
                                            </Group>
                                            <Group justify="space-between">
                                                <Text size="xs" c="dimmed">⚙️ Operations</Text>
                                                <Progress value={healthScore.breakdown.operations} size="sm" style={{ width: 60 }} />
                                            </Group>
                                            <Group justify="space-between">
                                                <Text size="xs" c="dimmed">👥 Customer</Text>
                                                <Progress value={healthScore.breakdown.customer} size="sm" style={{ width: 60 }} />
                                            </Group>
                                        </Stack>
                                    )}
                                </Card>

                                {/* Active Goals */}
                                <Card withBorder radius="md" p="md" style={{ flex: 1 }}>
                                    <Group justify="space-between" mb="sm">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed">
                                            Active Goals
                                        </Text>
                                        <Badge size="sm" variant="light">
                                            {goalsData?.length || 0}
                                        </Badge>
                                    </Group>
                                    {goalsData && goalsData.length > 0 ? (
                                        <Stack gap="xs">
                                            {goalsData.slice(0, 2).map((goal: any) => (
                                                <div key={goal.id}>
                                                    <Text size="xs" fw={500} lineClamp={1}>
                                                        {goal.title}
                                                    </Text>
                                                    <Progress
                                                        value={(goal.current / goal.target) * 100}
                                                        size="xs"
                                                        radius="xl"
                                                        color="blue"
                                                        mt={4}
                                                    />
                                                </div>
                                            ))}
                                        </Stack>
                                    ) : (
                                        <Text size="xs" c="dimmed">No active goals</Text>
                                    )}
                                </Card>

                                {/* Pending Tasks */}
                                <Card withBorder radius="md" p="md" style={{ flex: 1 }}>
                                    <Group justify="space-between" mb="sm">
                                        <Text size="xs" fw={600} tt="uppercase" c="dimmed">
                                            Pending Tasks
                                        </Text>
                                        <Badge size="sm" variant="light" color="orange">
                                            {tasksData?.length || 0}
                                        </Badge>
                                    </Group>
                                    {tasksData && tasksData.length > 0 ? (
                                        <Stack gap={4}>
                                            {tasksData.slice(0, 3).map((task: any) => (
                                                <Text key={task.id} size="xs" lineClamp={1}>
                                                    • {task.title}
                                                </Text>
                                            ))}
                                        </Stack>
                                    ) : (
                                        <Text size="xs" c="dimmed">All caught up! 🎉</Text>
                                    )}
                                </Card>
                            </Group>
                        </div>
                    </div>
                </Collapse>

                {/* Chat Messages - ChatGPT Style */}
                <ScrollArea style={{ flex: 1 }} viewportRef={scrollAreaRef} offsetScrollbars>
                    <div style={{ maxWidth: 750, margin: '0 auto', padding: '32px 24px' }}>
                        <Stack gap="xl">
                            {visibleMessages.map((msg, idx) => (
                                <div key={msg.id}>
                                    <Group gap="md" align="flex-start" wrap="nowrap">
                                        {/* Avatar */}
                                        <div
                                            style={{
                                                width: 36,
                                                height: 36,
                                                borderRadius: '50%',
                                                background: msg.role === 'user' ? '#5865F2' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flexShrink: 0,
                                                fontSize: 18,
                                            }}
                                        >
                                            {msg.role === 'user' ? '👤' : '✨'}
                                        </div>

                                        {/* Message Content */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            {/* Agent name - static label only; selection via header */}
                                            <Text size="sm" fw={600} mb={8} c="#1f2937">
                                                {msg.role === 'user' ? (user?.name || 'You') :
                                                    selectedPersona === 'business_analyst' ? '📊 Business Analyst' :
                                                        selectedPersona === 'data_scientist' ? '📈 Data Scientist' :
                                                            selectedPersona === 'consultant' ? '💼 Consultant' :
                                                                selectedPersona === 'operations_manager' ? '⚙️ Operations Manager' :
                                                                    '🚀 Growth Strategist'
                                                }
                                            </Text>

                                            {/* Inline context summary under first assistant intro */}
                                            {msg.role === 'assistant' && idx === 0 && (
                                                <Card withBorder radius="md" p="xs" mb={8} style={{ background: '#f8fafc' }}>
                                                    <Group gap="xs" wrap="wrap">
                                                        <Badge size="sm" color={healthScore?.score >= 70 ? 'teal' : healthScore?.score >= 50 ? 'yellow' : 'red'} variant="light">Health {healthScore?.score || 0}</Badge>
                                                        {goalsData && goalsData.slice(0, 1).map((g: any) => (
                                                            <Badge size="sm" color="blue" key={g.id} variant="light" style={{ maxWidth: 200 }}>
                                                                {g.title.slice(0, 40)}{g.title.length > 40 ? '…' : ''}
                                                            </Badge>
                                                        ))}
                                                        <Badge size="sm" color="orange" variant="light">Tasks {tasksData?.length || 0}</Badge>
                                                    </Group>
                                                </Card>
                                            )}
                                            {/* Intent Chips */}
                                            {msg.role === 'assistant' && showAgentLabels && msg.intent && (
                                                <Badge size="xs" color="violet" variant="dot" mb="xs">
                                                    {msg.intent.replace('_', ' ')}
                                                </Badge>
                                            )}

                                            {/* Message Text */}
                                            {msg.role === 'assistant' ? (
                                                <Box
                                                    style={{
                                                        fontSize: '15px',
                                                        lineHeight: 1.7,
                                                        color: '#374151',
                                                        '& h1, & h2, & h3': {
                                                            marginTop: '1.25rem',
                                                            marginBottom: '0.75rem',
                                                            fontWeight: 600,
                                                            color: '#1f2937',
                                                        },
                                                        '& h1': { fontSize: '1.5rem' },
                                                        '& h2': { fontSize: '1.25rem' },
                                                        '& h3': { fontSize: '1.1rem' },
                                                        '& p': { marginBottom: '1rem' },
                                                        '& ul, & ol': {
                                                            marginLeft: '1.5rem',
                                                            marginBottom: '1rem',
                                                        },
                                                        '& li': { marginBottom: '0.5rem' },
                                                        '& strong': { fontWeight: 600, color: '#1f2937' },
                                                        '& code': {
                                                            background: '#f3f4f6',
                                                            padding: '0.125rem 0.375rem',
                                                            borderRadius: '0.25rem',
                                                            fontSize: '0.875em',
                                                            fontFamily: 'monospace',
                                                        },
                                                        '& pre': {
                                                            background: '#1f2937',
                                                            color: '#f9fafb',
                                                            padding: '1rem',
                                                            borderRadius: '0.5rem',
                                                            overflow: 'auto',
                                                        },
                                                        '& table': {
                                                            width: '100%',
                                                            borderCollapse: 'collapse',
                                                            marginBottom: '1rem',
                                                        },
                                                        '& th, & td': {
                                                            border: '1px solid #e5e7eb',
                                                            padding: '0.5rem',
                                                            textAlign: 'left',
                                                        },
                                                        '& th': {
                                                            background: '#f9fafb',
                                                            fontWeight: 600,
                                                        },
                                                    }}
                                                >
                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                                                </Box>
                                            ) : (
                                                <Text size="sm" style={{ color: '#374151', lineHeight: 1.6 }}>{msg.content}</Text>
                                            )}

                                            {/* Quick Action Buttons for latest assistant message */}
                                            {msg.role === 'assistant' && idx === visibleMessages.length - 1 && !isLoading && (
                                                <Group gap="xs" mt="md">
                                                    <Button
                                                        size="xs"
                                                        variant="light"
                                                        onClick={() => createPlanMutation.mutate()}
                                                        loading={createPlanMutation.isPending}
                                                    >
                                                        Create Plan
                                                    </Button>
                                                    <Button
                                                        size="xs"
                                                        variant="subtle"
                                                        onClick={() => setInput('Tell me more')}
                                                    >
                                                        Tell me more
                                                    </Button>
                                                    {msg.runUrl && (
                                                        <Button
                                                            size="xs"
                                                            variant="subtle"
                                                            onClick={() => {
                                                                window.open(msg.runUrl!, '_blank')
                                                                logAnalyticsEvent('trace_opened', { message_id: msg.id })
                                                            }}
                                                        >
                                                            Trace
                                                        </Button>
                                                    )}
                                                    <Group gap={4} ml="xs">
                                                        <Button size="compact-xs" variant={msg.feedback === 'up' ? 'filled' : 'subtle'} onClick={() => {
                                                            setAgentConversations((prev) => ({
                                                                ...prev,
                                                                [selectedPersona]: prev[selectedPersona].map(m => m.id === msg.id ? { ...m, feedback: m.feedback === 'up' ? undefined : 'up' } : m)
                                                            }))
                                                            logAnalyticsEvent('coach_feedback', { message_id: msg.id, rating: msg.feedback === 'up' ? 'clear' : 'up' })
                                                        }}>👍</Button>
                                                        <Button size="compact-xs" variant={msg.feedback === 'down' ? 'filled' : 'subtle'} onClick={() => {
                                                            setAgentConversations((prev) => ({
                                                                ...prev,
                                                                [selectedPersona]: prev[selectedPersona].map(m => m.id === msg.id ? { ...m, feedback: m.feedback === 'down' ? undefined : 'down' } : m)
                                                            }))
                                                            logAnalyticsEvent('coach_feedback', { message_id: msg.id, rating: msg.feedback === 'down' ? 'clear' : 'down' })
                                                        }}>👎</Button>
                                                    </Group>
                                                </Group>
                                            )}

                                            {/* Tool events (compact) */}
                                            {msg.role === 'assistant' && msg.toolEvents && msg.toolEvents.length > 0 && (
                                                <Card withBorder radius="sm" p="xs" mt="xs">
                                                    <Text size="xs" fw={600} c="dimmed" mb={4}>Run details</Text>
                                                    <Stack gap={4}>
                                                        {msg.toolEvents.map((ev, i) => (
                                                            <Group key={i} justify="space-between">
                                                                <Text size="xs">{ev.type}{ev.name ? ` • ${ev.name}` : ''}</Text>
                                                                <Text size="xs" c="dimmed">{ev.latency_ms ? `${ev.latency_ms} ms` : ev.ts?.slice(11, 19)}</Text>
                                                            </Group>
                                                        ))}
                                                    </Stack>
                                                </Card>
                                            )}
                                        </div>
                                    </Group>
                                </div>
                            ))}

                            {isLoading && (
                                <Group gap="md" align="flex-start" wrap="nowrap">
                                    <div
                                        style={{
                                            width: 36,
                                            height: 36,
                                            borderRadius: '50%',
                                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0,
                                            fontSize: 18,
                                        }}
                                    >
                                        ✨
                                    </div>
                                    <div>
                                        <Text size="sm" fw={600} mb={8} c="#1f2937">
                                            {selectedPersona === 'business_analyst' ? '� Business Analyst' :
                                                selectedPersona === 'data_scientist' ? '📈 Data Scientist' :
                                                    selectedPersona === 'consultant' ? '💼 Consultant' :
                                                        selectedPersona === 'operations_manager' ? '⚙️ Operations Manager' :
                                                            '🚀 Growth Strategist'
                                            }
                                        </Text>
                                        <Group gap="xs">
                                            <div className="typing-dots">
                                                <span>.</span>
                                                <span>.</span>
                                                <span>.</span>
                                            </div>
                                        </Group>
                                    </div>
                                </Group>
                            )}
                        </Stack>

                        {/* Quick Suggestions - After welcome message */}
                        {messages.length === 1 && (
                            <div style={{ marginTop: 24 }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                                    <Card
                                        withBorder
                                        radius="md"
                                        p="md"
                                        style={{ cursor: 'pointer', transition: 'all 0.2s', borderColor: '#e5e7eb' }}
                                        onClick={() => handleSendMessage('Create a weekly action plan for my business.')}
                                    >
                                        <Text size="sm" fw={500} mb={4}>Weekly Action Plan</Text>
                                        <Text size="xs" c="dimmed">Get organized with tasks</Text>
                                    </Card>
                                    <Card
                                        withBorder
                                        radius="md"
                                        p="md"
                                        style={{ cursor: 'pointer', transition: 'all 0.2s', borderColor: '#e5e7eb' }}
                                        onClick={() => handleSendMessage(`My health score is ${healthScore?.score || 0}. What are the top 3 actions to improve it?`)}
                                    >
                                        <Text size="sm" fw={500} mb={4}>Improve Health Score</Text>
                                        <Text size="xs" c="dimmed">Get quick wins</Text>
                                    </Card>
                                    <Card
                                        withBorder
                                        radius="md"
                                        p="md"
                                        style={{ cursor: 'pointer', transition: 'all 0.2s', borderColor: '#e5e7eb' }}
                                        onClick={() => handleSendMessage('Forecast next month revenue and highlight top 3 risk factors.')}
                                    >
                                        <Text size="sm" fw={500} mb={4}>Forecast Revenue</Text>
                                        <Text size="xs" c="dimmed">Predict & plan ahead</Text>
                                    </Card>
                                    <Card
                                        withBorder
                                        radius="md"
                                        p="md"
                                        style={{ cursor: 'pointer', transition: 'all 0.2s', borderColor: '#e5e7eb' }}
                                        onClick={() => handleSendMessage('Optimize inventory levels using OptiGuide playbook.')}
                                    >
                                        <Text size="sm" fw={500} mb={4}>Optimize Inventory</Text>
                                        <Text size="xs" c="dimmed">Reduce waste</Text>
                                    </Card>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                {/* Message Input - Fixed Bottom - ChatGPT Style */}
                <div style={{ borderTop: '1px solid #e5e7eb', background: 'white', flexShrink: 0, padding: '20px 0 24px' }}>
                    <div style={{ maxWidth: 750, margin: '0 auto', padding: '0 24px' }}>
                        <form
                            onSubmit={(e) => {
                                e.preventDefault()
                                if (input.trim() && !isLoading) {
                                    handleSendMessage(input)
                                    setInput('')
                                }
                            }}
                        >
                            <div style={{ position: 'relative' }}>
                                <Textarea
                                    placeholder="Message AI Business Coach..."
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
                                    maxRows={5}
                                    autosize
                                    disabled={isLoading}
                                    styles={{
                                        input: {
                                            border: '1px solid #d1d5db',
                                            borderRadius: '24px',
                                            padding: '12px 52px 12px 16px',
                                            fontSize: 15,
                                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                            '&:focus': {
                                                borderColor: '#5865F2',
                                                boxShadow: '0 0 0 3px rgba(88, 101, 242, 0.1)',
                                            }
                                        },
                                    }}
                                />
                                <Button
                                    type="submit"
                                    disabled={!input.trim() || isLoading}
                                    radius="xl"
                                    size="sm"
                                    style={{
                                        position: 'absolute',
                                        right: 8,
                                        bottom: 8,
                                        background: input.trim() ? '#5865F2' : '#e5e7eb',
                                        border: 'none',
                                    }}
                                >
                                    <IconSend size={18} />
                                </Button>
                            </div>
                        </form>

                        <Text size="xs" c="dimmed" ta="center" mt="sm">
                            AI can make mistakes. Check important info.
                        </Text>
                    </div>
                </div>
            </div>{/* end main column */}
        </div>
    )
}
