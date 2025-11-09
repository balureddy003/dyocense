import { Badge, Button, Text, Title } from '@mantine/core'
import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import AgentActionCard from '../components/AgentActionCard'
import ChatShell from '../components/ChatShell'
import { toolConfigs } from '../data/tools'
import { useAuthStore } from '../stores/auth'

const useFocusedTool = () => {
    const location = useLocation()
    return useMemo(() => new URLSearchParams(location.search).get('tool'), [location.search])
}

export default function Tools() {
    const tenantId = useAuthStore((s: any) => s.tenantId)
    const focusedTool = useFocusedTool()

    return (
        <div className="page-shell space-y-10">
            <section className="glass-panel--light space-y-4 text-center">
                <p className="eyebrow text-brand-600">Planner · Agents · Executor</p>
                <Title order={1}>Pick the right cockpit for today’s work</Title>
                <Text c="neutral.600" maw={560} mx="auto">
                    Every workflow is powered by the Dyocense decision kernel. Start in Planner, delegate to Agents, and track outcomes without context switching.
                </Text>
            </section>

            <section className="glass-panel grid gap-8 md:grid-cols-2">
                <div className="space-y-4">
                    <p className="eyebrow text-brand-200">Try the copilot first</p>
                    <Title order={3} c="white">
                        Even before signup, see how the chat drives action cards.
                    </Title>
                    <Text c="gray.2">
                        Ask something in natural language and we’ll show the Planner/Agents/Executor cards you’ll unlock once you create a workspace.
                    </Text>
                </div>
                <ChatShell
                    title="GenAI preview"
                    description="This is a read-only teaser. Full orchestration triggers after signup."
                    prompts={['How would Dyocense plan a weekend pop-up?', 'What steps do agents take for a staffing shortage?']}
                />
            </section>

            <section className="space-y-6">
                {toolConfigs.map((tool) => {
                    const isFocused = tool.key === focusedTool
                    return (
                        <div key={tool.key} id={tool.key} className={`glass-panel--light space-y-6 ${isFocused ? 'ring-2 ring-brand/40' : ''}`}>
                            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                                <div className="space-y-3">
                                    <Title order={3}>{tool.title}</Title>
                                    <Text c="neutral.600">{tool.summary}</Text>
                                    <div className="flex flex-wrap gap-2">
                                        {tool.metrics.map((metric) => (
                                            <Badge key={metric} color="brand" variant="light">
                                                {metric}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex w-full flex-col gap-3 md:w-auto">
                                    <Button component={Link} to={tenantId ? tool.route : `/signup?tool=${tool.key}`} radius="xl">
                                        {tenantId ? tool.cta : 'Start with sample data'}
                                    </Button>
                                </div>
                            </div>

                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-3">
                                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-neutral-500">What you get</p>
                                    <ul className="space-y-2 text-sm text-neutral-700">
                                        {tool.outcomes.map((line) => (
                                            <li key={line} className="flex items-start gap-2">
                                                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-brand-500"></span>
                                                {line}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div className="space-y-3">
                                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-neutral-500">Preview cards</p>
                                    <div className="space-y-2">
                                        <AgentActionCard
                                            label="Ask the planner"
                                            description="“What’s the fastest path to launch?”"
                                            badge="Chat"
                                            cta="Try"
                                            onSelect={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                        />
                                        <AgentActionCard
                                            label="One-click actions"
                                            description="Approve, assign, or log evidence from the chat."
                                            badge="Cards"
                                            cta="See demo"
                                            onSelect={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                        />
                                        <Text size="xs" c="neutral.500">
                                            Login to connect your workspace and unlock live orchestration runs.
                                        </Text>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </section>
        </div>
    )
}
