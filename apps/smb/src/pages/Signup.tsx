import { Alert, Badge, Button, Paper, SegmentedControl, Stack, Text, TextInput, Textarea, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { tryPost } from '../lib/api'

const goals = [
    { label: 'Plan launch', value: 'launch' },
    { label: 'Improve ops', value: 'ops' },
    { label: 'Automate reporting', value: 'reporting' },
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
                        <p className="eyebrow text-brand-200">Start your pilot</p>
                        <Title order={2} c="white">
                            Create your Dyocense workspace
                        </Title>
                        <Text c="gray.2">Use any email you check daily—we’ll send a one-click magic link.</Text>
                    </div>
                    <Paper radius="xl" p="lg" className="bg-white/10 backdrop-blur" withBorder={false}>
                        <Text size="xs" fw={600} tt="uppercase" c="gray.2" style={{ letterSpacing: '0.25em' }}>
                            See the copilot in action
                        </Text>
                        <Stack gap="xs" mt="sm" textWrap="pretty" c="gray.1">
                            <Text size="sm">“Draft a launch plan for our spring promo.” → Planner cards appear instantly.</Text>
                            <Text size="sm">“Email the staff about the schedule change.” → Agent triggers a workflow.</Text>
                            <Text size="sm">“Explain today’s forecast to the owner.” → Evidence summary ready to send.</Text>
                        </Stack>
                    </Paper>
                    <Badge size="lg" radius="sm" color="brand" variant="light" className="w-fit">
                        Pilot seats available
                    </Badge>
                </div>

                <div className="glass-panel--light space-y-6">
                    <Stack gap="xs">
                        <Text className="eyebrow text-brand-600">Step 1 · Invite yourself</Text>
                        <Text c="neutral.600">Tell us about your business so we can preload the right template.</Text>
                    </Stack>
                    {mutation.isError && <Alert color="red">We couldn’t reach signup. Using a dev token fallback.</Alert>}
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
                                    <Text size="sm" fw={600} c="neutral.600">
                                        What brings you here?
                                    </Text>
                                    <SegmentedControl fullWidth data={goals} {...field} />
                                </div>
                            )}
                        />
                        <Controller
                            control={control}
                            name="useCase"
                            render={({ field }) => (
                                <Textarea label="Anything else?" placeholder="e.g. Need help syncing Shopify promos" minRows={3} {...field} />
                            )}
                        />
                        <Button type="submit" fullWidth radius="xl" loading={mutation.isPending}>
                            {mutation.isPending ? 'Sending link…' : 'Send me a magic link'}
                        </Button>
                        <Text size="xs" ta="center" c="neutral.600">
                            Already a customer? <Link to={`/verify?next=${encodeURIComponent(next)}`}>Get a new link</Link>
                        </Text>
                    </form>
                </div>
            </div>
        </div>
    )
}
