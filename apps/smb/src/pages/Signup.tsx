import { Alert, Badge, Button, Paper, Radio, Stack, Text, TextInput, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { OAuthButtons } from '../components/OAuthButtons'
import { post } from '../lib/api'

const plans = [
    {
        id: 'pilot',
        name: 'Pilot',
        price: 'Free',
        cadence: '14-day guided trial',
        description: 'Perfect to get started and see value',
        features: ['Full platform access', 'Connect your real data', 'Live onboarding session'],
    },
    {
        id: 'run',
        name: 'Run',
        price: '$79',
        cadence: 'per seat / month',
        description: 'For teams ready to build momentum',
        features: ['Unlimited plans & evidence', '3 agents included', 'Email + chat support'],
        highlight: true,
    },
    {
        id: 'scale',
        name: 'Scale',
        price: 'Custom',
        cadence: 'annual',
        description: 'Enterprise-grade for growing businesses',
        features: ['Dedicated success pod', 'Private data boundary', 'Outcome-based pricing'],
    },
]

type SignupForm = {
    fullName: string
    businessName: string
    email: string
    phoneNumber: string
}

export default function Signup() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const toolHint = searchParams.get('tool')
    const planParam = searchParams.get('plan') || 'pilot'
    const next = searchParams.get('next') ?? '/home'

    const [selectedPlan, setSelectedPlan] = useState(planParam)

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<SignupForm>({
        defaultValues: {
            fullName: '',
            businessName: '',
            email: '',
            phoneNumber: '',
        },
    })

    const mutation = useMutation({
        mutationFn: async (values: SignupForm) => {
            const response = await post<{ token?: string }>('/v1/auth/signup', {
                email: values.email,
                name: values.fullName,
                business_name: values.businessName,
                phone: values.phoneNumber,
                plan: selectedPlan,
            })

            if (!response?.token) {
                throw new Error('No verification token received. Please try again.')
            }

            return response.token
        },
        onSuccess: (token) => {
            const params = new URLSearchParams({ token, next, plan: selectedPlan })
            if (toolHint) params.set('tool', toolHint)
            navigate(`/verify?${params.toString()}`)
        },
        onError: (error: any) => {
            // Log error for debugging
            console.error('Signup error:', error)
        },
    })

    const onSubmit = (values: SignupForm) => mutation.mutate(values)

    const currentPlan = plans.find(p => p.id === selectedPlan) || plans[0]
    const isScalePlan = selectedPlan === 'scale'

    // Check if the error is due to email already registered (409 Conflict)
    const isEmailAlreadyRegistered = mutation.error &&
        (mutation.error as any)?.message?.includes('already registered') ||
        (mutation.error as any)?.status === 409

    return (
        <div className="page-shell">
            <div className="grid gap-8 md:grid-cols-[0.9fr_1.1fr]">
                <div className="glass-panel space-y-6">
                    <div className="space-y-3">
                        <p className="text-xs font-bold uppercase tracking-[0.4em] text-brand-600">Start your journey</p>
                        <Title order={2} className="text-gray-900">
                            {isScalePlan ? 'Talk to Our Team' : 'Get Started in 60 Seconds'}
                        </Title>
                        <Text className="text-gray-700">
                            {isScalePlan
                                ? 'Share your details and we\'ll schedule a personalized demo with our team.'
                                : 'Join thousands of business owners using AI-powered insights to grow smarter.'
                            }
                        </Text>
                    </div>

                    {/* Selected Plan Summary */}
                    <Paper radius="xl" p="lg" className="border border-brand-200 bg-gradient-to-br from-brand-50 to-violet-50" withBorder={false}>
                        <div className="flex items-start justify-between mb-3">
                            <div>
                                <Text size="xs" fw={600} tt="uppercase" className="text-brand-700" style={{ letterSpacing: '0.25em' }}>
                                    Your plan
                                </Text>
                                <Text size="xl" fw={700} className="text-gray-900" mt={4}>{currentPlan.name}</Text>
                                <Text size="sm" className="text-gray-600">
                                    {currentPlan.price} {currentPlan.price !== 'Free' && currentPlan.price !== 'Custom' && <span className="text-xs">/ {currentPlan.cadence}</span>}
                                </Text>
                            </div>
                            <Button
                                variant="subtle"
                                size="compact-xs"
                                className="text-brand-600 hover:text-brand-700"
                                onClick={() => window.scrollTo({ top: document.getElementById('plan-selection')?.offsetTop, behavior: 'smooth' })}
                            >
                                Change
                            </Button>
                        </div>
                        <Stack gap="xs" mt="sm">
                            {currentPlan.features.map((feature, idx) => (
                                <Text key={idx} size="sm" className="text-gray-700">✓ {feature}</Text>
                            ))}
                        </Stack>
                    </Paper>

                    {!isScalePlan && (
                        <Badge size="lg" radius="sm" color="brand" variant="light" className="w-fit">
                            {currentPlan.id === 'pilot' ? 'Free assessment • No credit card' : 'Start immediately after verification'}
                        </Badge>
                    )}
                </div>

                <div className="glass-panel--light space-y-6">
                    {/* Plan Selection */}
                    <div id="plan-selection">
                        <Stack gap="xs" mb="md">
                            <Text className="text-xs font-bold uppercase tracking-[0.4em] text-brand-600">Step 1 · Choose your plan</Text>
                            <Text className="text-gray-700">Select the plan that best fits your business needs.</Text>
                        </Stack>

                        <Radio.Group value={selectedPlan} onChange={setSelectedPlan}>
                            <Stack gap="sm">
                                {plans.map((plan) => (
                                    <Paper
                                        key={plan.id}
                                        p="md"
                                        radius="md"
                                        withBorder
                                        className={`cursor-pointer transition-all hover:shadow-md ${selectedPlan === plan.id ? 'ring-2 ring-brand-500 bg-brand-50/50' : ''}`}
                                        onClick={() => setSelectedPlan(plan.id)}
                                    >
                                        <Radio
                                            value={plan.id}
                                            label={
                                                <div className="ml-2">
                                                    <div className="flex items-baseline gap-2">
                                                        <Text fw={600} size="lg" className="text-gray-900">{plan.name}</Text>
                                                        {plan.highlight && (
                                                            <Badge size="xs" color="brand" variant="filled">Most Popular</Badge>
                                                        )}
                                                    </div>
                                                    <Text size="sm" className="text-gray-600" mt={2}>{plan.description}</Text>
                                                    <Text fw={700} size="md" className="text-gray-900" mt={6}>
                                                        {plan.price}
                                                        {plan.price !== 'Free' && plan.price !== 'Custom' && (
                                                            <Text span size="xs" fw={400} className="text-gray-600"> / {plan.cadence}</Text>
                                                        )}
                                                    </Text>
                                                </div>
                                            }
                                        />
                                    </Paper>
                                ))}
                            </Stack>
                        </Radio.Group>
                    </div>

                    {/* User Information Form */}
                    <div>
                        <Stack gap="xs" mb="md">
                            <Text className="text-xs font-bold uppercase tracking-[0.4em] text-brand-600">Step 2 · Your information</Text>
                            <Text className="text-gray-700">
                                {isScalePlan
                                    ? 'We\'ll reach out within 24 hours to schedule your demo.'
                                    : 'Just a few details to get you started.'
                                }
                            </Text>
                        </Stack>

                        {mutation.isError && (
                            isEmailAlreadyRegistered ? (
                                <Alert color="blue" title="Account already exists" mb="md">
                                    This email is already registered. <Link to="/login" className="font-semibold underline">Sign in instead</Link> to access your account.
                                </Alert>
                            ) : (
                                <Alert color="red" title="Signup failed" mb="md">
                                    We couldn't create your account. Please try again, or <Link to="/contact" className="underline">contact support</Link> if the problem persists.
                                </Alert>
                            )
                        )}

                        {/* OAuth Buttons - available for all plans */}
                        <OAuthButtons mode="signup" />

                        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                            <Controller
                                control={control}
                                name="fullName"
                                rules={{ required: 'Your name is required' }}
                                render={({ field }) => (
                                    <TextInput label="Your name" placeholder="Alex Kim" error={errors.fullName?.message} {...field} />
                                )}
                            />
                            <Controller
                                control={control}
                                name="businessName"
                                rules={{ required: 'Business name is required' }}
                                render={({ field }) => (
                                    <TextInput label="Business name" placeholder="Northwind Cafe" error={errors.businessName?.message} {...field} />
                                )}
                            />
                            <Controller
                                control={control}
                                name="email"
                                rules={{ required: 'Email is required', pattern: { value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i, message: 'Invalid email address' } }}
                                render={({ field }) => (
                                    <TextInput
                                        label="Email address"
                                        description="You can use any email — personal or business"
                                        placeholder="you@yourbusiness.com"
                                        autoComplete="email"
                                        error={errors.email?.message}
                                        {...field}
                                    />
                                )}
                            />
                            <Controller
                                control={control}
                                name="phoneNumber"
                                rules={{ required: false }}
                                render={({ field }) => (
                                    <TextInput label="Phone number (optional)" placeholder="+1 (555) 123-4567" autoComplete="tel" {...field} />
                                )}
                            />

                            <Button type="submit" fullWidth radius="xl" size="lg" loading={mutation.isPending}>
                                {mutation.isPending
                                    ? (isScalePlan ? 'Submitting...' : 'Creating your account…')
                                    : (isScalePlan ? 'Request demo' : `Start with ${currentPlan.name} plan`)
                                }
                            </Button>

                            <div className="text-center space-y-2">
                                <Text size="xs" className="text-gray-600">
                                    Already have an account? <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700 hover:underline">Sign in</Link>
                                </Text>
                                <Text size="xs" className="text-gray-500">
                                    By signing up, you agree to our <Link to="/terms" className="text-gray-600 hover:text-gray-900 underline">Terms</Link> and <Link to="/privacy" className="text-gray-600 hover:text-gray-900 underline">Privacy Policy</Link>
                                </Text>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    )
}
