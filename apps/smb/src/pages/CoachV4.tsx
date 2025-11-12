import { Badge, Button, Card, Group, HoverCard, Menu, ScrollArea, Stack, Text, Textarea, TextInput } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconChevronDown, IconExternalLink, IconHelp, IconPlayerStop, IconSearch, IconSend, IconSparkles } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CoachSettings from '../components/CoachSettings'
import ConversationHistory from '../components/ConversationHistory'
import DataSourcesIndicator from '../components/DataSourcesIndicator'
import ErrorState from '../components/ErrorState'
import EvidencePanel from '../components/EvidencePanel'
import LoadingSkeleton from '../components/LoadingSkeleton'
import MetricsCard from '../components/MetricsCard'
import OnboardingTour from '../components/OnboardingTour'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { API_BASE, get } from '../lib/api'
import { Conversation, deleteConversation, generateConversationTitle, loadConversations, saveConversation } from '../lib/conversations'
import { formatRelativeTime, isDataStale } from '../lib/time'
import { getTenantToolsAndPrompts } from '../lib/toolSuggestions'
import { useAuthStore } from '../stores/auth'

export interface Evidence {
    claim: string
    source: string
    confidence: number
    data: any
    timestamp?: string
    sampleSize?: number
}

export interface DataSource {
    name: string
    icon: string
    lastSync: string
    recordCount: number
}

export interface RunStep {
    name: string
    status: 'complete' | 'running' | 'error'
    duration: number
    output?: any
}

export interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    runUrl?: string
    isStreaming?: boolean
    metadata?: {
        intent?: string
        conversation_stage?: string
        focusTitle?: string
        quickActions?: Array<{ label: string; prompt: string }>
        evidence?: Evidence[]
        dataSources?: DataSource[]
        runSteps?: RunStep[]
        runCost?: number
        runDuration?: number
        error?: boolean
        rich_data?: {
            type: string
            metrics?: any[]
            chart?: any
        }
    }
}

const AGENTS: Array<{ id: string; label: string; emoji: string }> = [
    { id: 'business_analyst', label: 'Business Analyst', emoji: '📊' },
    { id: 'data_scientist', label: 'Data Scientist', emoji: '📈' },
    { id: 'consultant', label: 'Consultant', emoji: '💼' },
    { id: 'operations_manager', label: 'Operations Manager', emoji: '⚙️' },
    { id: 'growth_strategist', label: 'Growth Strategist', emoji: '🚀' },
]

export default function CoachV4() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    // Debug: Log auth state on mount
    useEffect(() => {
        console.log('[CoachV4] Auth state:', {
            tenantId,
            hasApiToken: !!apiToken,
            user: user?.email || 'Not logged in'
        })
        if (!tenantId || !apiToken) {
            console.warn('[CoachV4] Missing authentication! tenantId or apiToken is undefined')
        }
    }, [tenantId, apiToken, user])

    // Responsive breakpoints
    const isMobile = useMediaQuery('(max-width: 767px)')
    const isTablet = useMediaQuery('(max-width: 1023px)')

    // Sidebar state
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(() => {
        if (isMobile) return false // Default closed on mobile
        try { return (localStorage.getItem('coach.sidebarOpen') || 'true') === 'true' } catch { return true }
    })
    const [goalSearch, setGoalSearch] = useState<string>('')
    useEffect(() => { localStorage.setItem('coach.sidebarOpen', String(sidebarOpen)) }, [sidebarOpen])

    // Onboarding state
    const [showOnboarding, setShowOnboarding] = useState<boolean>(() => {
        try { return localStorage.getItem('onboarding_completed') !== 'true' } catch { return true }
    })

    // AbortController for stopping generation
    const abortControllerRef = useRef<AbortController | null>(null)

    // Persistent selections
    const [selectedAgent, setSelectedAgent] = useState<string>(() => {
        try { return localStorage.getItem('coach.selectedAgent') || 'business_analyst' } catch { return 'business_analyst' }
    })
    useEffect(() => { try { localStorage.setItem('coach.selectedAgent', selectedAgent) } catch { } }, [selectedAgent])

    // Settings modal
    const [settingsOpen, setSettingsOpen] = useState(false)
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>([])
    const [includeEvidence, setIncludeEvidence] = useState(true)
    const [includeForecast, setIncludeForecast] = useState(false)

    // Data
    const { data: healthScore, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useQuery({
        queryKey: ['health-score', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/health-score`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })
    const { data: goalsData, isLoading: goalsLoading, error: goalsError, refetch: refetchGoals } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/goals`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })
    const { data: tasksData, isLoading: tasksLoading, error: tasksError, refetch: refetchTasks } = useQuery({
        queryKey: ['tasks', tenantId, 'todo'],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })
    // Connectors (for MCP-aware tools & prompts)
    const connectorsQuery = useConnectorsQuery(apiToken, tenantId, { enabled: !!tenantId && !!apiToken })
    const enabledConnectors = useMemo(
        () => {
            const filtered = (connectorsQuery.data ?? []).filter((c: any) => c.status === 'active' && c?.metadata?.mcp_enabled)
            console.log('[CoachV4] All connectors:', connectorsQuery.data)
            console.log('[CoachV4] Enabled connectors (active + mcp_enabled):', filtered)
            return filtered
        },
        [connectorsQuery.data]
    )
    const { tools: suggestedTools, prompts: suggestedPrompts } = useMemo(() => {
        try {
            const result = getTenantToolsAndPrompts(enabledConnectors as any)
            console.log('[CoachV4] Tools and prompts:', result)
            return result
        } catch (err) {
            console.error('[CoachV4] Error getting tools/prompts:', err)
            return { tools: [], prompts: [] }
        }
    }, [enabledConnectors])

    // Active goals list for sidebar (must be after goalsData query)
    const activeGoals = goalsData?.filter((g: any) => g.status === 'active').slice(0, 5) || []

    // Conversation history (tenant-scoped)
    const [conversations, setConversations] = useState<Conversation[]>(() =>
        tenantId ? loadConversations(tenantId) : []
    )
    const [currentConversationId, setCurrentConversationId] = useState<string | undefined>()
    const [historyOpen, setHistoryOpen] = useState(false)

    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isSending, setIsSending] = useState(false)

    // Helper to generate Today's Focus
    const generateTodaysFocus = () => {
        const score = healthScore?.score || 0
        const breakdown = healthScore?.breakdown
        // Exclude starter tasks from urgent tasks calculation
        const realTasks = tasksData?.filter((t: any) => !t.is_starter_task) || []
        const urgentTasks = realTasks.filter((t: any) => t.priority === 'high' || t.priority === 'urgent' || new Date(t.due_date) < new Date()).slice(0, 3)
        const activeGoalsList = goalsData?.filter((g: any) => g.status === 'active') || []

        // Check if we have any real data connected
        const hasAnyRealData = realTasks.length > 0 || activeGoalsList.length > 0 || score > 0

        // Priority 0: No data connected OR data synced but needs analysis
        if (score === 0 && !hasAnyRealData) {
            // Check if connector exists but data hasn't synced yet
            const hasConnector = enabledConnectors.length > 0

            if (hasConnector) {
                const connectorNames = enabledConnectors.map((c: any) => c.connector_name).join(', ')
                return {
                    title: "🔄 Data Sync in Progress",
                    message: `Great! I see you've connected: **${connectorNames}**\n\nI'm analyzing your data to calculate your business health score. This usually takes a few moments.\n\nOnce sync completes, I'll show you:\n• Business health breakdown\n• Revenue & operations insights\n• Personalized recommendations`,
                    quickActions: [
                        { label: "🔍 Check Sync Status", prompt: "What's the status of my data sync?" },
                        { label: "📊 What Data Types", prompt: "What types of data can you analyze from my connector?" },
                        { label: "🎯 Set a Goal", prompt: "Help me set my first business goal while we wait" }
                    ]
                }
            }

            // No connector at all
            return {
                title: "👋 Welcome to Your AI Business Coach!",
                message: `To get personalized insights and track your business health, let's connect your data sources.\n\nI can help you analyze data from:\n• ERPNext integrations\n• CSV file uploads\n• E-commerce platforms`,
                quickActions: [
                    { label: "🔗 Connect ERPNext", prompt: "How do I connect my ERPNext data?" },
                    { label: "📁 Upload CSV", prompt: "I want to upload CSV files to analyze" },
                    { label: "🎯 Set a Goal", prompt: "Help me set my first business goal" }
                ]
            }
        }

        // Priority 1: Critical health score (but only if we have data)
        if (score > 0 && score < 40) {
            return {
                title: "🚨 Today's Focus: Critical Business Health",
                message: `Your health score is ${score}/100 - this needs immediate attention! Let's identify the biggest issue and create a recovery plan.`,
                quickActions: [
                    { label: "🩺 Diagnose Issues", prompt: "What's causing my low health score?" },
                    { label: "🚀 Recovery Plan", prompt: "Create a 7-day recovery plan for my business" },
                    { label: "📊 Show Details", prompt: "Break down my health score by category" }
                ]
            }
        }

        // Priority 2: Urgent/overdue tasks (exclude starter tasks)
        if (urgentTasks.length > 0) {
            const taskList = urgentTasks.map((t: any) => `• ${t.title}`).join('\n')
            const taskCount = urgentTasks.length
            return {
                title: "⚠️ Today's Focus: Urgent Tasks",
                message: `You have ${taskCount} urgent task${taskCount > 1 ? 's' : ''} that need${taskCount === 1 ? 's' : ''} attention today:\n\n${taskList}`,
                quickActions: [
                    { label: "📋 View Tasks", prompt: `Tell me about these urgent tasks: ${urgentTasks.map((t: any) => t.title).join(', ')}` },
                    { label: "✅ Prioritize", prompt: "Help me prioritize my urgent tasks" },
                    { label: "🎯 Quick Win", prompt: "Which task can I finish fastest?" }
                ]
            }
        }

        // Priority 3: Active goals needing progress
        if (activeGoalsList.length > 0) {
            const stalled = activeGoalsList.find((g: any) => {
                const progress = g.target_value ? ((g.current_value || 0) / g.target_value) * 100 : 0
                return progress < 30 // Less than 30% progress
            })
            if (stalled) {
                return {
                    title: "🎯 Today's Focus: Accelerate Goal Progress",
                    message: `Your goal "${stalled.title}" is at ${Math.round((stalled.current_value || 0) / stalled.target_value * 100)}% progress. Let's create momentum!`,
                    quickActions: [
                        { label: "🚀 Action Plan", prompt: `Create a weekly action plan for my goal: ${stalled.title}` },
                        { label: "📈 Progress Check", prompt: `Show me progress on: ${stalled.title}` },
                        { label: "💡 Quick Wins", prompt: "What quick wins can boost this goal?" }
                    ]
                }
            }
        }

        // Default: Positive check-in (or welcome for new tenants)
        if (!hasAnyRealData) {
            // New tenant without data
            return {
                title: `👋 Welcome${user?.name ? ', ' + user.name.split(' ')[0] : ''}!`,
                message: `Let's set up your business for success! I can help you:\n\n• Connect your data sources (ERPNext, CSV files)\n• Set your first business goal\n• Create an action plan\n• Track your progress`,
                quickActions: [
                    { label: "🔗 Connect Data", prompt: "How do I connect my business data?" },
                    { label: "🎯 Set a Goal", prompt: "Help me set my first business goal" },
                    { label: "📋 Create Tasks", prompt: "Create a weekly action plan for my business" }
                ]
            }
        }

        // Existing tenant with data - show data insights
        const dataInsights: string[] = []
        if (breakdown?.revenue_available && breakdown?.revenue_source) {
            const recordCount = breakdown.revenue_record_count || 0
            const isSample = breakdown.is_sample_data
            dataInsights.push(`📊 **Revenue**: ${recordCount.toLocaleString()} orders from ${breakdown.revenue_source}${isSample ? ' (sample)' : ''}`)
        }
        if (breakdown?.operations_available && breakdown?.operations_source) {
            const recordCount = breakdown.operations_record_count || 0
            const isSample = breakdown.is_sample_data
            dataInsights.push(`⚙️ **Operations**: ${recordCount.toLocaleString()} items from ${breakdown.operations_source}${isSample ? ' (sample)' : ''}`)
        }
        if (breakdown?.customer_available && breakdown?.customer_source) {
            const recordCount = breakdown.customer_record_count || 0
            const isSample = breakdown.is_sample_data
            dataInsights.push(`👥 **Customers**: ${recordCount.toLocaleString()} records from ${breakdown.customer_source}${isSample ? ' (sample)' : ''}`)
        }

        const dataInsightMessage = dataInsights.length > 0
            ? `\n\n**Connected Data:**\n${dataInsights.join('\n')}`
            : ''

        return {
            title: `👋 Good Morning${user?.name ? ', ' + user.name.split(' ')[0] : ''}!`,
            message: `Your business is running smoothly (Health: ${score}/100). What would you like to work on today?${dataInsightMessage}`,
            quickActions: [
                { label: "📊 Daily Summary", prompt: "Show me yesterday's performance summary" },
                { label: "🎯 Set New Goal", prompt: "Help me set a new business goal" },
                { label: "💡 Opportunities", prompt: "What opportunities should I focus on?" }
            ]
        }
    }

    // Update welcome message when agent changes OR when health/goals/tasks load
    useEffect(() => {
        const focus = generateTodaysFocus()
        setMessages([{
            id: 'hello',
            role: 'assistant',
            content: focus.message,
            timestamp: new Date(),
            metadata: {
                focusTitle: focus.title,
                quickActions: focus.quickActions
            }
        }])
    }, [selectedAgent, user?.name, healthScore, tasksData, goalsData])

    // Save current conversation when messages change
    useEffect(() => {
        if (messages.length > 1 && tenantId) { // Only save if there's actual conversation and tenantId exists
            const conversationId = currentConversationId || `conv-${Date.now()}`
            const title = currentConversationId
                ? conversations.find(c => c.id === conversationId)?.title || generateConversationTitle(messages)
                : generateConversationTitle(messages)

            const conversation: Conversation = {
                id: conversationId,
                title,
                messages,
                createdAt: currentConversationId
                    ? conversations.find(c => c.id === conversationId)?.createdAt || new Date()
                    : new Date(),
                updatedAt: new Date(),
                agent: selectedAgent,
                tenantId: tenantId
            }

            saveConversation(conversation, tenantId)
            setConversations(loadConversations(tenantId))
            if (!currentConversationId) {
                setCurrentConversationId(conversationId)
            }
        }
    }, [messages, tenantId])

    const handleNewConversation = () => {
        setMessages([])
        setCurrentConversationId(undefined)
        // Trigger welcome message regeneration
        setTimeout(() => {
            const focus = generateTodaysFocus()
            setMessages([{
                id: 'hello',
                role: 'assistant',
                content: focus.message,
                timestamp: new Date(),
                metadata: {
                    focusTitle: focus.title,
                    quickActions: focus.quickActions
                }
            }])
        }, 0)
    }

    const handleSelectConversation = (conversation: Conversation) => {
        setMessages(conversation.messages)
        setCurrentConversationId(conversation.id)
        if (conversation.agent) {
            setSelectedAgent(conversation.agent)
        }
        if (isMobile) {
            setSidebarOpen(false) // Close sidebar on mobile after selection
        }
    }

    const handleDeleteConversation = (id: string) => {
        if (!tenantId) return
        deleteConversation(id, tenantId)
        setConversations(loadConversations(tenantId))
        if (id === currentConversationId) {
            handleNewConversation()
        }
    }

    const sendMessage = async () => {
        const text = input.trim()
        if (!text) return

        const userMsg: Message = {
            id: String(Date.now()),
            role: 'user',
            content: text,
            timestamp: new Date()
        }
        setMessages((m) => [...m, userMsg])
        setInput('')
        setIsSending(true)

        // Create placeholder assistant message for streaming
        const assistantMsgId = `${userMsg.id}-r`
        const assistantMsg: Message = {
            id: assistantMsgId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true
        }
        setMessages((m) => [...m, assistantMsg])

        // Create abort controller for this request
        const abortController = new AbortController()
        abortControllerRef.current = abortController

        try {
            // Use streaming endpoint
            console.log('[CoachV4] Sending message to backend:', {
                endpoint: `${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream`,
                tenantId,
                agent: selectedAgent,
                messagePreview: text.substring(0, 50)
            })

            const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiToken}`,
                },
                body: JSON.stringify({
                    message: text,
                    conversation_history: messages
                        .filter(m => m.role !== 'assistant' || !m.isStreaming)
                        .slice(-10) // Last 10 messages for context
                        .map(m => ({
                            role: m.role,
                            content: m.content,
                            timestamp: m.timestamp.toISOString()
                        })),
                    persona: selectedAgent,
                    include_evidence: includeEvidence,
                    include_forecast: includeForecast,
                    data_sources: selectedDataSources
                }),
                signal: abortController.signal
            })

            console.log('[CoachV4] Backend response status:', response.status)

            if (!response.ok) {
                const errorText = await response.text()
                console.error('[CoachV4] Backend error:', errorText)
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            let fullContent = ''
            let lastMetadata = {}

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    const chunk = decoder.decode(value)
                    const lines = chunk.split('\n')

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6))
                                console.log('[CoachV4] SSE data received:', data)

                                if (data.delta) {
                                    fullContent += data.delta
                                    if (data.metadata) {
                                        lastMetadata = data.metadata
                                        console.log('[CoachV4] Metadata received:', data.metadata)
                                    }
                                    // Update message with streamed content
                                    setMessages((prevMessages) =>
                                        prevMessages.map((msg) =>
                                            msg.id === assistantMsgId
                                                ? { ...msg, content: fullContent, metadata: lastMetadata }
                                                : msg
                                        )
                                    )
                                }
                                if (data.done) {
                                    console.log('[CoachV4] Stream complete. RunURL:', data.runUrl)
                                    // Mark as complete
                                    setMessages((prevMessages) =>
                                        prevMessages.map((msg) =>
                                            msg.id === assistantMsgId
                                                ? { ...msg, isStreaming: false, runUrl: data.runUrl }
                                                : msg
                                        )
                                    )
                                }
                            } catch (e) {
                                console.warn('Failed to parse SSE data:', e, 'Line:', line)
                            }
                        }
                    }
                }
            }

            // Auto-scroll to bottom
            requestAnimationFrame(() => scrollAreaRef.current?.scrollTo({
                top: scrollAreaRef.current.scrollHeight,
                behavior: 'smooth'
            }))

        } catch (e: any) {
            console.error('Streaming error:', e)

            // Check if it was aborted by user
            if (e.name === 'AbortError') {
                setMessages((prevMessages) =>
                    prevMessages.map((msg) =>
                        msg.id === assistantMsgId
                            ? {
                                ...msg,
                                content: '_Generation stopped by user_',
                                isStreaming: false
                            }
                            : msg
                    )
                )
            } else {
                // Show error with retry option
                setMessages((prevMessages) =>
                    prevMessages.map((msg) =>
                        msg.id === assistantMsgId
                            ? {
                                ...msg,
                                content: `⚠️ **Error**: ${e.message || 'Failed to connect to AI coach. Please check your connection and try again.'}`,
                                isStreaming: false,
                                metadata: { error: true }
                            }
                            : msg
                    )
                )
            }
        } finally {
            setIsSending(false)
            abortControllerRef.current = null
        }
    }

    // Stop generation
    const stopGeneration = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
            abortControllerRef.current = null
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    // Quick action handlers
    const handleImproveScore = () => {
        setInput("How can I improve my business health score? What should I focus on?")
        // Auto-send after short delay
        setTimeout(() => sendMessage(), 100)
    }

    const handleCreatePlan = async () => {
        try {
            // Auto-generate a weekly action plan
            setInput("Create a weekly action plan based on my current goals and health score")
            setTimeout(() => sendMessage(), 100)
        } catch (e) {
            console.error('Failed to create plan:', e)
        }
    }

    return (
        <>
            {/* Onboarding Tour */}
            <OnboardingTour
                opened={showOnboarding}
                onClose={() => setShowOnboarding(false)}
            />

            <div style={{ display: 'flex', height: '100%', width: '100%', background: '#fff', position: 'relative' }}>
                {sidebarOpen && (
                    <div style={{
                        width: isMobile ? '100%' : isTablet ? 240 : 280,
                        display: 'flex',
                        flexDirection: 'column',
                        background: '#f7f7f8',
                        position: isMobile ? 'fixed' : 'relative',
                        top: isMobile ? 0 : 'auto',
                        left: isMobile ? 0 : 'auto',
                        bottom: isMobile ? 0 : 'auto',
                        right: isMobile ? 0 : 'auto',
                        zIndex: isMobile ? 100 : 'auto',
                        boxShadow: isMobile ? '0 -2px 10px rgba(0,0,0,0.1)' : 'none'
                    }}>
                        {/* Sidebar header */}
                        <div style={{ padding: '20px 16px 16px' }}>
                            <Button
                                fullWidth
                                variant="filled"
                                size="md"
                                mb={12}
                                styles={{
                                    root: {
                                        borderRadius: '6px',
                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                        border: 'none',
                                        fontWeight: 500
                                    }
                                }}
                                onClick={() => navigate('/goals')}
                            >
                                🎯 New Goal
                            </Button>
                            <TextInput
                                leftSection={<IconSearch size={16} />}
                                placeholder="Search goals..."
                                value={goalSearch}
                                onChange={(e) => setGoalSearch(e.currentTarget.value)}
                                size="sm"
                                styles={{
                                    input: {
                                        borderRadius: '6px',
                                        background: '#fff',
                                        border: 'none',
                                        fontSize: '13px'
                                    }
                                }}
                            />
                        </div>

                        {/* Conversation History Section */}
                        <div style={{ padding: '0 12px 12px', borderBottom: '1px solid #e5e7eb' }}>
                            <Group justify="space-between" mb={8} px={4}>
                                <Text size="11px" c="#6b7280" fw={600} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                    💬 Recent Chats ({conversations.length})
                                </Text>
                                <Button
                                    size="xs"
                                    variant="subtle"
                                    onClick={handleNewConversation}
                                    styles={{ root: { fontSize: '10px', height: 20, padding: '0 8px' } }}
                                >
                                    New
                                </Button>
                            </Group>
                            <ConversationHistory
                                conversations={conversations}
                                currentConversationId={currentConversationId}
                                onSelectConversation={handleSelectConversation}
                                onDeleteConversation={handleDeleteConversation}
                                onNewConversation={handleNewConversation}
                            />
                        </div>

                        {/* Active Goals List */}
                        <ScrollArea style={{ flex: 1 }}>
                            <div style={{ padding: '0 12px 12px' }}>
                                <Text size="11px" c="#6b7280" fw={600} tt="uppercase" mb={8} px={4} style={{ letterSpacing: '0.5px' }}>
                                    🎯 Active Goals ({goalsLoading ? '...' : activeGoals.length})
                                </Text>
                                {goalsLoading ? (
                                    <LoadingSkeleton type="goals" />
                                ) : goalsError ? (
                                    <ErrorState
                                        message="Failed to load goals"
                                        onRetry={() => refetchGoals()}
                                    />
                                ) : activeGoals.length === 0 ? (
                                    <Card
                                        padding="md"
                                        radius="md"
                                        mb={6}
                                        style={{
                                            background: '#fff',
                                            border: '1px dashed #d1d5db',
                                            cursor: 'pointer'
                                        }}
                                        onClick={() => navigate('/goals')}
                                    >
                                        <Text size="13px" c="#6b7280" ta="center" mb={4}>
                                            No active goals yet
                                        </Text>
                                        <Text size="11px" c="#8e8ea0" ta="center">
                                            Click "New Goal" to get started
                                        </Text>
                                    </Card>
                                ) : (
                                    activeGoals.map((goal: any) => (
                                        <div
                                            key={goal.id}
                                            style={{
                                                padding: '10px 12px',
                                                borderRadius: '6px',
                                                cursor: 'pointer',
                                                marginBottom: '4px',
                                                transition: 'background 0.15s ease',
                                                background: 'transparent'
                                            }}
                                            onMouseEnter={(e) => e.currentTarget.style.background = '#ececf1'}
                                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                            onClick={() => {
                                                setInput(`Tell me about my goal: ${goal.title}`)
                                                setTimeout(() => sendMessage(), 100)
                                            }}
                                        >
                                            <Text size="13px" fw={500} mb={4} lineClamp={2} c="#202123">
                                                {goal.title}
                                            </Text>
                                            <Group gap={6} mb={4}>
                                                <div style={{ flex: 1, height: 4, background: '#e5e7eb', borderRadius: 2, overflow: 'hidden' }}>
                                                    <div style={{
                                                        width: `${goal.target_value ? ((goal.current_value || 0) / goal.target_value) * 100 : 0}%`,
                                                        height: '100%',
                                                        background: '#8e44ad',
                                                        transition: 'width 0.3s ease'
                                                    }} />
                                                </div>
                                            </Group>
                                            <Text size="11px" c="#8e8ea0">
                                                {goal.current_value || 0} / {goal.target_value || 0} • {goal.deadline ? new Date(goal.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'No deadline'}
                                            </Text>
                                        </div>
                                    ))
                                )}

                                {/* Recent Conversations - removed for goal-first simplicity */}
                            </div>
                        </ScrollArea>

                        {/* Sidebar footer */}
                        <div style={{ padding: '12px 16px', borderTop: '1px solid #ececf1' }}>
                            <Button
                                size="sm"
                                variant="subtle"
                                fullWidth
                                onClick={() => setSidebarOpen(false)}
                                c="#6b7280"
                                styles={{
                                    root: {
                                        fontWeight: 400,
                                        fontSize: '13px'
                                    }
                                }}
                            >
                                ← Hide
                            </Button>
                        </div>
                    </div>
                )}            {/* Main column */}
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                    {/* Show sidebar button when hidden */}
                    {!sidebarOpen && (
                        <div style={{ position: 'absolute', top: 16, left: 16, zIndex: 10 }}>
                            <Button size="xs" variant="subtle" onClick={() => setSidebarOpen(true)}>
                                Show History
                            </Button>
                        </div>
                    )}

                    {/* Sticky header - MINIMAL, NO NAV BUTTONS */}
                    <div style={{ background: 'white', padding: '20px 0', position: 'sticky', top: 0, zIndex: 3 }}>
                        <div style={{ maxWidth: 750, margin: '0 auto', padding: '0 24px' }}>
                            <Group justify="space-between" align="center">
                                <Group gap="sm">
                                    <IconSparkles size={20} style={{ color: '#8e44ad', opacity: 0.9 }} />
                                    <div>
                                        <Text size="16px" fw={600} c="#202123">AI Business Coach</Text>
                                        <Text size="11px" c="#8e8ea0">Your fitness trainer for business growth</Text>
                                    </div>
                                </Group>
                            </Group>
                        </div>
                    </div>                {/* Chat thread - CLEAN, NO BORDERS */}
                    <ScrollArea style={{ flex: 1, background: '#fff' }} viewportRef={scrollAreaRef} offsetScrollbars>
                        <div style={{ maxWidth: 750, margin: '0 auto', padding: '32px 24px 80px' }}>
                            <Stack gap={32}>
                                {messages.map((m, idx) => (
                                    <div key={m.id}>
                                        {m.role === 'assistant' ? (
                                            <div>
                                                <Group gap={12} align="flex-start" wrap="nowrap">
                                                    <div style={{
                                                        width: 30,
                                                        height: 30,
                                                        borderRadius: '4px',
                                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        flexShrink: 0,
                                                        fontSize: 14
                                                    }}>
                                                        {AGENTS.find(a => a.id === selectedAgent)?.emoji || '✨'}
                                                    </div>
                                                    <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }}>
                                                        {/* Today's Focus Title (first message only) */}
                                                        {idx === 0 && m.metadata?.focusTitle && (
                                                            <Text size="16px" fw={600} c="#202123" mb={8}>
                                                                {m.metadata.focusTitle}
                                                            </Text>
                                                        )}

                                                        <Text
                                                            size="15px"
                                                            style={{
                                                                whiteSpace: 'pre-wrap',
                                                                lineHeight: 1.7,
                                                                color: '#353740',
                                                                fontWeight: 400
                                                            }}
                                                        >
                                                            {m.content || (m.isStreaming ? '...' : '')}
                                                        </Text>
                                                        {m.isStreaming && !m.content && (
                                                            <Text size="13px" c="#8e8ea0" style={{ fontStyle: 'italic' }}>
                                                                Thinking...
                                                            </Text>
                                                        )}

                                                        {/* Quick Action Buttons (first message only) */}
                                                        {idx === 0 && m.metadata?.quickActions && (
                                                            <Group gap={8} mt={16}>
                                                                {m.metadata.quickActions.map((action, i) => (
                                                                    <Button
                                                                        key={i}
                                                                        size="xs"
                                                                        variant="light"
                                                                        onClick={() => {
                                                                            setInput(action.prompt)
                                                                            setTimeout(() => sendMessage(), 100)
                                                                        }}
                                                                        styles={{
                                                                            root: {
                                                                                fontSize: '12px',
                                                                                fontWeight: 500,
                                                                                background: '#f3f4f6',
                                                                                border: 'none',
                                                                                color: '#374151'
                                                                            }
                                                                        }}
                                                                    >
                                                                        {action.label}
                                                                    </Button>
                                                                ))}
                                                            </Group>
                                                        )}

                                                        {/* Evidence Panel (all messages) */}
                                                        {m.metadata?.evidence && m.metadata.evidence.length > 0 && (
                                                            <EvidencePanel evidence={m.metadata.evidence} />
                                                        )}

                                                        {/* Rich Metrics Card */}
                                                        {m.metadata?.rich_data?.type === 'metrics_card' && (
                                                            <div style={{ marginTop: 12 }}>
                                                                <MetricsCard
                                                                    metrics={m.metadata.rich_data.metrics || []}
                                                                    chart={m.metadata.rich_data.chart}
                                                                />
                                                            </div>
                                                        )}

                                                        {/* Data Sources Indicator (all messages) */}
                                                        {m.metadata?.dataSources && m.metadata.dataSources.length > 0 && (
                                                            <DataSourcesIndicator sources={m.metadata.dataSources} />
                                                        )}

                                                        {/* LangGraph Run Link (all non-streaming messages) */}
                                                        {m.runUrl && !m.isStreaming && (
                                                            <Group gap={8} mt={12}>
                                                                <Button
                                                                    size="xs"
                                                                    variant="subtle"
                                                                    component="a"
                                                                    href={m.runUrl}
                                                                    target="_blank"
                                                                    leftSection={<IconExternalLink size={14} />}
                                                                    styles={{
                                                                        root: {
                                                                            fontSize: '11px',
                                                                            fontWeight: 500,
                                                                            color: '#6b7280'
                                                                        }
                                                                    }}
                                                                >
                                                                    🔍 View AI Run
                                                                </Button>
                                                                {m.metadata?.runDuration && (
                                                                    <Text size="10px" c="dimmed">
                                                                        {(m.metadata.runDuration / 1000).toFixed(1)}s
                                                                    </Text>
                                                                )}
                                                                {m.metadata?.runCost && (
                                                                    <Text size="10px" c="dimmed">
                                                                        ${m.metadata.runCost.toFixed(4)}
                                                                    </Text>
                                                                )}
                                                            </Group>
                                                        )}
                                                    </div>
                                                </Group>

                                                {/* Inline Context Card - Business Fitness Dashboard (first message only) */}
                                                {idx === 0 && (
                                                    <div style={{ marginLeft: 42, marginTop: 16 }}>
                                                        {healthLoading ? (
                                                            <LoadingSkeleton type="health" />
                                                        ) : healthError ? (
                                                            <ErrorState
                                                                variant="card"
                                                                message="Failed to load health score data"
                                                                onRetry={() => refetchHealth()}
                                                            />
                                                        ) : (
                                                            <Card withBorder padding="md" radius="md" style={{ background: '#fafbfc', borderColor: '#e1e4e8' }}>
                                                                <Group justify="space-between" mb={12}>
                                                                    <Group gap={8}>
                                                                        <Text size="12px" fw={600} c="#6b7280" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                                                            📊 Your Business Health
                                                                        </Text>
                                                                        <HoverCard width={280} shadow="md">
                                                                            <HoverCard.Target>
                                                                                <IconHelp size={14} color="#9ca3af" style={{ cursor: 'help' }} />
                                                                            </HoverCard.Target>
                                                                            <HoverCard.Dropdown>
                                                                                <Text size="xs" fw={600} mb={6}>What is Health Score?</Text>
                                                                                <Text size="xs" c="dimmed">
                                                                                    Your business health score (0-100) combines Revenue, Operations, and Customer metrics.
                                                                                    Green (70+) is healthy, yellow (50-69) needs attention, red (&lt;50) is critical.
                                                                                </Text>
                                                                            </HoverCard.Dropdown>
                                                                        </HoverCard>
                                                                    </Group>
                                                                    {healthScore?.updated_at && (
                                                                        <Text size="10px" c={isDataStale(healthScore.updated_at, 6) ? 'orange' : 'dimmed'}>
                                                                            {formatRelativeTime(healthScore.updated_at)}
                                                                        </Text>
                                                                    )}
                                                                </Group>

                                                                {/* Overall Score */}
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <Group gap={8} mb={4}>
                                                                        <Text size="11px" c="#8e8ea0" fw={500} tt="uppercase">Overall Health</Text>
                                                                        <Badge
                                                                            size="sm"
                                                                            color={healthScore?.score >= 70 ? 'teal' : healthScore?.score >= 50 ? 'yellow' : 'red'}
                                                                            variant="filled"
                                                                        >
                                                                            {healthScore?.score || 0}/100
                                                                        </Badge>
                                                                    </Group>
                                                                    <div style={{ width: '100%', height: 6, background: '#e5e7eb', borderRadius: 3, overflow: 'hidden' }}>
                                                                        <div style={{
                                                                            width: `${healthScore?.score || 0}%`,
                                                                            height: '100%',
                                                                            background: healthScore?.score >= 70 ? '#10b981' : healthScore?.score >= 50 ? '#f59e0b' : '#ef4444',
                                                                            transition: 'width 0.3s ease'
                                                                        }} />
                                                                    </div>
                                                                </div>

                                                                {/* Traffic Light Breakdown */}
                                                                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 12, marginBottom: 12 }}>
                                                                    <Text size="11px" c="#8e8ea0" fw={500} tt="uppercase" mb={10}>Health Breakdown</Text>

                                                                    {healthScore?.breakdown?.is_sample_data && (
                                                                        <div style={{
                                                                            padding: 8,
                                                                            background: '#fef3c7',
                                                                            borderRadius: 4,
                                                                            marginBottom: 12,
                                                                            border: '1px solid #fbbf24'
                                                                        }}>
                                                                            <Text size="11px" c="#92400e">
                                                                                ⚠️ Using sample data - Connect real integrations for accurate insights
                                                                            </Text>
                                                                        </div>
                                                                    )}

                                                                    <Stack gap={8}>
                                                                        {/* Revenue */}
                                                                        {healthScore?.breakdown?.revenue_available && (
                                                                            <Group gap={8} wrap="nowrap">
                                                                                <div style={{
                                                                                    width: 20,
                                                                                    height: 20,
                                                                                    borderRadius: '50%',
                                                                                    background: healthScore.breakdown.revenue >= 70 ? '#10b981' : healthScore.breakdown.revenue >= 50 ? '#f59e0b' : '#ef4444',
                                                                                    flexShrink: 0
                                                                                }} />
                                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                                    <Group gap={4} mb={2}>
                                                                                        <Text size="13px" fw={500} c="#202123">Revenue</Text>
                                                                                        <Text size="12px" c="#6b7280">{healthScore.breakdown.revenue}/100</Text>
                                                                                        {healthScore.breakdown.is_sample_data && (
                                                                                            <Badge size="xs" color="yellow" variant="filled">SAMPLE</Badge>
                                                                                        )}
                                                                                    </Group>
                                                                                    <Text size="11px" c={healthScore.breakdown.revenue >= 70 ? '#059669' : healthScore.breakdown.revenue >= 50 ? '#8e8ea0' : '#dc2626'}>
                                                                                        {healthScore.breakdown.revenue >= 70 ? '✓ Healthy' : healthScore.breakdown.revenue >= 50 ? '⚠️ Needs Work' : '🚨 Critical'}
                                                                                    </Text>
                                                                                    {healthScore.breakdown.revenue_source && (
                                                                                        <Text size="10px" c="dimmed" mt={2}>
                                                                                            📊 {healthScore.breakdown.revenue_source}
                                                                                        </Text>
                                                                                    )}
                                                                                </div>
                                                                            </Group>
                                                                        )}

                                                                        {/* Operations */}
                                                                        {healthScore?.breakdown?.operations_available && (
                                                                            <Group gap={8} wrap="nowrap">
                                                                                <div style={{
                                                                                    width: 20,
                                                                                    height: 20,
                                                                                    borderRadius: '50%',
                                                                                    background: healthScore.breakdown.operations >= 70 ? '#10b981' : healthScore.breakdown.operations >= 50 ? '#f59e0b' : '#ef4444',
                                                                                    flexShrink: 0
                                                                                }} />
                                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                                    <Group gap={4} mb={2}>
                                                                                        <Text size="13px" fw={500} c="#202123">Operations</Text>
                                                                                        <Text size="12px" c="#6b7280">{healthScore.breakdown.operations}/100</Text>
                                                                                        {healthScore.breakdown.is_sample_data && (
                                                                                            <Badge size="xs" color="yellow" variant="filled">SAMPLE</Badge>
                                                                                        )}
                                                                                    </Group>
                                                                                    <Text size="11px" c={healthScore.breakdown.operations >= 70 ? '#059669' : healthScore.breakdown.operations >= 50 ? '#8e8ea0' : '#dc2626'}>
                                                                                        {healthScore.breakdown.operations >= 70 ? '✓ Healthy' : healthScore.breakdown.operations >= 50 ? '⚠️ Needs Work' : '🚨 Critical'}
                                                                                    </Text>
                                                                                    {healthScore.breakdown.operations_source && (
                                                                                        <Text size="10px" c="dimmed" mt={2}>
                                                                                            📊 {healthScore.breakdown.operations_source}
                                                                                        </Text>
                                                                                    )}
                                                                                    {healthScore.breakdown.operations < 70 && (
                                                                                        <Button
                                                                                            size="xs"
                                                                                            variant="subtle"
                                                                                            onClick={() => {
                                                                                                setInput("How can I improve my operations score?")
                                                                                                setTimeout(() => sendMessage(), 100)
                                                                                            }}
                                                                                            mt={4}
                                                                                            styles={{
                                                                                                root: {
                                                                                                    fontSize: '11px',
                                                                                                    height: 24,
                                                                                                    padding: '0 8px',
                                                                                                    color: healthScore.breakdown.operations >= 50 ? '#d97706' : '#dc2626'
                                                                                                }
                                                                                            }}
                                                                                        >
                                                                                            Fix This →
                                                                                        </Button>
                                                                                    )}
                                                                                </div>
                                                                            </Group>
                                                                        )}

                                                                        {/* Customer */}
                                                                        {healthScore?.breakdown?.customer_available && (
                                                                            <Group gap={8} wrap="nowrap">
                                                                                <div style={{
                                                                                    width: 20,
                                                                                    height: 20,
                                                                                    borderRadius: '50%',
                                                                                    background: healthScore.breakdown.customer >= 70 ? '#10b981' : healthScore.breakdown.customer >= 50 ? '#f59e0b' : '#ef4444',
                                                                                    flexShrink: 0
                                                                                }} />
                                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                                    <Group gap={4} mb={2}>
                                                                                        <Text size="13px" fw={500} c="#202123">Customer</Text>
                                                                                        <Text size="12px" c="#6b7280">{healthScore.breakdown.customer}/100</Text>
                                                                                        {healthScore.breakdown.is_sample_data && (
                                                                                            <Badge size="xs" color="yellow" variant="filled">SAMPLE</Badge>
                                                                                        )}
                                                                                    </Group>
                                                                                    <Text size="11px" c={healthScore.breakdown.customer >= 70 ? '#059669' : healthScore.breakdown.customer >= 50 ? '#8e8ea0' : '#dc2626'}>
                                                                                        {healthScore.breakdown.customer >= 70 ? '✓ Healthy' : healthScore.breakdown.customer >= 50 ? '⚠️ Needs Work' : '🚨 Critical'}
                                                                                    </Text>
                                                                                    {healthScore.breakdown.customer_source && (
                                                                                        <Text size="10px" c="dimmed" mt={2}>
                                                                                            📊 {healthScore.breakdown.customer_source}
                                                                                        </Text>
                                                                                    )}
                                                                                    {healthScore.breakdown.customer < 70 && (
                                                                                        <Button
                                                                                            size="xs"
                                                                                            variant={healthScore.breakdown.customer < 50 ? "filled" : "subtle"}
                                                                                            color={healthScore.breakdown.customer < 50 ? "red" : undefined}
                                                                                            onClick={() => {
                                                                                                setInput("How can I improve my customer health score?")
                                                                                                setTimeout(() => sendMessage(), 100)
                                                                                            }}
                                                                                            mt={4}
                                                                                            styles={{
                                                                                                root: {
                                                                                                    fontSize: '11px',
                                                                                                    height: 24,
                                                                                                    padding: '0 8px'
                                                                                                }
                                                                                            }}
                                                                                        >
                                                                                            {healthScore.breakdown.customer < 50 ? 'Fix This Now 🚀' : 'Fix This →'}
                                                                                        </Button>
                                                                                    )}
                                                                                </div>
                                                                            </Group>
                                                                        )}

                                                                        {/* No data message */}
                                                                        {!healthScore?.breakdown?.revenue_available &&
                                                                            !healthScore?.breakdown?.operations_available &&
                                                                            !healthScore?.breakdown?.customer_available && (
                                                                                <Text size="12px" c="dimmed" ta="center" py={12}>
                                                                                    No health data available. Connect your data sources to see metrics.
                                                                                </Text>
                                                                            )}
                                                                    </Stack>
                                                                </div>

                                                                {/* Task Summary */}
                                                                <Group gap={8} style={{ borderTop: '1px solid #e5e7eb', paddingTop: 12 }}>
                                                                    <div>
                                                                        <Text size="11px" c="#8e8ea0" fw={500} tt="uppercase" mb={4}>Pending Tasks</Text>
                                                                        <Text size="18px" fw={600} c="#202123">{tasksData?.length || 0}</Text>
                                                                    </div>
                                                                    <Button
                                                                        size="xs"
                                                                        variant="light"
                                                                        onClick={() => navigate('/planner')}
                                                                        ml="auto"
                                                                        styles={{ root: { fontSize: '11px' } }}
                                                                    >
                                                                        View All →
                                                                    </Button>
                                                                </Group>
                                                            </Card>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <Group gap={12} align="flex-start" wrap="nowrap">
                                                <div style={{
                                                    width: 30,
                                                    height: 30,
                                                    borderRadius: '4px',
                                                    background: '#19c37d',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    flexShrink: 0,
                                                    fontSize: 14
                                                }}>
                                                    👤
                                                </div>
                                                <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }}>
                                                    <Text
                                                        size="15px"
                                                        style={{
                                                            whiteSpace: 'pre-wrap',
                                                            lineHeight: 1.7,
                                                            color: '#353740',
                                                            fontWeight: 400
                                                        }}
                                                    >
                                                        {m.content}
                                                    </Text>
                                                </div>
                                            </Group>
                                        )}
                                    </div>
                                ))}
                            </Stack>
                        </div>
                    </ScrollArea>

                    {/* Composer - CLEAN, SUBTLE BORDER */}
                    <div style={{ background: 'white', padding: '20px 0 32px' }}>
                        <div style={{ maxWidth: 750, margin: '0 auto', padding: '0 24px' }}>
                            {/* Coach selector, tools, and settings bar */}
                            <Group gap={8} mb={8} wrap="wrap">
                                {/* Coach Selector */}
                                <Menu shadow="sm" width={200}>
                                    <Menu.Target>
                                        <Button
                                            size="xs"
                                            variant="light"
                                            rightSection={<IconChevronDown size={12} />}
                                            styles={{
                                                root: {
                                                    fontSize: '11px',
                                                    height: 26,
                                                    padding: '0 10px',
                                                    background: '#f3f4f6',
                                                    border: 'none'
                                                }
                                            }}
                                        >
                                            {AGENTS.find(a => a.id === selectedAgent)?.emoji} {AGENTS.find(a => a.id === selectedAgent)?.label}
                                        </Button>
                                    </Menu.Target>
                                    <Menu.Dropdown>
                                        <Menu.Label>Switch Coach</Menu.Label>
                                        {AGENTS.map(a => (
                                            <Menu.Item
                                                key={a.id}
                                                onClick={() => setSelectedAgent(a.id)}
                                                leftSection={<span style={{ fontSize: '14px' }}>{a.emoji}</span>}
                                                bg={selectedAgent === a.id ? '#f3f4f6' : undefined}
                                            >
                                                {a.label}
                                            </Menu.Item>
                                        ))}
                                    </Menu.Dropdown>
                                </Menu>

                                {/* Tool/Connector Selector */}
                                {(suggestedTools.length > 0 || enabledConnectors.length > 0) && (
                                    <>
                                        <div style={{ width: 1, height: 20, background: '#e5e7eb', margin: '0 4px' }} />
                                        <Menu shadow="sm" width={280}>
                                            <Menu.Target>
                                                <Button
                                                    size="xs"
                                                    variant="light"
                                                    rightSection={<IconChevronDown size={12} />}
                                                    styles={{
                                                        root: {
                                                            fontSize: '11px',
                                                            height: 26,
                                                            padding: '0 10px',
                                                            background: '#f3f4f6',
                                                            border: 'none',
                                                            color: '#6b21a8'
                                                        }
                                                    }}
                                                >
                                                    🔧 Tools ({suggestedTools.length})
                                                </Button>
                                            </Menu.Target>
                                            <Menu.Dropdown>
                                                <Menu.Label>Connected Tools</Menu.Label>
                                                {(() => {
                                                    // Group connectors by type to avoid duplicates
                                                    const connectorsByType = enabledConnectors.reduce((acc: any, connector: any) => {
                                                        const type = connector.connector_type
                                                        if (!acc[type]) {
                                                            acc[type] = []
                                                        }
                                                        acc[type].push(connector)
                                                        return acc
                                                    }, {})

                                                    return Object.entries(connectorsByType).map(([connectorType, connectors]: [string, any]) => {
                                                        const connectorTools = suggestedTools.filter((t) => t.connector === connectorType)
                                                        if (connectorTools.length === 0) return null

                                                        const connectorList = connectors as any[]
                                                        const displayName = connectorList.length > 1
                                                            ? `${connectorType.toUpperCase()} (${connectorList.length} sources)`
                                                            : connectorList[0].display_name || connectorType

                                                        return (
                                                            <div key={connectorType}>
                                                                <Menu.Label style={{ fontSize: '10px', textTransform: 'uppercase', color: '#9ca3af', marginTop: 8 }}>
                                                                    {displayName}
                                                                </Menu.Label>
                                                                {connectorTools.map((tool) => (
                                                                    <Menu.Item
                                                                        key={tool.id}
                                                                        leftSection={<span style={{ fontSize: '12px' }}>🔧</span>}
                                                                        onClick={() => {
                                                                            // Generate contextual prompt based on tool
                                                                            let prompt = ''
                                                                            if (tool.id.includes('stock') || tool.id.includes('inventory')) {
                                                                                prompt = `Check my current inventory stock levels and show which items are low or out of stock`
                                                                            } else if (tool.id.includes('sales') || tool.id.includes('orders')) {
                                                                                prompt = `Show me recent sales orders and their status`
                                                                            } else if (tool.id.includes('purchase') || tool.id.includes('po')) {
                                                                                prompt = `Check purchase orders and show what needs to be reordered`
                                                                            } else if (tool.id.includes('csv.query')) {
                                                                                prompt = `Query my CSV data to find top products by revenue`
                                                                            } else if (tool.id.includes('csv.analyze')) {
                                                                                prompt = `Analyze my CSV data for trends and insights`
                                                                            } else if (tool.id.includes('csv.aggregate')) {
                                                                                prompt = `Aggregate my CSV data by category and show summary metrics`
                                                                            } else {
                                                                                prompt = `Use "${tool.label}" to ${tool.description?.toLowerCase() || 'analyze the data'}`
                                                                            }
                                                                            setInput(prompt)
                                                                        }}
                                                                        styles={{
                                                                            item: {
                                                                                fontSize: '12px',
                                                                                padding: '6px 12px',
                                                                                cursor: 'pointer'
                                                                            }
                                                                        }}
                                                                    >
                                                                        <div>
                                                                            <div style={{ fontWeight: 500 }}>{tool.label}</div>
                                                                            {tool.description && (
                                                                                <div style={{ fontSize: '10px', color: '#6b7280', marginTop: 2 }}>
                                                                                    {tool.description}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    </Menu.Item>
                                                                ))}
                                                            </div>
                                                        )
                                                    })
                                                })()}
                                            </Menu.Dropdown>
                                        </Menu>
                                    </>
                                )}

                                {/* Settings button */}
                                <Button
                                    size="xs"
                                    variant="subtle"
                                    onClick={() => setSettingsOpen(true)}
                                    ml="auto"
                                    styles={{
                                        root: {
                                            fontSize: '11px',
                                            height: 26,
                                            padding: '0 10px',
                                            color: '#6b7280'
                                        }
                                    }}
                                >
                                    ⚙️ Settings
                                </Button>
                            </Group>

                            {/* Input box */}
                            <div style={{
                                display: 'flex',
                                gap: '12px',
                                alignItems: 'flex-end',
                                background: '#fff',
                                borderRadius: '12px',
                                padding: '12px 16px',
                                border: '1px solid #d1d5db',
                                boxShadow: '0 0 0 1px rgba(0,0,0,0.05)'
                            }}>
                                <Textarea
                                    autosize
                                    minRows={1}
                                    maxRows={6}
                                    placeholder="Message AI Business Coach..."
                                    value={input}
                                    onChange={(e) => setInput(e.currentTarget.value)}
                                    onKeyDown={handleKeyDown}
                                    disabled={isSending}
                                    style={{ flex: 1 }}
                                    styles={{
                                        input: {
                                            border: 'none',
                                            background: 'transparent',
                                            padding: '0',
                                            fontSize: '15px',
                                            resize: 'none',
                                            color: '#353740'
                                        }
                                    }}
                                />
                                {isSending ? (
                                    <Button
                                        onClick={stopGeneration}
                                        color="red"
                                        variant="subtle"
                                        size="sm"
                                        styles={{
                                            root: {
                                                borderRadius: '8px',
                                                minWidth: '36px',
                                                height: '36px',
                                                padding: '0 12px'
                                            }
                                        }}
                                    >
                                        <IconPlayerStop size={16} />
                                    </Button>
                                ) : (
                                    <Button
                                        onClick={sendMessage}
                                        disabled={!input.trim()}
                                        size="sm"
                                        styles={{
                                            root: {
                                                borderRadius: '8px',
                                                background: input.trim() ? '#202123' : '#d1d5db',
                                                border: 'none',
                                                minWidth: '36px',
                                                height: '36px',
                                                padding: '0 12px'
                                            }
                                        }}
                                    >
                                        <IconSend size={16} />
                                    </Button>
                                )}
                            </div>

                            {/* Guided Question Prompts (only show when input is empty) */}
                            {!input && messages.length <= 1 && (
                                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #e5e7eb' }}>
                                    {suggestedPrompts.length > 0 ? (
                                        <>
                                            <Text size="11px" c="#8e8ea0" fw={500} mb={8}>� Try these prompts:</Text>
                                            <Group gap={6}>
                                                {suggestedPrompts.map((p) => (
                                                    <Button
                                                        key={p.id}
                                                        size="xs"
                                                        variant="light"
                                                        onClick={() => {
                                                            setInput(p.text)
                                                            setTimeout(() => sendMessage(), 100)
                                                        }}
                                                        styles={{
                                                            root: {
                                                                fontSize: '11px',
                                                                fontWeight: 400,
                                                                height: 28,
                                                                background: '#f9fafb',
                                                                border: '1px solid #e5e7eb',
                                                                color: '#374151'
                                                            }
                                                        }}
                                                    >
                                                        {p.title}
                                                    </Button>
                                                ))}
                                            </Group>
                                        </>
                                    ) : (
                                        <>
                                            <Text size="11px" c="#8e8ea0" fw={500} mb={8}>�💬 Suggested Questions:</Text>
                                            <Group gap={6}>
                                                {(() => {
                                                    const score = healthScore?.score || 0
                                                    const hasGoals = (goalsData?.length || 0) > 0
                                                    const hasTasks = (tasksData?.length || 0) > 0

                                                    // Smart suggestions based on context
                                                    const suggestions = []
                                                    if (score < 50) {
                                                        suggestions.push("Why is my health score low?")
                                                    } else {
                                                        suggestions.push("Show me yesterday's sales")
                                                    }

                                                    if (hasTasks) {
                                                        suggestions.push("What should I focus on today?")
                                                    } else {
                                                        suggestions.push("Create a weekly action plan")
                                                    }

                                                    if (hasGoals) {
                                                        suggestions.push("Check my goal progress")
                                                    } else {
                                                        suggestions.push("Help me set a new goal")
                                                    }

                                                    return suggestions.map((s, i) => (
                                                        <Button
                                                            key={i}
                                                            size="xs"
                                                            variant="light"
                                                            onClick={() => setInput(s)}
                                                            styles={{
                                                                root: {
                                                                    fontSize: '11px',
                                                                    fontWeight: 400,
                                                                    height: 28,
                                                                    background: '#f9fafb',
                                                                    border: '1px solid #e5e7eb',
                                                                    color: '#6b7280'
                                                                }
                                                            }}
                                                        >
                                                            {s}
                                                        </Button>
                                                    ))
                                                })()}
                                            </Group>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Settings modal */}
                <CoachSettings
                    opened={settingsOpen}
                    onClose={() => setSettingsOpen(false)}
                    selectedPersona={selectedAgent}
                    onPersonaChange={setSelectedAgent}
                    selectedDataSources={selectedDataSources}
                    onDataSourcesChange={setSelectedDataSources}
                    includeEvidence={includeEvidence}
                    onIncludeEvidenceChange={setIncludeEvidence}
                    includeForecast={includeForecast}
                    onIncludeForecastChange={setIncludeForecast}
                    personas={AGENTS.map(a => ({ id: a.id, name: a.label, emoji: a.emoji, description: '', expertise: [], tone: 'neutral' }))}
                    dataSources={[]}
                />
            </div >
        </>
    )
}
