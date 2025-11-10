import { Button, Progress, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BusinessHealthScore from '../components/BusinessHealthScore'
import WeeklyPlan from '../components/WeeklyPlan'
import { useAuthStore } from '../stores/auth'
import { calculateHealthScore, getBusinessMetricsFromConnectors } from '../utils/healthScore'
import { generateTasksForGoal, type Goal } from '../utils/planGenerator'

type WelcomeStep = 'score-reveal' | 'goal-selection' | 'plan-preview'

const goalSuggestions = [
    {
        title: 'Grow Revenue',
        description: 'Increase monthly sales and customer lifetime value',
        icon: '💰',
        category: 'revenue' as const,
        placeholder: 'e.g., Increase Q4 revenue by 25%',
    },
    {
        title: 'Improve Cash Flow',
        description: 'Reduce payment delays and optimize expenses',
        icon: '💵',
        category: 'operations' as const,
        placeholder: 'e.g., Improve cash flow by reducing outstanding invoices',
    },
    {
        title: 'Win More Customers',
        description: 'Increase conversion rate and customer retention',
        icon: '🎯',
        category: 'customer' as const,
        placeholder: 'e.g., Build loyalty program to increase repeat customers by 35%',
    },
    {
        title: 'Optimize Operations',
        description: 'Improve efficiency and reduce operational costs',
        icon: '⚙️',
        category: 'operations' as const,
        placeholder: 'e.g., Improve inventory turnover rate to 95%',
    },
]

export default function Welcome() {
    const user = useAuthStore((s) => s.user)
    const navigate = useNavigate()

    const [step, setStep] = useState<WelcomeStep>('score-reveal')
    const [healthScore, setHealthScore] = useState<number>(0)
    const [animating, setAnimating] = useState(false)
    const [selectedSuggestion, setSelectedSuggestion] = useState<number | null>(null)
    const [customGoal, setCustomGoal] = useState('')
    const [previewTasks, setPreviewTasks] = useState<any[]>([])

    // Step 1: Calculate and reveal health score with animation
    const revealHealthScore = async () => {
        setAnimating(true)
        const metrics = await getBusinessMetricsFromConnectors()
        const result = calculateHealthScore(metrics)

        // Animate score counting up from 0 to actual score
        let current = 0
        const target = result.overallScore
        const duration = 1500 // 1.5 seconds
        const increment = target / (duration / 30)

        const interval = setInterval(() => {
            current += increment
            if (current >= target) {
                setHealthScore(target)
                clearInterval(interval)
                setAnimating(false)
            } else {
                setHealthScore(Math.floor(current))
            }
        }, 30)
    }

    // Initialize score reveal on mount
    useState(() => {
        if (step === 'score-reveal' && healthScore === 0) {
            setTimeout(revealHealthScore, 500)
        }
    })

    // Step 2: Handle goal selection
    const handleGoalSelection = () => {
        if (selectedSuggestion === null && !customGoal) return

        // Generate preview tasks from selected goal
        const suggestion = selectedSuggestion !== null ? goalSuggestions[selectedSuggestion] : null
        const goalDescription = customGoal || suggestion?.placeholder || ''

        const mockGoal: Goal = {
            id: 'welcome-goal-1',
            title: suggestion?.title || 'Your Goal',
            description: goalDescription,
            current: 0,
            target: 100,
            unit: '%',
            category: suggestion?.category || 'revenue',
            deadline: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(), // 90 days from now
        }

        const tasks = generateTasksForGoal(mockGoal)
        setPreviewTasks(
            tasks.slice(0, 5).map((task) => ({
                id: task.id,
                title: task.title,
                category: task.category,
                completed: false,
            })),
        )

        setStep('plan-preview')
    }

    // Step 3: Complete onboarding
    const completeOnboarding = () => {
        // Mark as onboarded in localStorage
        localStorage.setItem('hasCompletedOnboarding', 'true')
        navigate('/home', { replace: true })
    }

    const progressValue = step === 'score-reveal' ? 33 : step === 'goal-selection' ? 66 : 100

    return (
        <div className="page-shell">
            <div className="mx-auto max-w-4xl space-y-8">
                {/* Progress indicator */}
                <div className="space-y-2">
                    <Progress value={progressValue} size="sm" radius="xl" />
                    <Text size="sm" c="dimmed" ta="center">
                        Step {step === 'score-reveal' ? '1' : step === 'goal-selection' ? '2' : '3'} of 3
                    </Text>
                </div>

                {/* Step 1: Health Score Reveal */}
                {step === 'score-reveal' && (
                    <div className="glass-panel space-y-8 text-center">
                        <div className="space-y-4">
                            <div className="mx-auto h-16 w-16 rounded-full bg-brand/10 p-4">
                                <span className="text-3xl">👋</span>
                            </div>
                            <Title order={2}>Hi {user?.name || 'there'}! I'm your business coach.</Title>
                            <Text c="dimmed">Let's see how your business is performing...</Text>
                        </div>

                        <div className="flex justify-center">
                            <BusinessHealthScore score={healthScore} trend={0} />
                        </div>

                        {!animating && healthScore > 0 && (
                            <div className="space-y-4">
                                <Title order={3}>Your Business Health Score: {healthScore}</Title>
                                <Text size="lg" c={healthScore >= 80 ? 'green' : healthScore >= 60 ? 'teal' : 'orange'} fw={600}>
                                    {healthScore >= 80 ? 'Excellent! 💪' : healthScore >= 60 ? 'Strong Performance! 👍' : 'Room to Improve! 📈'}
                                </Text>
                                <Text c="dimmed">
                                    {healthScore >= 80
                                        ? "You're in better shape than 85% of similar businesses."
                                        : healthScore >= 60
                                            ? "You're performing better than 70% of similar businesses."
                                            : "Let's work together to boost this score!"}
                                </Text>
                                <Button size="lg" onClick={() => setStep('goal-selection')}>
                                    Show me how to improve
                                </Button>
                            </div>
                        )}
                    </div>
                )}

                {/* Step 2: Goal Selection */}
                {step === 'goal-selection' && (
                    <div className="glass-panel space-y-6">
                        <div className="space-y-3 text-center">
                            <div className="mx-auto h-16 w-16 rounded-full bg-brand/10 p-4">
                                <span className="text-3xl">🎯</span>
                            </div>
                            <Title order={2}>Every business needs goals. What's your #1 priority?</Title>
                            <Text c="dimmed">Pick a suggestion or write your own</Text>
                        </div>

                        <Stack gap="md">
                            {goalSuggestions.map((suggestion, index) => (
                                <button
                                    className={`rounded-2xl border-2 p-6 text-left transition-all ${selectedSuggestion === index
                                            ? 'border-brand bg-brand/5'
                                            : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
                                        }`}
                                    key={index}
                                    onClick={() => {
                                        setSelectedSuggestion(index)
                                        setCustomGoal('')
                                    }}
                                    type="button"
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 text-2xl">{suggestion.icon}</div>
                                        <div className="flex-1">
                                            <Text fw={600} size="lg">
                                                {suggestion.title}
                                            </Text>
                                            <Text size="sm" c="dimmed">
                                                {suggestion.description}
                                            </Text>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </Stack>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-white/10"></div>
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-[#0f172a] px-2 text-slate-400">Or write your own</span>
                            </div>
                        </div>

                        <Textarea
                            leftSection={<IconSparkles size={18} />}
                            placeholder="e.g., I want to increase revenue by 25% by end of Q4"
                            minRows={3}
                            value={customGoal}
                            onChange={(e) => {
                                setCustomGoal(e.target.value)
                                setSelectedSuggestion(null)
                            }}
                        />

                        <Button disabled={selectedSuggestion === null && !customGoal} fullWidth onClick={handleGoalSelection} size="lg">
                            Create my action plan
                        </Button>
                    </div>
                )}

                {/* Step 3: Plan Preview */}
                {step === 'plan-preview' && (
                    <div className="glass-panel space-y-6">
                        <div className="space-y-3 text-center">
                            <div className="mx-auto h-16 w-16 rounded-full bg-brand/10 p-4">
                                <span className="text-3xl">✅</span>
                            </div>
                            <Title order={2}>Here's your first week's action plan</Title>
                            <Text c="dimmed">
                                Each week, I'll give you 5–7 tasks to move you closer to your goal. Check them off, build streaks, and celebrate milestones
                                together!
                            </Text>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                            <WeeklyPlan tasks={previewTasks} />
                        </div>

                        <div className="space-y-3">
                            <Text fw={600} size="sm">
                                What happens next:
                            </Text>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li className="flex gap-3">
                                    <span className="text-brand">✓</span>
                                    Your dashboard shows health score, goals & weekly tasks
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-brand">✓</span>
                                    Check off tasks to build streaks and improve your score
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-brand">✓</span>
                                    Get milestone celebrations when you hit 25%, 50%, 75%, 100%
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-brand">✓</span>
                                    Weekly summaries show your progress & momentum
                                </li>
                            </ul>
                        </div>

                        <Button fullWidth onClick={completeOnboarding} size="lg">
                            Let's do this! 🚀
                        </Button>
                    </div>
                )}
            </div>
        </div>
    )
}
