import { showNotification } from '@mantine/notifications'
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { triggerRun } from '../lib/api'
import { trackEvent } from '../lib/telemetry'
import { useAuthStore } from '../stores/auth'
import AgentActionCard from './AgentActionCard'

type Message = {
    role: 'user' | 'agent'
    text: string
    actions?: ActionCard[]
}

type ActionCard = {
    label: string
    description: string
    badge?: string
    cta?: string
    onSelect: () => void
    event?: string
    eventPayload?: Record<string, unknown>
}

const DEFAULT_PROMPTS = [
    'Create a plan to boost weekday lunch traffic',
    'How should I staff for the weekend rush?',
    'Draft a message to explain today’s forecast to the team',
]

type ChatShellProps = {
    title?: string
    description?: string
    prompts?: string[]
    templateId?: string
    planHint?: string
    planId?: string
}

export default function ChatShell({ title, description, prompts = DEFAULT_PROMPTS, templateId = 'inventory_basic', planHint, planId }: ChatShellProps) {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()
    const [messages, setMessages] = React.useState<Message[]>([
        {
            role: 'agent',
            text: description ?? 'Hi! I’m the Dyocense planning copilot. Ask me for a plan, a forecast, or a next action and I’ll give you the answer plus one-click cards.',
        },
    ])
    const [input, setInput] = React.useState('')
    const [loading, setLoading] = React.useState(false)

    const scrollRef = React.useRef<HTMLDivElement | null>(null)

    React.useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    const composeActions = (runId?: string): ActionCard[] => [
        {
            label: 'Open Planner',
            description: 'Review milestones, reassign owners, and regenerate steps.',
            badge: 'Plan',
            cta: 'Open',
            onSelect: () => navigate('/planner'),
            event: 'chat_action_open_planner',
        },
        {
            label: 'Launch Agents',
            description: 'Delegate follow-ups (emails, schedules, promos) to copilots.',
            badge: 'Automation',
            cta: 'Run',
            onSelect: () => navigate('/agents'),
            event: 'chat_action_launch_agents',
        },
        {
            label: 'View Evidence',
            description: runId ? `Inspect run ${runId} status in the execution console.` : 'Check latest runs + audit log.',
            badge: 'Exec',
            cta: 'View',
            onSelect: () => navigate('/executor'),
            event: 'chat_action_view_evidence',
            eventPayload: { run_id: runId },
        },
    ]

    const sendMessage = async (prompt?: string) => {
        const value = (prompt ?? input).trim()
        if (!value) return
        setMessages((prev) => [...prev, { role: 'user', text: value }])
        trackEvent('chat_prompt_submitted', { source: title ?? 'workspace', prompt: value })
        setInput('')
        setLoading(true)

        try {
            const response = apiToken
                ? await triggerRun(
                      {
                          template_id: templateId,
                          goal: value,
                          project_id: `chat-${Date.now().toString(36)}`,
                          mode: 'plan',
                          ...(planId ? { plan_id: planId } : {}),
                      },
                      apiToken,
                  )
                : null

            const currentPlanHint = planHint ?? ''
            const agentMessage = response
                ? `Started a Dyocense run (${response.run_id}) using the ${templateId} template. I’ll stream progress into the execution console. ${currentPlanHint}`
                : `Here’s a suggested sequence based on our playbooks. ${currentPlanHint}`
            if (response) {
                trackEvent('chat_run_triggered', { run_id: response.run_id, template_id: templateId, prompt: value })
                showNotification({
                    title: 'Run started',
                    message: `Tracking run ${response.run_id} in the execution console.`,
                    color: 'green',
                })
            } else {
                trackEvent('chat_run_stubbed', { template_id: templateId, prompt: value })
                showNotification({
                    title: 'Sample plan ready',
                    message: 'Connect your workspace to trigger live runs.',
                    color: 'blue',
                })
            }

            setMessages((prev) => [
                ...prev,
                {
                    role: 'agent',
                    text: agentMessage,
                    actions: composeActions(response?.run_id),
                },
            ])
        } catch (err) {
            trackEvent('chat_run_error', { template_id: templateId, prompt: value })
            showNotification({
                title: 'Unable to reach orchestration',
                message: 'I’ll keep your prompt locally—try again once you reconnect.',
                color: 'red',
            })
            setMessages((prev) => [
                ...prev,
                {
                    role: 'agent',
                    text: 'I could not reach the orchestration service. I’ll keep your prompt locally—try again once you reconnect.',
                    actions: composeActions(),
                },
            ])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="chat-shell">
            {title && (
                <div className="mb-3">
                    <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-600">{title}</p>
                    {description && <p className="text-xs text-slate-400">{description}</p>}
                </div>
            )}
            <div className="chat-shell__messages" ref={scrollRef}>
                {messages.map((msg, idx) => (
                    <div className={`chat-message chat-message--${msg.role}`} key={`chat-${idx}`}>
                        <p>{msg.text}</p>
                        {msg.actions && (
                            <div className="chat-message__actions">
                                {msg.actions.map((action) => (
                                    <AgentActionCard
                                        key={action.label}
                                        {...action}
                                        onSelect={() => {
                                            if (action.event) trackEvent(action.event, { source: title ?? 'workspace', ...(action.eventPayload ?? {}) })
                                            action.onSelect()
                                        }}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                ))}
                {loading && <div className="chat-typing">Thinking…</div>}
            </div>

            <div className="chat-shell__suggestions">
                {prompts.map((prompt) => (
                    <button
                        className="suggestion-chip"
                        key={prompt}
                        onClick={() => {
                            trackEvent('chat_prompt_chip_clicked', { source: title ?? 'workspace', prompt })
                            sendMessage(prompt)
                        }}
                        type="button"
                    >
                        {prompt}
                    </button>
                ))}
            </div>

            <div className="chat-shell__input">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask for a plan, forecast, or follow-up…"
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    disabled={loading}
                />
                <button onClick={() => sendMessage()} disabled={loading || !input.trim()} type="button">
                    Send
                </button>
            </div>
        </div>
    )
}
