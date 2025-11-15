import { ActionIcon, Badge, Button, Card, Checkbox, Collapse, Divider, Drawer, Group, Menu, Progress, ScrollArea, Select, Stack, Tabs, Text, Textarea, useMantineTheme } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconChartBar, IconCheck, IconChevronDown, IconChevronLeft, IconChevronRight, IconDotsVertical, IconFileText, IconSend, IconSparkles, IconTarget } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { type AgentMode, type DataSource } from '../components/AgentModeSwitcher'
import CoachVisualization from '../components/CoachVisualization'
import CreateTaskModal from '../components/CreateTaskModal'
import { Markdown } from '../components/Markdown'
import { OptiGuideQuickActions } from '../components/OptiGuideQuickActions'
import { ReportDownloadButtons } from '../components/ReportDownloadButtons'
import { API_BASE, get, post, put } from '../lib/api'
import { Conversation, Message as ConvMessage, generateConversationTitle, loadConversations, saveConversation } from '../lib/conversations'
import { trackEvent } from '../lib/telemetry'
import { useAuthStore } from '../stores/auth'

// Simple message shape for the chat UI
export type Message = {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    metadata?: {
        phase?: string
        intent?: string
        total_tasks?: number
        task_id?: string
        task_status?: string
        data_sources?: string[]
        tools_used?: string[]
        report_id?: string
        visual_response?: any  // Multi-agent visualization data
    }
}

export default function CoachV5() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()
    const { chatId } = useParams<{ chatId?: string }>()
    const location = useLocation() as any
    const passedContext = (location?.state && location.state.context) || null
    const contextBootstrappedRef = useRef(false)
    const queryClient = useQueryClient()

    const isMobile = useMediaQuery('(max-width: 767px)')
    const theme = useMantineTheme()

    // Data
    const { data: goalsData = [] } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/goals`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30_000,
    })
    const { data: tasksData = [] } = useQuery({
        queryKey: ['tasks', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30_000,
    })
    const { data: healthScore } = useQuery({
        queryKey: ['health-score', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/health-score`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 60_000,
    })
    const { data: connectorsData = [] } = useQuery({
        queryKey: ['connectors', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/connectors`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 60_000,
    })

    // Conversation state
    const [conversations, setConversations] = useState<Conversation[]>(() => (tenantId ? loadConversations(tenantId) : []))
    const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(chatId)
    const [messages, setMessages] = useState<Message[]>([])
    const lastAssistant = useMemo(() => [...messages].reverse().find((m) => m.role === 'assistant'), [messages])

    // Goal link state
    const [selectedGoalId, setSelectedGoalId] = useState<string | null>(() => {
        try { return sessionStorage.getItem('latestGoalId') } catch { return null }
    })

    // Compose state
    const [input, setInput] = useState('')
    const [isSending, setIsSending] = useState(false)
    const [taskModalOpen, setTaskModalOpen] = useState(false)
    const [taskDraftTitle, setTaskDraftTitle] = useState<string | undefined>()
    const [agentMode, setAgentMode] = useState<AgentMode>('analyze')  // Agent mode switcher
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>([])  // Selected connectors
    const abortControllerRef = useRef<AbortController | null>(null)

    // Execution progress state
    const [executionPhase, setExecutionPhase] = useState<string | null>(null)
    const [executionProgress, setExecutionProgress] = useState<{ intent?: string; total_tasks?: number; completed_tasks?: number }>({});

    // Transform connectors to data sources for agent context
    const availableDataSources: DataSource[] = useMemo(() => {
        if (!connectorsData || !Array.isArray(connectorsData)) return [];

        return connectorsData.map((connector: any) => ({
            id: connector.connector_id || connector.id,
            type: connector.connector_type || connector.type || 'unknown',
            name: connector.display_name || connector.name || connector.connector_type,
            category: connector.category || 'data',
            icon: connector.icon || 'database',
            recordCount: connector.metadata?.total_records || connector.record_count || 0
        }));
    }, [connectorsData]);

    // Three-plane layout state
    const [showLeftPlane, setShowLeftPlane] = useState(true)
    const [showRightPlane, setShowRightPlane] = useState(false)
    const [conversationSearch, setConversationSearch] = useState('')
    const [leftView, setLeftView] = useState<'chat' | 'insights'>('chat')
    const [evidenceView, setEvidenceView] = useState<'sources' | 'reports' | 'graphs'>('sources')

    // Trip.com-inspired collapsible sections
    const [stepsExpanded, setStepsExpanded] = useState(true)
    const [tasksExpanded, setTasksExpanded] = useState(true)

    const hasInsights = useMemo(() => {
        try {
            return Boolean((lastAssistant?.metadata && (lastAssistant.metadata.visual_response || lastAssistant.metadata.intent)) || (typeof healthScore === 'object' && healthScore))
        } catch { return false }
    }, [lastAssistant, healthScore])

    // Health status in header
    const [healthStatus, setHealthStatus] = useState<'unknown' | 'ok' | 'down'>('unknown')
    const [lastHealthCheck, setLastHealthCheck] = useState<Date | null>(null)
    useEffect(() => {
        let cancelled = false
        const check = async () => {
            try {
                const res = await fetch(`${API_BASE}/health`)
                if (cancelled) return
                setHealthStatus(res.ok ? 'ok' : 'down')
                setLastHealthCheck(new Date())
            } catch {
                if (!cancelled) {
                    setHealthStatus('down')
                    setLastHealthCheck(new Date())
                }
            }
        }
        check()
        const id = setInterval(check, 60_000)
        return () => { cancelled = true; clearInterval(id) }
    }, [])

    // Inline goal picker flow for Save as Task when no goal linked
    const [showGoalPicker, setShowGoalPicker] = useState(false)

    // Task creation
    const createTaskMutation = useMutation({
        mutationFn: async (payload: any) => post(`/v1/tenants/${tenantId}/tasks`, payload, apiToken),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', tenantId] }),
    })
    const updateTaskMutation = useMutation({
        mutationFn: async ({ taskId, data }: { taskId: string; data: any }) => put(`/v1/tenants/${tenantId}/tasks/${taskId}`, data, apiToken),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', tenantId] }),
    })

    // Create goal from insight (lowest health dimension)
    const createGoalFromInsightMutation = useMutation({
        mutationFn: async () => {
            const breakdown = (healthScore as any)?.breakdown || {}
            const dims: Array<{ key: 'revenue' | 'operations' | 'customer'; label: string; unit: string }> = [
                { key: 'revenue', label: 'Revenue', unit: 'USD' },
                { key: 'operations', label: 'Operations', unit: 'Units' },
                { key: 'customer', label: 'Customer', unit: 'Customers' },
            ]
            const lowest = dims.reduce((min, d) => ({
                ...min,
                cand: (min as any).cand?.score <= (breakdown[d.key] ?? 0) ? (min as any).cand : { key: d.key, score: breakdown[d.key] ?? 0, unit: d.unit }
            }), { cand: { key: 'operations', score: breakdown.operations ?? 0, unit: 'Units' } } as any).cand

            const deadline = new Date(); deadline.setDate(deadline.getDate() + 30)
            const payload = {
                title: `Improve ${lowest.key} health` as string,
                description: `Created from health insight. Current ${lowest.key} health is ${(lowest.score ?? 0)}/100.`,
                current: 0,
                target: 100,
                unit: lowest.unit,
                category: lowest.key,
                deadline: deadline.toISOString().split('T')[0],
                auto_tracked: false,
            }
            const created = await post(`/v1/tenants/${tenantId}/goals`, payload, apiToken)
            return created
        },
        onSuccess: (created: any) => {
            try { if (created?.id) sessionStorage.setItem('latestGoalId', created.id) } catch { }
            setSelectedGoalId(created?.id || null)
            queryClient.invalidateQueries({ queryKey: ['goals', tenantId] })
        }
    })

    // Load from URL if present
    useEffect(() => {
        if (!tenantId) return
        const list = loadConversations(tenantId)
        setConversations(list)
        if (chatId) {
            const found = list.find((c) => c.id === chatId)
            if (found) {
                setMessages(found.messages as unknown as Message[])
                setCurrentConversationId(found.id)
                if (found.goalId) setSelectedGoalId(found.goalId)
                return
            }
        }
        // If no existing conversation and no chatId, seed welcome
        if (!chatId) {
            setMessages([
                {
                    id: 'hello',
                    role: 'assistant',
                    content:
                        selectedGoalId
                            ? `You're working on this goal. Ask me to draft an action plan or create tasks.\n\n• "Create a weekly action plan"\n• "Break down this goal into 5 tasks"\n• "Suggest the next best action"`
                            : `Welcome! Link this chat to a goal to keep everything in one place.\n\n• "Help me set a goal"\n• "Create an action plan for revenue growth"`,
                    timestamp: new Date(),
                },
            ])
        }
    }, [tenantId, chatId])

    // Start chat based on passed dashboard context (if present)
    useEffect(() => {
        if (!tenantId || !apiToken) return
        if (contextBootstrappedRef.current) return
        if (!passedContext) return
        contextBootstrappedRef.current = true

        // Show initial progress and activate "thinking" indicator
        setIsSending(true)
        setExecutionPhase('planning')
        setExecutionProgress({ intent: 'analyzing_dashboard', total_tasks: 4, completed_tasks: 0 })

        const summaryParts: string[] = []
        // Handle healthScore as either object or number
        const healthScoreValue = typeof passedContext.healthScore === 'object'
            ? passedContext.healthScore.score
            : passedContext.healthScore
        summaryParts.push(`Today's health score is ${healthScoreValue}/100 (prev ${passedContext.previousScore}).`)
        if (Array.isArray(passedContext.alerts) && passedContext.alerts.length) {
            const a = passedContext.alerts.slice(0, 3).map((x: any) => x.title).join('; ')
            summaryParts.push(`Needs attention: ${a}.`)
        }
        if (Array.isArray(passedContext.signals) && passedContext.signals.length) {
            const s = passedContext.signals.slice(0, 3).map((x: any) => x.title).join('; ')
            summaryParts.push(`Positive: ${s}.`)
        }
        if (Array.isArray(passedContext.goals) && passedContext.goals.length) {
            const g = passedContext.goals.slice(0, 2).map((x: any) => x.title).join('; ')
            summaryParts.push(`Top goals: ${g}.`)
        }
        const pendingTasks = Array.isArray(passedContext.tasks) ? passedContext.tasks.filter((t: any) => t.status !== 'completed') : []
        summaryParts.push(`Pending tasks: ${pendingTasks.length}.`)
        const prompt = `${summaryParts.join(' ')} Based on this, propose the next best actions for the next 7 days.`

        // Kick off streaming with context prompt
        const assistantId = `${Date.now()}-a`
        setMessages((prev) => [
            ...prev,
            { id: `${Date.now()}-u`, role: 'user', content: prompt, timestamp: new Date() },
            { id: assistantId, role: 'assistant', content: '', timestamp: new Date() }
        ])

            ; (async () => {
                try {
                    setExecutionProgress({ intent: 'analyzing_dashboard', total_tasks: 4, completed_tasks: 1 })
                    const controller = new AbortController()
                    abortControllerRef.current = controller
                    const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream/v2`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(apiToken ? { Authorization: `Bearer ${apiToken}` } : {}),
                        },
                        body: JSON.stringify({
                            message: prompt,
                            conversation_history: [],
                            persona: 'business_analyst',
                            context: passedContext,
                        }),
                        signal: controller.signal,
                    })

                    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

                    setExecutionPhase('task_execution')
                    setExecutionProgress({ intent: 'analyzing_dashboard', total_tasks: 4, completed_tasks: 2 })

                    const reader = response.body.getReader()
                    const decoder = new TextDecoder()
                    let full = ''
                    let collectedMetadata: any = {}
                    let dataSources = new Set<string>()
                    let toolsUsed = new Set<string>()
                    let taskCount = 0

                    while (true) {
                        const { done, value } = await reader.read()
                        if (done) break
                        const lines = decoder.decode(value).split('\n')
                        for (const line of lines) {
                            if (!line.startsWith('data: ')) continue
                            try {
                                const data = JSON.parse(line.slice(6))
                                if (data.delta) full += data.delta
                                if (data.metadata) {
                                    collectedMetadata = { ...collectedMetadata, ...data.metadata }
                                    if (data.metadata.phase) setExecutionPhase(data.metadata.phase)

                                    // Track task progress
                                    if (data.metadata.total_tasks) {
                                        const completedTasks = data.metadata.completed_tasks || taskCount
                                        setExecutionProgress({
                                            intent: data.metadata.intent || 'analyzing_dashboard',
                                            total_tasks: data.metadata.total_tasks,
                                            completed_tasks: completedTasks
                                        })
                                    }
                                    if (data.metadata.task_status === 'completed') {
                                        taskCount++
                                        setExecutionProgress((prev) => ({
                                            ...prev,
                                            completed_tasks: taskCount
                                        }))
                                    }
                                }
                                setMessages((prev) => prev.map((m) => (m.id === assistantId ? {
                                    ...m,
                                    content: full,
                                    metadata: {
                                        ...collectedMetadata,
                                        data_sources: Array.from(dataSources),
                                        tools_used: Array.from(toolsUsed)
                                    }
                                } : m)))
                            } catch { }
                        }
                    }

                    // Clear progress on completion
                    setExecutionPhase(null)
                    setExecutionProgress({})
                    setIsSending(false)
                } catch (e: any) {
                    setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: `⚠️ Error: ${e?.message || 'failed to reach coach'}` } : m)))
                } finally {
                    abortControllerRef.current = null
                    setIsSending(false)
                }
            })()
    }, [passedContext, tenantId, apiToken])

    // Persist conversation whenever messages change
    useEffect(() => {
        if (!tenantId) return
        if (messages.length === 0) return

        const conversationId = currentConversationId || `conv-${Date.now()}`
        const title = currentConversationId
            ? conversations.find((c) => c.id === conversationId)?.title || generateConversationTitle(messages as unknown as ConvMessage[])
            : generateConversationTitle(messages as unknown as ConvMessage[])

        const conversation: Conversation = {
            id: conversationId,
            title,
            messages: messages as unknown as ConvMessage[],
            createdAt: currentConversationId ? (conversations.find((c) => c.id === conversationId)?.createdAt || new Date()) : new Date(),
            updatedAt: new Date(),
            agent: 'business_analyst',
            tenantId,
            goalId: selectedGoalId || undefined,
        }
        saveConversation(conversation, tenantId)
        setConversations(loadConversations(tenantId))
        if (!currentConversationId) setCurrentConversationId(conversationId)
    }, [messages, selectedGoalId])

    const activeGoals = useMemo(() => goalsData.filter((g: any) => g.status === 'active'), [goalsData])
    const goalOptions = activeGoals.map((g: any) => {
        const p = g.target ? Math.min((g.current / g.target) * 100, 100) : 0
        const days = (() => {
            try {
                const d = new Date(g.deadline)
                const now = new Date()
                return Math.max(0, Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)))
            } catch { return undefined }
        })()
        const suffix = `${Math.round(p)}%${typeof days === 'number' ? ` · ${days}d left` : ''}`
        return { label: `${g.title} (${suffix})`, value: g.id }
    })

    const linkedGoal = activeGoals.find((g: any) => g.id === selectedGoalId)
    const goalTasks = useMemo(() => tasksData.filter((t: any) => t.goal_id === selectedGoalId), [tasksData, selectedGoalId])

    // Filtered conversations based on search
    const filteredConversations = useMemo(() => {
        if (!conversationSearch.trim()) return conversations
        const query = conversationSearch.toLowerCase()
        return conversations.filter(c =>
            c.title.toLowerCase().includes(query) ||
            c.messages.some(m => m.content.toLowerCase().includes(query))
        )
    }, [conversations, conversationSearch])
    const goalProgress = useMemo(() => {
        if (!linkedGoal) return 0
        const p = linkedGoal.target ? Math.min((linkedGoal.current / linkedGoal.target) * 100, 100) : 0
        return Math.round(p)
    }, [linkedGoal])

    const addAssistantMessage = (content: string) =>
        setMessages((prev) => [...prev, { id: `${Date.now()}-a`, role: 'assistant', content, timestamp: new Date() }])

    // Seed a simple sample plan to show the experience without backend calls
    const addSamplePlan = () => {
        const sample = `**Your plan for this week**

- Review top 5 SKUs by cost and reduce safety stock where demand is stable
- Place one consolidated order to cut ordering fees by ~20%
- Tag overstocked items for discount and bundle offers

Tip: Link a goal to save these as tasks and track progress.`
        addAssistantMessage(sample)
    }

    const handleSend = async () => {
        const value = input.trim()
        if (!value) return
        const userId = `${Date.now()}-u`
        setMessages((prev) => [...prev, { id: userId, role: 'user', content: value, timestamp: new Date() }])
        setInput('')
        setIsSending(true)
        trackEvent('chat_message_sent', { tenantId, linked_goal: !!selectedGoalId })

        // Placeholder assistant for streaming
        const assistantId = `${Date.now()}-a`
        setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '', timestamp: new Date() }])

        try {
            const controller = new AbortController()
            abortControllerRef.current = controller

            // Use SSE streaming for real-time responses
            const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiToken ? { Authorization: `Bearer ${apiToken}` } : {}),
                },
                body: JSON.stringify({
                    question: value,
                    stream: true,
                }),
                signal: controller.signal,
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.error || `HTTP ${response.status}`)
            }

            // Handle Server-Sent Events (SSE) stream
            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            let buffer = ''
            let fullNarrative = ''
            let streamDone = false

            if (reader) {
                while (true) {
                    const { done, value: chunk } = await reader.read()
                    if (done) break

                    buffer += decoder.decode(chunk, { stream: true })
                    const lines = buffer.split('\n')
                    buffer = lines.pop() || ''

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6))

                                if (data.done) {
                                    streamDone = true
                                    break
                                }

                                if (data.error) {
                                    throw new Error(data.error)
                                }

                                // Update message with streaming narrative content
                                if (data.narrative) {
                                    fullNarrative = data.narrative
                                    setMessages((prev) =>
                                        prev.map((m) => (m.id === assistantId ? { ...m, content: fullNarrative } : m))
                                    )
                                }
                            } catch (parseErr) {
                                console.warn('Failed to parse SSE data:', line)
                            }
                        }
                    }

                    // Exit outer loop if stream is done
                    if (streamDone) break
                }
            }

            // If no narrative was received, show a placeholder
            if (!fullNarrative) {
                fullNarrative = 'Response completed with no content'
                setMessages((prev) =>
                    prev.map((m) => (m.id === assistantId ? { ...m, content: fullNarrative } : m))
                )
            }

            trackEvent('assistant_plan_generated', { tenantId, linked_goal: !!selectedGoalId, contains_bullets: /\n-/.test(fullNarrative) })
            setExecutionPhase(null)
            setExecutionProgress({})
        } catch (err: any) {
            if (err.name === 'AbortError') {
                setMessages((prev) => prev.filter((m) => m.id !== assistantId))
            } else {
                const errorMsg = err.message || 'Failed to send message'
                setMessages((prev) =>
                    prev.map((m) => (m.id === assistantId ? { ...m, content: `⚠️ Error: ${errorMsg}` } : m))
                )
            }
            setExecutionPhase(null)
            setExecutionProgress({})
        } finally {
            setIsSending(false)
            abortControllerRef.current = null
        }
    }

    const extractBullets = (text: string) => {
        return text
            .split('\n')
            .map((l) => l.trim())
            .filter((l) => /^(?:[-*•]|\d+\.)\s+/.test(l))
            .map((l) => l.replace(/^(?:[-*•]|\d+\.)\s+/, ''))
    }

    // Detect if a message contains an actionable multi-step plan suitable to convert into tasks
    const planBullets = useMemo(() => {
        const b = lastAssistant ? extractBullets(lastAssistant.content) : []
        return b
            .map((t) => t.replace(/^"|"$/g, '').trim()) // remove surrounding quotes
            .filter((t) => t.length >= 10) // ignore super short
    }, [lastAssistant])

    const isActionPlan = useMemo(() => {
        if (planBullets.length >= 4) return true
        // If 3 bullets and at least 2 start with an imperative verb
        const imperative = /^(create|draft|prepare|plan|break|define|set|analyze|review|optimize|implement|schedule|estimate|collect|prioritize|assign)\b/i
        const imperativeCount = planBullets.filter((t) => imperative.test(t)).length
        return planBullets.length >= 3 && imperativeCount >= 2
    }, [planBullets])

    const createTasksFromLastAssistant = async () => {
        if (!selectedGoalId) {
            addAssistantMessage('Please link this chat to a goal first (top bar).')
            return
        }
        const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')
        if (!lastAssistant) return

        const bullets = extractBullets(lastAssistant.content)
        if (bullets.length === 0) {
            addAssistantMessage('I could not find bullet points to convert. Ask me to propose tasks first!')
            return
        }

        // Create up to 5 tasks
        const toCreate = bullets.slice(0, 5)
        for (const title of toCreate) {
            try {
                await createTaskMutation.mutateAsync({ title, status: 'todo', priority: 'medium', horizon: 'weekly', goal_id: selectedGoalId })
            } catch (_e) {
                // Fail silently; user will still see assistant feedback
            }
        }
        addAssistantMessage(`Created ${toCreate.length} task(s) for this goal.`)
        trackEvent('tasks_created_from_reply', { tenantId, count: toCreate.length })
    }

    const openSaveAsTask = (title?: string) => {
        if (!selectedGoalId) {
            // Ask user to pick a goal inline
            setTaskDraftTitle(title)
            setShowGoalPicker(true)
            return
        }
        setTaskDraftTitle(title)
        setTaskModalOpen(true)
    }

    const [showOptiGuide, setShowOptiGuide] = useState(false)
    const [optiGuideInitQuestion, setOptiGuideInitQuestion] = useState<string | undefined>()
    const [optiGuideInitMode, setOptiGuideInitMode] = useState<'what-if' | 'why' | undefined>()

    return (
        <div style={{ background: '#f5f5f5', minHeight: '100vh', padding: '12px' }}>
            {/* Simplified header */}
            <Group justify="space-between" align="center" mb="sm" px="md" py="xs" style={{
                background: 'white',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
            }}>
                <Group gap="md">
                    <Text size="lg" fw={700} c="dark">✨ AI Business Coach</Text>
                    {linkedGoal && (
                        <>
                            <Divider orientation="vertical" />
                            <Group gap={6}>
                                <Text size="sm" c="dimmed">Working on:</Text>
                                <Text size="sm" fw={600} lineClamp={1} style={{ maxWidth: '200px' }}>{linkedGoal.title}</Text>
                            </Group>
                        </>
                    )}
                </Group>
                <Group gap="xs">
                    {!linkedGoal && (
                        <Select
                            placeholder="Pick a goal to start"
                            data={goalOptions}
                            value={selectedGoalId}
                            onChange={(v) => setSelectedGoalId(v)}
                            searchable
                            clearable
                            size="xs"
                            w={200}
                            styles={{
                                input: { height: '30px', fontSize: '12px' }
                            }}
                        />
                    )}
                    <Button
                        size="xs"
                        variant={linkedGoal ? "light" : "filled"}
                        onClick={() => navigate('/goals')}
                    >
                        {linkedGoal ? 'Change goal' : '+ Create goal'}
                    </Button>
                    <Button
                        size="xs"
                        variant="light"
                        color="violet"
                        onClick={() => setShowOptiGuide(true)}
                    >
                        Run scenario
                    </Button>
                </Group>
            </Group>

            {/* Trip.com-style three-plane layout */}
            <div style={{ display: 'flex', gap: '8px', position: 'relative', height: 'calc(100vh - 160px)' }}>
                {/* LEFT PLANE: AI Assistant + Business Insights */}
                {showLeftPlane && (
                    <Card withBorder={false} radius="md" p={0} shadow="xs" style={{ width: '360px', flexShrink: 0, background: 'white', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                        <div style={{ padding: '8px 12px', borderBottom: `1px solid ${theme.colors.gray[2]}` }}>
                            <Group justify="space-between" align="center">
                                <Group gap="xs">
                                    <div style={{
                                        width: '28px',
                                        height: '28px',
                                        borderRadius: '6px',
                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '14px'
                                    }}>
                                        ✨
                                    </div>
                                    <Text size="xs" fw={700}>AI Assistant</Text>
                                </Group>
                                <ActionIcon variant="subtle" color="gray" size="xs" onClick={() => setShowLeftPlane(false)}>
                                    <IconChevronLeft size={14} />
                                </ActionIcon>
                            </Group>
                        </div>

                        {/* Business Insights - Collapsible Section (hidden unless insights exist) */}
                        {hasInsights && (
                            <div style={{ borderBottom: `1px solid ${theme.colors.gray[2]}`, background: theme.colors.blue[0] }}>
                                <Button
                                    fullWidth
                                    variant="subtle"
                                    color="blue"
                                    size="xs"
                                    onClick={() => setLeftView(leftView === 'insights' ? 'chat' : 'insights')}
                                    styles={{
                                        root: {
                                            borderRadius: 0,
                                            padding: '6px 10px',
                                            height: 'auto'
                                        }
                                    }}
                                >
                                    <Group justify="space-between" style={{ width: '100%' }}>
                                        <Group gap={6}>
                                            <IconChartBar size={12} />
                                            <Text size="xs" fw={600}>Business Insights</Text>
                                        </Group>
                                        <Text size="xs">
                                            {leftView === 'insights' ? '▼' : '▶'}
                                        </Text>
                                    </Group>
                                </Button>

                                {leftView === 'insights' && (
                                    <ScrollArea style={{ maxHeight: '200px' }} p={6}>
                                        <Stack gap={6}>
                                            {/* Compact Health Score */}
                                            {typeof (healthScore as any)?.score === 'number' && (
                                                <Card withBorder radius="sm" p="xs">
                                                    <Group justify="space-between" mb={4}>
                                                        <Text size="xs" fw={600}>Health Score</Text>
                                                        <Badge size="sm" color={(healthScore as any).score >= 70 ? 'teal' : (healthScore as any).score >= 40 ? 'yellow' : 'red'}>
                                                            {(healthScore as any).score}/100
                                                        </Badge>
                                                    </Group>
                                                    <Progress
                                                        value={(healthScore as any).score}
                                                        radius="sm"
                                                        size="xs"
                                                        color={(healthScore as any).score >= 70 ? 'teal' : (healthScore as any).score >= 40 ? 'yellow' : 'red'}
                                                    />
                                                </Card>
                                            )}
                                            {/* Compact Goal Progress */}
                                            {linkedGoal && (
                                                <Card withBorder radius="sm" p="xs">
                                                    <Group justify="space-between" mb={4}>
                                                        <Text size="xs" fw={600} lineClamp={1} style={{ flex: 1 }}>{linkedGoal.title}</Text>
                                                        <Badge size="sm" color={goalProgress >= 70 ? 'teal' : 'blue'}>
                                                            {goalProgress}%
                                                        </Badge>
                                                    </Group>
                                                    <Progress value={goalProgress} radius="sm" size="xs" color={goalProgress >= 70 ? 'teal' : 'blue'} />
                                                </Card>
                                            )}
                                        </Stack>
                                    </ScrollArea>
                                )}
                            </div>
                        )}

                        {/* AI Chat Section */}
                        <ScrollArea style={{ flex: 1 }} p={8}>
                            <Stack gap="md">
                                {messages.map((m) => (
                                    <div key={m.id} style={{ display: 'flex', gap: '8px', flexDirection: m.role === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
                                        <div style={{
                                            width: '28px',
                                            height: '28px',
                                            borderRadius: '8px',
                                            background: m.role === 'assistant' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : theme.colors.brand[6],
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0,
                                            fontSize: '13px'
                                        }}>
                                            {m.role === 'assistant' ? '✨' : (user?.name?.[0]?.toUpperCase() || 'U')}
                                        </div>
                                        <div style={{ flex: 1, maxWidth: '260px' }}>
                                            <div style={{
                                                padding: '8px 10px',
                                                borderRadius: '10px',
                                                background: m.role === 'assistant' ? theme.colors.gray[0] : theme.colors.brand[6],
                                                border: m.role === 'assistant' ? `1px solid ${theme.colors.gray[2]}` : 'none'
                                            }}>
                                                {m.role === 'assistant' ? (
                                                    <div style={{
                                                        fontSize: '13px',
                                                        lineHeight: '1.6',
                                                        color: theme.colors.dark[7]
                                                    }} className="markdown-content">
                                                        {/* Multi-agent visualizations */}
                                                        {m.metadata?.visual_response && (
                                                            <CoachVisualization visualResponse={m.metadata.visual_response} />
                                                        )}

                                                        {/* Text content (if any) */}
                                                        {m.content && <Markdown content={m.content} size="sm" />}
                                                    </div>
                                                ) : (
                                                    <Text size="xs" c="white" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                                                        {m.content}
                                                    </Text>
                                                )}
                                            </div>
                                            <Text size="xs" c="dimmed" mt={3} style={{ textAlign: m.role === 'user' ? 'right' : 'left' }}>
                                                {m.timestamp instanceof Date ? m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                                            </Text>
                                        </div>
                                    </div>
                                ))}
                                {isSending && (
                                    <Stack gap={8}>
                                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                            <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                <Text size="sm" c="white">✨</Text>
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <Text size="sm" c="dimmed" fs="italic">
                                                    {executionPhase === 'planning' && 'Planning analysis...'}
                                                    {executionPhase === 'task_execution' && 'Analyzing your business...'}
                                                    {executionPhase === 'report_generated' && 'Generating insights...'}
                                                    {executionPhase === 'analysis' && 'Crafting recommendations...'}
                                                    {!executionPhase && 'Thinking...'}
                                                </Text>
                                                {executionProgress.total_tasks && executionProgress.total_tasks > 0 && (
                                                    <>
                                                        <Progress
                                                            value={(executionProgress.completed_tasks || 0) / executionProgress.total_tasks * 100}
                                                            size="xs"
                                                            radius="xl"
                                                            color="violet"
                                                            mt={4}
                                                            animated
                                                        />
                                                        <Text size="xs" c="dimmed" mt={2}>
                                                            {executionProgress.completed_tasks || 0} of {executionProgress.total_tasks} tasks completed
                                                        </Text>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </Stack>
                                )}
                            </Stack>
                        </ScrollArea>

                        <div style={{ borderTop: `1px solid ${theme.colors.gray[2]}`, background: '#fafafa', padding: '8px' }}>
                            <Stack gap={6}>
                                {/* Suggested prompts - Trip.com style */}
                                {messages.length === 0 && (
                                    <Stack gap={4}>
                                        <Text size="xs" c="dimmed" fw={500} px={1}>Try asking:</Text>
                                        <Group gap={4} wrap="wrap">
                                            {[
                                                'Create a weekly action plan',
                                                'Analyze my revenue trends',
                                                'Suggest 5 quick wins'
                                            ].map((prompt) => (
                                                <Button
                                                    key={prompt}
                                                    size="xs"
                                                    variant="light"
                                                    color="gray"
                                                    radius="xl"
                                                    onClick={() => setInput(prompt)}
                                                    styles={{
                                                        root: {
                                                            height: '24px',
                                                            fontSize: '10px',
                                                            fontWeight: 500,
                                                            padding: '0 10px'
                                                        }
                                                    }}
                                                >
                                                    {prompt}
                                                </Button>
                                            ))}
                                        </Group>
                                    </Stack>
                                )}

                                <Group gap={6} align="flex-end">
                                    <Textarea
                                        placeholder={
                                            linkedGoal
                                                ? `Ask about ${linkedGoal.title.toLowerCase()}...`
                                                : "Ask anything about your business..."
                                        }
                                        minRows={1}
                                        maxRows={3}
                                        autosize
                                        value={input}
                                        onChange={(e) => setInput(e.currentTarget.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault()
                                                if (input.trim() && !isSending) handleSend()
                                            }
                                        }}
                                        radius="md"
                                        size="xs"
                                        styles={{
                                            input: {
                                                background: 'white',
                                                border: `1px solid ${theme.colors.gray[3]}`,
                                                fontSize: '12px',
                                                padding: '6px 8px'
                                            }
                                        }}
                                        style={{ flex: 1 }}
                                    />
                                    {isSending ? (
                                        <Button size="xs" variant="light" color="red" radius="md" onClick={() => abortControllerRef.current?.abort()} h={28}>
                                            Stop
                                        </Button>
                                    ) : (
                                        <Button
                                            onClick={handleSend}
                                            disabled={!input.trim()}
                                            size="xs"
                                            radius="md"
                                            color="brand"
                                            style={{ minWidth: '50px' }}
                                            h={28}
                                        >
                                            <IconSend size={14} />
                                        </Button>
                                    )}
                                </Group>
                            </Stack>
                        </div>
                    </Card>
                )}

                {/* Scenarios Drawer */}
                <Drawer
                    opened={showOptiGuide}
                    onClose={() => setShowOptiGuide(false)}
                    position="right"
                    size="xl"
                    title="What‑If & Why Scenarios"
                >
                    <OptiGuideQuickActions
                        onClose={() => setShowOptiGuide(false)}
                        initialMode={optiGuideInitMode}
                        initialQuestion={optiGuideInitQuestion}
                        onSendToChat={(content) => {
                            // Add the scenario result as an assistant message
                            addAssistantMessage(content)
                            setShowOptiGuide(false)

                            // Optionally auto-populate a follow-up prompt
                            // This helps users understand they can continue the conversation
                            setTimeout(() => {
                                setInput('Tell me more about this analysis')
                            }, 100)
                        }}
                    />
                </Drawer>

                {/* Inline Goal Picker for Save as Task */}
                <Drawer
                    opened={showGoalPicker}
                    onClose={() => setShowGoalPicker(false)}
                    position="top"
                    size="sm"
                    title="Pick a goal to save tasks"
                >
                    <Stack gap="md">
                        <Text size="sm" c="dimmed">Select which goal these tasks should be linked to:</Text>
                        <Select
                            placeholder="Select goal"
                            data={goalOptions}
                            value={selectedGoalId}
                            onChange={(v) => setSelectedGoalId(v)}
                            searchable
                            clearable
                            size="sm"
                        />
                        <Group justify="flex-end" gap="xs">
                            <Button variant="default" size="xs" onClick={() => setShowGoalPicker(false)}>Cancel</Button>
                            <Button
                                size="xs"
                                color="brand"
                                disabled={!selectedGoalId}
                                onClick={() => {
                                    setShowGoalPicker(false)
                                    setTaskModalOpen(true)
                                }}
                            >
                                Continue
                            </Button>
                        </Group>
                    </Stack>
                </Drawer>

                {/* Temporarily hide old insights - will be removed */}
                {false && (
                    // OLD INSIGHTS TAB
                    <ScrollArea style={{ flex: 1 }} p="sm">
                        <Stack gap="sm">
                            {/* Business Health Score */}
                            <div>
                                <Text size="xs" c="dimmed" fw={700} tt="uppercase" mb="xs" style={{ letterSpacing: '0.5px' }}>
                                    📊 Health Score
                                </Text>
                                <Card withBorder radius="md" p="sm">
                                    {typeof (healthScore as any)?.score === 'number' ? (
                                        <>
                                            <Group justify="space-between" mb="md">
                                                <div>
                                                    <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>Overall Score</Text>
                                                    <Text size="xl" fw={700} c={(healthScore as any).score >= 70 ? 'teal' : (healthScore as any).score >= 40 ? 'yellow' : 'red'}>
                                                        {(healthScore as any).score}<Text span size="lg" c="dimmed">/100</Text>
                                                    </Text>
                                                </div>
                                                <div style={{
                                                    width: '48px',
                                                    height: '48px',
                                                    borderRadius: '12px',
                                                    background: (healthScore as any).score >= 70 ? theme.colors.teal[0] : (healthScore as any).score >= 40 ? theme.colors.yellow[0] : theme.colors.red[0],
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center'
                                                }}>
                                                    <Text size="lg">
                                                        {(healthScore as any).score >= 70 ? '🎉' : (healthScore as any).score >= 40 ? '📈' : '⚠️'}
                                                    </Text>
                                                </div>
                                            </Group>
                                            <Progress
                                                value={(healthScore as any).score}
                                                radius="xl"
                                                mb="sm"
                                                size="md"
                                                color={(healthScore as any).score >= 70 ? 'teal' : (healthScore as any).score >= 40 ? 'yellow' : 'red'}
                                            />
                                            {(healthScore as any)?.breakdown && (
                                                <Stack gap="sm" mb="sm">
                                                    {(['revenue', 'operations', 'customer'] as const).map((k) => {
                                                        const val = (healthScore as any)?.breakdown?.[k]
                                                        if (typeof val !== 'number') return null
                                                        const color = val >= 70 ? 'teal' : val >= 40 ? 'yellow' : 'red'
                                                        const emoji = k === 'revenue' ? '💰' : k === 'operations' ? '⚙️' : '👥'
                                                        const label = k.charAt(0).toUpperCase() + k.slice(1)
                                                        return (
                                                            <div key={`br-${k}`}>
                                                                <Group justify="space-between" mb={6}>
                                                                    <Group gap="6px">
                                                                        <Text size="md">{emoji}</Text>
                                                                        <Text size="xs" fw={600}>{label}</Text>
                                                                    </Group>
                                                                    <Badge size="sm" radius="md" variant="light" color={color} style={{ fontWeight: 600 }}>
                                                                        {val}
                                                                    </Badge>
                                                                </Group>
                                                                <Progress value={val} radius="xl" color={color} size="sm" />
                                                            </div>
                                                        )
                                                    })}
                                                </Stack>
                                            )}
                                            <Button
                                                fullWidth
                                                size="xs"
                                                variant="light"
                                                color="brand"
                                                radius="md"
                                                leftSection={<IconSparkles size={14} />}
                                                loading={createGoalFromInsightMutation.isPending}
                                                onClick={() => createGoalFromInsightMutation.mutate()}
                                            >
                                                Create Goal from Insight
                                            </Button>
                                        </>
                                    ) : (
                                        <div style={{ textAlign: 'center', padding: '24px 16px' }}>
                                            <Text size="lg" mb="xs">📊</Text>
                                            <Text size="xs" c="dimmed">Connect data to see health score</Text>
                                        </div>
                                    )}
                                </Card>
                            </div>

                            {/* Goal Progress */}
                            <div>
                                <Text size="xs" c="dimmed" fw={700} tt="uppercase" mb="xs" style={{ letterSpacing: '0.5px' }}>
                                    🎯 Goal Progress
                                </Text>
                                <Card withBorder radius="md" p="sm">
                                    {linkedGoal ? (
                                        <>
                                            <Group justify="space-between" mb="md">
                                                <Text fw={700} size="sm" lineClamp={2} style={{ flex: 1 }}>
                                                    {linkedGoal.title}
                                                </Text>
                                                <Badge
                                                    size="lg"
                                                    radius="lg"
                                                    variant="light"
                                                    color={goalProgress >= 70 ? 'teal' : goalProgress >= 40 ? 'blue' : 'yellow'}
                                                    style={{ fontWeight: 700 }}
                                                >
                                                    {goalProgress}%
                                                </Badge>
                                            </Group>
                                            <Text size="xs" c="dimmed" mb="md">
                                                {linkedGoal.current?.toLocaleString?.() ?? 0} / {linkedGoal.target?.toLocaleString?.() ?? 0} {linkedGoal.unit}
                                            </Text>
                                            <Progress
                                                value={goalProgress}
                                                radius="xl"
                                                size="md"
                                                color={goalProgress >= 70 ? 'teal' : goalProgress >= 40 ? 'blue' : 'yellow'}
                                            />
                                        </>
                                    ) : (
                                        <div style={{ textAlign: 'center', padding: '24px 16px' }}>
                                            <Text size="lg" mb="xs">🎯</Text>
                                            <Text size="xs" c="dimmed">Select a goal to track progress</Text>
                                        </div>
                                    )}
                                </Card>
                            </div>
                        </Stack>
                    </ScrollArea>
                )}

                {/* CENTER PLANE: Single unified plan view */}
                <Card withBorder={false} radius="md" p={0} shadow="xs" style={{ flex: 1, minWidth: 0, background: 'white', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ padding: '8px 12px', borderBottom: `1px solid ${theme.colors.gray[2]}` }}>
                        <Group justify="space-between">
                            <Group gap={6}>
                                {!showLeftPlane && (
                                    <ActionIcon variant="subtle" color="gray" onClick={() => setShowLeftPlane(true)} size="xs">
                                        <IconChevronRight size={14} />
                                    </ActionIcon>
                                )}
                                <IconFileText size={16} color={theme.colors.brand[6]} />
                                <Text fw={700} size="xs">This week</Text>
                            </Group>
                            {linkedGoal && (
                                <Badge size="xs" variant="light" color="teal" radius="sm">
                                    {linkedGoal.title}
                                </Badge>
                            )}
                        </Group>
                    </div>

                    <ScrollArea style={{ flex: 1 }} p={10}>
                        <Stack gap={12}>
                            {!lastAssistant ? (
                                <Card withBorder radius="md" p="md" style={{ textAlign: 'center' }}>
                                    <div style={{
                                        width: '48px', height: '48px', borderRadius: '12px',
                                        background: theme.colors.brand[0], display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px'
                                    }}>
                                        <IconSparkles size={24} color={theme.colors.brand[6]} />
                                    </div>
                                    <Text fw={700} size="sm" mb={4}>Welcome!</Text>
                                    <Text size="xs" c="dimmed" mb="sm">Choose how to get started:</Text>
                                    <Group gap={8} grow>
                                        <Button size="xs" variant="light" onClick={() => navigate('/goals')}>Pick a goal</Button>
                                        <Button size="xs" variant="light" color="violet" onClick={() => { setOptiGuideInitMode('what-if'); setOptiGuideInitQuestion('What if order costs increase by 20%?'); setShowOptiGuide(true) }}>Run scenario</Button>
                                        <Button size="xs" variant="light" color="teal" onClick={addSamplePlan}>See example</Button>
                                    </Group>
                                </Card>
                            ) : (
                                <>
                                    {/* Trip.com-style: Action steps section with collapse */}
                                    {isActionPlan && planBullets.length > 0 && (
                                        <Card withBorder radius="md" p={0} style={{ overflow: 'hidden' }}>
                                            <div
                                                onClick={() => setStepsExpanded(v => !v)}
                                                style={{
                                                    padding: '10px 12px',
                                                    cursor: 'pointer',
                                                    background: theme.colors.gray[0],
                                                    borderBottom: stepsExpanded ? `1px solid ${theme.colors.gray[2]}` : 'none',
                                                    transition: 'background 0.2s'
                                                }}
                                                onMouseEnter={(e) => e.currentTarget.style.background = theme.colors.gray[1]}
                                                onMouseLeave={(e) => e.currentTarget.style.background = theme.colors.gray[0]}
                                            >
                                                <Group justify="space-between">
                                                    <Group gap="xs">
                                                        <div style={{
                                                            width: '24px',
                                                            height: '24px',
                                                            borderRadius: '6px',
                                                            background: theme.colors.brand[6],
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center'
                                                        }}>
                                                            <IconTarget size={14} color="white" />
                                                        </div>
                                                        <div>
                                                            <Text fw={600} size="sm" c="dark">Recommended Steps</Text>
                                                            <Text size="xs" c="dimmed">{planBullets.length} action items</Text>
                                                        </div>
                                                    </Group>
                                                    <Group gap="xs">
                                                        {stepsExpanded && (
                                                            <Button
                                                                size="xs"
                                                                variant="light"
                                                                color="brand"
                                                                onClick={(e) => {
                                                                    e.stopPropagation()
                                                                    createTasksFromLastAssistant()
                                                                }}
                                                            >
                                                                Save all
                                                            </Button>
                                                        )}
                                                        <ActionIcon
                                                            size="sm"
                                                            variant="subtle"
                                                            color="gray"
                                                            style={{
                                                                transform: stepsExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                                                transition: 'transform 0.2s'
                                                            }}
                                                        >
                                                            <IconChevronDown size={16} />
                                                        </ActionIcon>
                                                    </Group>
                                                </Group>
                                            </div>
                                            <Collapse in={stepsExpanded}>
                                                <Stack gap="xs" p="sm">
                                                    {planBullets.slice(0, 3).map((b, idx) => (
                                                        <Card key={`plan-${idx}`} withBorder radius="md" p="sm" style={{ transition: 'all 0.2s', background: 'white' }}>
                                                            <Group justify="space-between" align="flex-start" wrap="nowrap" gap="xs">
                                                                <Group gap="sm" align="flex-start" style={{ flex: 1 }}>
                                                                    <div style={{
                                                                        width: '24px',
                                                                        height: '24px',
                                                                        borderRadius: '6px',
                                                                        background: theme.colors.brand[0],
                                                                        border: `2px solid ${theme.colors.brand[3]}`,
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        justifyContent: 'center',
                                                                        flexShrink: 0
                                                                    }}>
                                                                        <Text size="xs" fw={700} c="brand">{idx + 1}</Text>
                                                                    </div>
                                                                    <div style={{ flex: 1 }}>
                                                                        <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{b}</Text>
                                                                    </div>
                                                                </Group>
                                                                <Button
                                                                    size="xs"
                                                                    variant="light"
                                                                    color="teal"
                                                                    onClick={() => openSaveAsTask(b)}
                                                                    style={{ flexShrink: 0, height: '24px', padding: '0 8px', fontSize: '11px' }}
                                                                >
                                                                    + Task
                                                                </Button>
                                                            </Group>
                                                        </Card>
                                                    ))}
                                                </Stack>
                                            </Collapse>
                                        </Card>
                                    )}

                                    {/* Trip.com-style: Tasks section with collapse */}
                                    {selectedGoalId && (
                                        <Card withBorder radius="md" p={0} style={{ overflow: 'hidden' }}>
                                            <div
                                                onClick={() => setTasksExpanded(v => !v)}
                                                style={{
                                                    padding: '10px 12px',
                                                    cursor: 'pointer',
                                                    background: theme.colors.gray[0],
                                                    borderBottom: tasksExpanded ? `1px solid ${theme.colors.gray[2]}` : 'none',
                                                    transition: 'background 0.2s'
                                                }}
                                                onMouseEnter={(e) => e.currentTarget.style.background = theme.colors.gray[1]}
                                                onMouseLeave={(e) => e.currentTarget.style.background = theme.colors.gray[0]}
                                            >
                                                <Group justify="space-between">
                                                    <Group gap="xs">
                                                        <div style={{
                                                            width: '24px',
                                                            height: '24px',
                                                            borderRadius: '6px',
                                                            background: theme.colors.teal[6],
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center'
                                                        }}>
                                                            <IconCheck size={14} color="white" />
                                                        </div>
                                                        <div>
                                                            <Text fw={600} size="sm" c="dark">Your Tasks</Text>
                                                            <Text size="xs" c="dimmed">
                                                                {goalTasks.length === 0
                                                                    ? 'No tasks yet'
                                                                    : `${goalTasks.filter((t: any) => t.status !== 'completed').length} active`
                                                                }
                                                            </Text>
                                                        </div>
                                                    </Group>
                                                    <Group gap="xs">
                                                        {tasksExpanded && goalTasks.length > 3 && (
                                                            <Button
                                                                size="xs"
                                                                variant="subtle"
                                                                onClick={(e) => {
                                                                    e.stopPropagation()
                                                                    navigate('/tasks')
                                                                }}
                                                            >
                                                                View all
                                                            </Button>
                                                        )}
                                                        <ActionIcon
                                                            size="sm"
                                                            variant="subtle"
                                                            color="gray"
                                                            style={{
                                                                transform: tasksExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                                                transition: 'transform 0.2s'
                                                            }}
                                                        >
                                                            <IconChevronDown size={16} />
                                                        </ActionIcon>
                                                    </Group>
                                                </Group>
                                            </div>
                                            <Collapse in={tasksExpanded}>
                                                {goalTasks.length === 0 ? (
                                                    <div style={{ textAlign: 'center', padding: '32px 16px', background: 'white' }}>
                                                        <Text size="lg" mb={8}>✅</Text>
                                                        <Text size="xs" c="dimmed" mb={4}>No tasks yet</Text>
                                                        <Text size="xs" c="dimmed">Create tasks from the steps above</Text>
                                                    </div>
                                                ) : (
                                                    <Stack gap={8} p="sm">
                                                        {goalTasks.slice(0, 5).map((t: any) => {
                                                            const checked = t.status === 'completed'
                                                            return (
                                                                <Card key={t.id} withBorder radius="sm" p={10} style={{
                                                                    background: checked ? theme.colors.gray[0] : 'white',
                                                                    borderColor: checked ? theme.colors.gray[2] : theme.colors.teal[2],
                                                                    transition: 'all 0.2s'
                                                                }}>
                                                                    <Group justify="space-between" align="flex-start" wrap="nowrap" gap={6}>
                                                                        <Group gap="xs" align="flex-start" style={{ flex: 1 }}>
                                                                            <Checkbox
                                                                                checked={checked}
                                                                                size="sm"
                                                                                color="teal"
                                                                                onChange={async () => {
                                                                                    const next = checked ? 'in_progress' : 'completed'
                                                                                    await updateTaskMutation.mutateAsync({ taskId: t.id, data: { status: next } })
                                                                                }}
                                                                                style={{ marginTop: '1px' }}
                                                                            />
                                                                            <div style={{ flex: 1 }}>
                                                                                <Text
                                                                                    size="sm"
                                                                                    fw={checked ? 400 : 600}
                                                                                    c={checked ? 'dimmed' : 'dark'}
                                                                                    style={{ textDecoration: checked ? 'line-through' : 'none', lineHeight: 1.5 }}
                                                                                >
                                                                                    {t.title}
                                                                                </Text>
                                                                            </div>
                                                                        </Group>
                                                                        <Menu shadow="md" width={160} position="bottom-end">
                                                                            <Menu.Target>
                                                                                <ActionIcon size="sm" variant="subtle" color="gray">
                                                                                    <IconDotsVertical size={14} />
                                                                                </ActionIcon>
                                                                            </Menu.Target>
                                                                            <Menu.Dropdown>
                                                                                {(['low', 'medium', 'high', 'urgent'] as const).map(p => (
                                                                                    <Menu.Item
                                                                                        key={p}
                                                                                        onClick={async () => updateTaskMutation.mutateAsync({ taskId: t.id, data: { priority: p } })}
                                                                                    >
                                                                                        {p.charAt(0).toUpperCase() + p.slice(1)} Priority
                                                                                    </Menu.Item>
                                                                                ))}
                                                                            </Menu.Dropdown>
                                                                        </Menu>
                                                                    </Group>
                                                                </Card>
                                                            )
                                                        })}
                                                    </Stack>
                                                )}
                                            </Collapse>
                                        </Card>
                                    )}
                                </>
                            )}
                        </Stack>
                    </ScrollArea>
                </Card>                {/* RIGHT PLANE: Evidence, Reports & Data (Trip.com-style) */}
                {showRightPlane && (
                    <Card withBorder={false} radius="md" p={0} shadow="xs" style={{ width: '360px', flexShrink: 0, background: 'white', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                        <div style={{ padding: '8px 12px', borderBottom: `1px solid ${theme.colors.gray[2]}` }}>
                            <Group justify="space-between" align="center" mb={6}>
                                <Group gap={6}>
                                    <IconFileText size={14} color={theme.colors.brand[6]} />
                                    <Text fw={700} size="xs">Evidence & Reports</Text>
                                </Group>
                                <ActionIcon variant="subtle" color="gray" onClick={() => setShowRightPlane(false)} size="xs">
                                    <IconChevronRight size={12} />
                                </ActionIcon>
                            </Group>

                            {/* Evidence type tabs */}
                            <Tabs value={evidenceView} onChange={(v) => setEvidenceView(v as any)}>
                                <Tabs.List style={{ border: 'none', gap: '2px' }}>
                                    <Tabs.Tab value="sources" style={{ padding: '6px 10px', fontSize: '10px' }}>
                                        📊 Sources
                                    </Tabs.Tab>
                                    <Tabs.Tab value="reports" style={{ padding: '6px 10px', fontSize: '10px' }}>
                                        📄 Reports
                                    </Tabs.Tab>
                                    <Tabs.Tab value="graphs" style={{ padding: '6px 10px', fontSize: '10px' }}>
                                        📈 Graphs
                                    </Tabs.Tab>
                                </Tabs.List>
                            </Tabs>
                        </div>

                        <ScrollArea style={{ flex: 1 }} p={8}>
                            <Stack gap={8}>
                                {evidenceView === 'sources' && lastAssistant ? (
                                    <>
                                        <Text size="xs" c="dimmed" fw={700} tt="uppercase" mb={4} style={{ letterSpacing: '0.3px' }}>
                                            📊 Evidence & Sources
                                        </Text>
                                        <Card withBorder radius="sm" p={8}>
                                            <Stack gap={8}>
                                                {(lastAssistant.metadata?.data_sources || []).length > 0 && (
                                                    <div>
                                                        <Text size="xs" c="dimmed" fw={600} mb={4}>Data Sources</Text>
                                                        <Group gap={4}>
                                                            {(lastAssistant.metadata?.data_sources || []).map((ds) => (
                                                                <Badge key={`ds-${ds}`} size="xs" color="gray" variant="light">{ds}</Badge>
                                                            ))}
                                                        </Group>
                                                    </div>
                                                )}
                                                {(lastAssistant.metadata?.tools_used || []).length > 0 && (
                                                    <div>
                                                        <Text size="xs" c="dimmed" fw={600} mb={4}>Tools Used</Text>
                                                        <Group gap={4}>
                                                            {(lastAssistant.metadata?.tools_used || []).map((tool) => (
                                                                <Badge key={`tool-${tool}`} size="xs" color="blue" variant="light">{tool}</Badge>
                                                            ))}
                                                        </Group>
                                                    </div>
                                                )}
                                                {'report_id' in (lastAssistant.metadata || {}) && lastAssistant.metadata?.report_id && (
                                                    <div>
                                                        <Text size="xs" c="dimmed" fw={600} mb={4}>Generated Report</Text>
                                                        <ReportDownloadButtons
                                                            reportId={String((lastAssistant.metadata as any).report_id)}
                                                            tenantId={tenantId!}
                                                            reportTitle={linkedGoal?.title || 'Business Report'}
                                                        />
                                                    </div>
                                                )}
                                            </Stack>
                                        </Card>
                                    </>
                                ) : evidenceView === 'reports' ? (
                                    <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                                        <Text size="lg" mb={6}>📄</Text>
                                        <Text size="xs" c="dimmed">Reports section</Text>
                                    </div>
                                ) : evidenceView === 'graphs' ? (
                                    <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                                        <Text size="lg" mb={6}>📈</Text>
                                        <Text size="xs" c="dimmed">Graphs coming soon</Text>
                                    </div>
                                ) : (
                                    <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                                        <Text size="lg" mb={6}>💬</Text>
                                        <Text size="xs" c="dimmed">Start a conversation</Text>
                                    </div>
                                )}
                            </Stack>
                        </ScrollArea>
                    </Card>
                )}
            </div>

            <CreateTaskModal
                opened={taskModalOpen}
                onClose={() => setTaskModalOpen(false)}
                initialTitle={taskDraftTitle}
                onCreate={async (task) => {
                    if (!selectedGoalId) return
                    await createTaskMutation.mutateAsync({ ...task, goal_id: selectedGoalId })
                    trackEvent('task_created_from_message', { tenantId })
                }}
            />
        </div >
    )
}
