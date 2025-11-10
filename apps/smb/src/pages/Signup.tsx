import { Alert, Badge, Button, Paper, SegmentedControl, Stack, Text, TextInput, Textarea, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { tryPost } from '../lib/api'

const goals = [
    { label: '💰 Grow my revenue', value: 'revenue' },
    { label: '💵 Improve cash flow', value: 'cash_flow' },
    { label: '🎯 Win more customers', value: 'customers' },
    { label: '📊 Get better insights', value: 'insights' },
]

type SignupForm = {
    fullName: string
    businessName: string
    email: string
    goal: string
    useCase: string
}

export default function Signup() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const toolHint = searchParams.get('tool')
    const next = searchParams.get('next') ?? '/home'

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<SignupForm>({
        defaultValues: {
            fullName: '',
            businessName: '',
            email: '',
            goal: goals[0].value,
            useCase: '',
        },
    })

    const mutation = useMutation({
        mutationFn: async (values: SignupForm) => {
            const response = await tryPost<{ token?: string }>('/v1/auth/signup', {
                email: values.email,
                name: values.fullName,
                business_name: values.businessName,
                intent: toolHint ?? values.goal,
                use_case: values.useCase,
            })
            return response?.token ?? `dev-token-${Date.now()}`
        },
        onSuccess: (token) => {
            const params = new URLSearchParams({ token, next })
            if (toolHint) params.set('tool', toolHint)
            navigate(`/verify?${params.toString()}`)
        },
    })

    const onSubmit = (values: SignupForm) => mutation.mutate(values)

    return (
        <div className="page-shell">
            <div className="grid gap-8 md:grid-cols-[0.9fr_1.1fr]">
                <div className="glass-panel space-y-6">
                    <div className="space-y-3">
                        <p className="eyebrow text-brand-200">Start your journey</p>
                        <Title order={2} c="white">
                            Welcome! Let's Get to Know Your Business
                        </Title>
                        <Text c="gray.2">In 60 seconds, you'll have your business health score and personalized action plan.</Text>
                    </div>
                    <Paper radius="xl" p="lg" className="bg-white/10 backdrop-blur" withBorder={false}>
                        <Text size="xs" fw={600} tt="uppercase" c="gray.2" style={{ letterSpacing: '0.25em' }}>
                            What you'll get
                        </Text>
                        <Stack gap="xs" mt="sm" c="gray.1">
                            <Text size="sm">✓ Business health score in 30 seconds</Text>
                            <Text size="sm">✓ Personalized weekly action plan</Text>
                            <Text size="sm">✓ AI coach to guide you every step</Text>
                        </Stack>
                    </Paper>
                    <Badge size="lg" radius="sm" color="brand" variant="light" className="w-fit">
                        Free assessment • No credit card
                    </Badge>
                </div>

                <div className="glass-panel--light space-y-6">
                    <Stack gap="xs">
                        <Text className="eyebrow text-brand-600">Step 1 · Quick assessment</Text>
                        <Text c="gray.6">Tell us about your business so the coach can personalize your plan.</Text>
                    </Stack>
                    {mutation.isError && <Alert color="red">We couldn't reach signup. Using a dev token fallback.</Alert>}
                    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                        <Controller
                            control={control}
                            name="fullName"
                            rules={{ required: 'Your name is required' }}
                            render={({ field }) => (
                                <TextInput label="Name" placeholder="Alex Kim" error={errors.fullName?.message} {...field} />
                            )}
                        />
                        <Controller
                            control={control}
                            name="businessName"
                            rules={{ required: 'Business name is required' }}
                            render={({ field }) => (
                                <TextInput label="Business" placeholder="Northwind Cafe" error={errors.businessName?.message} {...field} />
                            )}
                        />
                        <Controller
                            control={control}
                            name="email"
                            rules={{ required: 'Email is required' }}
                            render={({ field }) => (
                                <TextInput label="Email" placeholder="owner@gmail.com" autoComplete="email" error={errors.email?.message} {...field} />
                            )}
                        />
                        <Controller
                            control={control}
                            name="goal"
                            render={({ field }) => (
                                <div className="space-y-2">
                                    <Text size="sm" fw={600} c="gray.6">
                                        What's your #1 priority right now?
                                    </Text>
                                    <SegmentedControl fullWidth data={goals} {...field} />
                                </div>
                            )}
                        />
                        <Controller
                            control={control}
                            name="useCase"
                            render={({ field }) => (
                                <Textarea label="Anything else we should know?" placeholder="e.g., I need help with inventory turnover" minRows={3} {...field} />
                            )}
                        />
                        <Button type="submit" fullWidth radius="xl" loading={mutation.isPending}>
                            {mutation.isPending ? 'Preparing your assessment…' : 'Start my free assessment'}
                        </Button>
                        <Text size="xs" ta="center" c="gray.6">
                            Already a customer? <Link to={`/verify?next=${encodeURIComponent(next)}`}>Get a new link</Link>
                        </Text>
                    </form>
                </div>
            </div>
        </div>
    )
}
