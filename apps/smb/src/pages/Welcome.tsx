import { Button, Progress, Stack, Text, Title } from '@mantine/core'
import { IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'

type WelcomeStep = 'intro' | 'preview-value' | 'next-steps'

// Health score categories that users will track once they connect data
const healthCategories = [
    { icon: '💰', label: 'Revenue Growth', description: 'Track sales trends and growth rate' },
    { icon: '💵', label: 'Cash Flow', description: 'Monitor incoming and outgoing cash' },
    { icon: '📊', label: 'Profit Margins', description: 'Analyze profitability across products' },
    { icon: '📦', label: 'Inventory Health', description: 'Optimize stock levels and turnover' },
    { icon: '⭐', label: 'Customer Satisfaction', description: 'Measure ratings and retention' },
    { icon: '🚚', label: 'Operations', description: 'Track order fulfillment and efficiency' },
]

export default function Welcome() {
    const user = useAuthStore((s) => s.user)
    const navigate = useNavigate()

    const [step, setStep] = useState<WelcomeStep>('intro')

    const progressValue = step === 'intro' ? 33 : step === 'preview-value' ? 66 : 100

    const handleSkip = () => {
        localStorage.setItem('hasCompletedOnboarding', 'true')
        navigate('/home', { replace: true })
    }

    const handleConnectData = () => {
        localStorage.setItem('hasCompletedOnboarding', 'true')
        navigate('/connectors', { replace: true })
    }

    const handleGoToDashboard = () => {
        localStorage.setItem('hasCompletedOnboarding', 'true')
        navigate('/home', { replace: true })
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
            <div className="mx-auto max-w-5xl space-y-6">
                {/* Progress indicator */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        {step !== 'intro' && (
                            <Button
                                variant="subtle"
                                size="sm"
                                onClick={() => setStep(step === 'next-steps' ? 'preview-value' : 'intro')}
                            >
                                ← Back
                            </Button>
                        )}
                        {step === 'intro' && <div />}
                        <Button variant="subtle" size="sm" c="dimmed" onClick={handleSkip}>
                            Skip for now
                        </Button>
                    </div>
                    <Progress value={progressValue} size="sm" radius="xl" color="indigo" />
                    <Text size="sm" c="dimmed" ta="center">
                        Step {step === 'intro' ? '1' : step === 'preview-value' ? '2' : '3'} of 3 · Takes about 2 minutes
                    </Text>
                </div>

                {/* Step 1: Welcome & Introduction */}
                {step === 'intro' && (
                    <Paper p="xl" radius="lg" shadow="xl" className="border border-slate-700">
                        <Stack gap="xl" align="center">
                            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-4xl shadow-lg">
                                👋
                            </div>

                            <div className="text-center space-y-3">
                                <Title order={1} size="h2">
                                    Welcome to Dyocense, {user?.name?.split(' ')[0] || 'there'}!
                                </Title>
                                <Text size="lg" c="dimmed" maw={600} mx="auto">
                                    Your AI-powered business coach that helps you make smarter decisions, track what matters,
                                    and achieve your goals faster.
                                </Text>
                            </div>

                            <Grid gutter="md" w="100%" mt="md">
                                <Grid.Col span={{ base: 12, sm: 4 }}>
                                    <Card padding="lg" radius="md" className="h-full border border-slate-700 bg-slate-800/50">
                                        <Stack gap="sm" align="center">
                                            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-indigo-500/10 text-2xl">
                                                <IconChartBar size={28} className="text-indigo-400" />
                                            </div>
                                            <Text fw={600} size="lg" ta="center">Track Health</Text>
                                            <Text size="sm" c="dimmed" ta="center">
                                                Monitor key metrics across revenue, cash flow, operations, and customer satisfaction
                                            </Text>
                                        </Stack>
                                    </Card>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, sm: 4 }}>
                                    <Card padding="lg" radius="md" className="h-full border border-slate-700 bg-slate-800/50">
                                        <Stack gap="sm" align="center">
                                            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-violet-500/10 text-2xl">
                                                <IconTarget size={28} className="text-violet-400" />
                                            </div>
                                            <Text fw={600} size="lg" ta="center">Set Goals</Text>
                                            <Text size="sm" c="dimmed" ta="center">
                                                Define clear objectives and get AI-generated action plans to achieve them
                                            </Text>
                                        </Stack>
                                    </Card>
                                </Grid.Col>
                                <Grid.Col span={{ base: 12, sm: 4 }}>
                                    <Card padding="lg" radius="md" className="h-full border border-slate-700 bg-slate-800/50">
                                        <Stack gap="sm" align="center">
                                            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-pink-500/10 text-2xl">
                                                <IconSparkles size={28} className="text-pink-400" />
                                            </div>
                                            <Text fw={600} size="lg" ta="center">Get Coached</Text>
                                            <Text size="sm" c="dimmed" ta="center">
                                                Ask questions, get insights, and receive personalized guidance 24/7
                                            </Text>
                                        </Stack>
                                    </Card>
                                </Grid.Col>
                            </Grid>

                            <Button
                                size="lg"
                                variant="gradient"
                                gradient={{ from: 'indigo', to: 'violet', deg: 90 }}
                                rightSection={<IconRocket size={20} />}
                                onClick={() => setStep('preview-value')}
                                fullWidth
                                maw={400}
                                mt="md"
                            >
                                See what you'll get
                            </Button>
                        </Stack>
                    </Paper>
                )}

                {/* Step 2: Preview Value - Show what they'll get with data */}
                {step === 'preview-value' && (
                    <Paper p="xl" radius="lg" shadow="xl" className="border border-slate-700">
                        <Stack gap="xl">
                            <div className="text-center space-y-3">
                                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-4xl shadow-lg mx-auto">
                                    📊
                                </div>
                                <Title order={2}>You'll get your Business Health Score</Title>
                                <Text size="lg" c="dimmed" maw={700} mx="auto">
                                    Once you connect your business data, you'll see a live health score based on these key areas:
                                </Text>
                            </div>

                            {/* Preview of health categories */}
                            <Grid gutter="md">
                                {healthCategories.map((category) => (
                                    <Grid.Col key={category.label} span={{ base: 12, sm: 6, md: 4 }}>
                                        <Paper p="md" radius="md" className="border border-slate-700 bg-slate-800/30">
                                            <Group gap="sm">
                                                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-slate-700/50 text-xl">
                                                    {category.icon}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <Text fw={600} size="sm">{category.label}</Text>
                                                    <Text size="xs" c="dimmed" lineClamp={2}>{category.description}</Text>
                                                </div>
                                            </Group>
                                        </Paper>
                                    </Grid.Col>
                                ))}
                            </Grid>

                            {/* Visual preview */}
                            <Paper p="xl" radius="md" className="border-2 border-dashed border-slate-600 bg-slate-800/20">
                                <Stack gap="lg" align="center">
                                    <div className="relative">
                                        <svg width="200" height="200" className="transform -rotate-90">
                                            <circle
                                                cx="100"
                                                cy="100"
                                                r="80"
                                                stroke="#334155"
                                                strokeWidth="16"
                                                fill="none"
                                            />
                                            <circle
                                                cx="100"
                                                cy="100"
                                                r="80"
                                                stroke="url(#gradient)"
                                                strokeWidth="16"
                                                fill="none"
                                                strokeDasharray="502"
                                                strokeDashoffset="125"
                                                strokeLinecap="round"
                                            />
                                            <defs>
                                                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" stopColor="#6366f1" />
                                                    <stop offset="100%" stopColor="#8b5cf6" />
                                                </linearGradient>
                                            </defs>
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <Text size="3rem" fw={700} lh={1} c="gray.5">?</Text>
                                            <Text size="xs" c="dimmed">/100</Text>
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <Badge size="lg" variant="light" color="gray">
                                            Connect data to unlock
                                        </Badge>
                                        <Text size="sm" c="dimmed" mt="xs">
                                            Your score updates in real-time as your business changes
                                        </Text>
                                    </div>
                                </Stack>
                            </Paper>

                            <Button
                                size="lg"
                                variant="gradient"
                                gradient={{ from: 'indigo', to: 'violet', deg: 90 }}
                                onClick={() => setStep('next-steps')}
                                fullWidth
                                maw={400}
                                mx="auto"
                            >
                                Continue
                            </Button>
                        </Stack>
                    </Paper>
                )}

                {/* Step 3: Next Steps - Choose how to get started */}
                {step === 'next-steps' && (
                    <Paper p="xl" radius="lg" shadow="xl" className="border border-slate-700">
                        <Stack gap="xl">
                            <div className="text-center space-y-3">
                                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-4xl shadow-lg mx-auto">
                                    🚀
                                </div>
                                <Title order={2}>Ready to get started?</Title>
                                <Text size="lg" c="dimmed" maw={600} mx="auto">
                                    Choose how you'd like to begin your journey
                                </Text>
                            </div>

                            <Grid gutter="lg">
                                <Grid.Col span={{ base: 12, sm: 6 }}>
                                    <Card
                                        padding="xl"
                                        radius="md"
                                        className="h-full border-2 border-indigo-500 bg-indigo-500/10 cursor-pointer hover:bg-indigo-500/20 transition-all"
                                        onClick={handleConnectData}
                                    >
                                        <Stack gap="md" align="center" justify="center" style={{ minHeight: 250 }}>
                                            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-500 text-3xl shadow-lg">
                                                <IconPlugConnected size={32} className="text-white" />
                                            </div>
                                            <div className="text-center">
                                                <Text fw={700} size="xl" mb="xs">Connect Your Data</Text>
                                                <Badge variant="light" color="indigo" size="sm" mb="md">Recommended</Badge>
                                                <Text size="sm" c="dimmed">
                                                    Link your ERP, POS, or upload CSV files to get instant insights and your business health score
                                                </Text>
                                            </div>
                                            <Button
                                                variant="filled"
                                                color="indigo"
                                                size="md"
                                                rightSection={<IconPlugConnected size={18} />}
                                                fullWidth
                                            >
                                                Connect data sources
                                            </Button>
                                        </Stack>
                                    </Card>
                                </Grid.Col>

                                <Grid.Col span={{ base: 12, sm: 6 }}>
                                    <Card
                                        padding="xl"
                                        radius="md"
                                        className="h-full border border-slate-600 bg-slate-800/50 cursor-pointer hover:border-slate-500 transition-all"
                                        onClick={handleGoToDashboard}
                                    >
                                        <Stack gap="md" align="center" justify="center" style={{ minHeight: 250 }}>
                                            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-700 text-3xl">
                                                <IconCheckbox size={32} className="text-slate-300" />
                                            </div>
                                            <div className="text-center">
                                                <Text fw={700} size="xl" mb="xs">Explore First</Text>
                                                <Text size="sm" c="dimmed">
                                                    Take a look around, chat with your AI coach, and connect your data later
                                                </Text>
                                            </div>
                                            <Button
                                                variant="light"
                                                color="gray"
                                                size="md"
                                                fullWidth
                                            >
                                                Go to dashboard
                                            </Button>
                                        </Stack>
                                    </Card>
                                </Grid.Col>
                            </Grid>

                            <Text size="xs" c="dimmed" ta="center" mt="md">
                                💡 You can always connect your data sources later from Settings
                            </Text>
                        </Stack>
                    </Paper>
                )}
            </div>
        </div>
    )
}
