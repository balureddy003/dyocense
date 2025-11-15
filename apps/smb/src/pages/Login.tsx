import { Alert, Button, Paper, PasswordInput, SegmentedControl, Text, TextInput, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { OAuthButtons } from '../components/OAuthButtons'
import { post } from '../lib/api'
import { useAuthStore } from '../stores/auth'

type LoginForm = {
    email: string
    password: string
}

type PasswordLoginResponse = {
    token: string
    user_id: string
    tenant_id: string
    expires_in: number
}

export default function Login() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const next = searchParams.get('next') ?? '/home'
    const setAuth = useAuthStore((s) => s.setAuth)
    const [loginMode, setLoginMode] = useState<'magic' | 'password'>('magic')

    const {
        control,
        handleSubmit,
        setValue,
        formState: { errors },
    } = useForm<LoginForm>({
        defaultValues: {
            email: '',
            password: '',
        },
    })

    const mutation = useMutation({
        mutationFn: async (values: LoginForm) => {
            const response = await post<{ token?: string }>('/v1/auth/login', {
                email: values.email,
            })

            if (!response?.token) {
                throw new Error('No verification token received. Please try again.')
            }

            return response.token
        },
        onSuccess: (token: string) => {
            const params = new URLSearchParams({ token, next })
            navigate(`/verify?${params.toString()}`)
        },
    })

    const passwordLoginMutation = useMutation({
        mutationFn: async (values: { email: string; password: string }) => {
            return post<PasswordLoginResponse>('/v1/auth/login-password', values)
        },
        onSuccess: (data, variables) => {
            setAuth({
                apiToken: data.token,
                tenantId: data.tenant_id,
                user: {
                    user_id: data.user_id,
                    email: variables.email,
                    full_name: variables.email,
                    name: variables.email,
                },
            })
            navigate(next, { replace: true })
        },
    })

    useEffect(() => {
        mutation.reset()
        passwordLoginMutation.reset()
        setValue('password', '')
    }, [loginMode, mutation, passwordLoginMutation, setValue])

    const onSubmit = (values: LoginForm) => mutation.mutate(values)
    const handlePasswordLogin = handleSubmit((values: LoginForm) => {
        passwordLoginMutation.mutate({ email: values.email, password: values.password })
    })

    return (
        <div className="page-shell">
            <div className="mx-auto max-w-md">
                <div className="glass-panel--light space-y-6">
                    <div className="space-y-3 text-center">
                        <p className="text-xs font-bold uppercase tracking-[0.4em] text-brand-600">Welcome back</p>
                        <Title order={2} className="text-gray-900">
                            Sign in to Dyocense
                        </Title>
                        <Text className="text-gray-700">
                            {loginMode === 'magic'
                                ? "We'll send you a secure access link — no password needed."
                                : 'Use your password to unlock your workspace instantly.'}
                        </Text>
                    </div>

                    <div className="space-y-3">
                        <SegmentedControl
                            value={loginMode}
                            onChange={(value) => setLoginMode(value as 'magic' | 'password')}
                            data={[
                                { value: 'magic', label: 'Magic link' },
                                { value: 'password', label: 'Password' },
                            ]}
                            fullWidth
                        />
                        <Text size="xs" c="dimmed" className="text-center">
                            {loginMode === 'magic'
                                ? 'Quick magic link delivered to your inbox (no password required).'
                                : 'Sign in with your email and password (saved securely).'}
                        </Text>
                    </div>

                    {loginMode === 'magic' && mutation.isError && (
                        <Alert color="red" title="Login failed">
                            We couldn't find your account. Please check your email and try again, or <Link to="/signup" className="font-semibold underline">create a new account</Link>.
                        </Alert>
                    )}

                    {loginMode === 'magic' && mutation.isSuccess && (
                        <Alert color="green" title="Check your email! 📧">
                            We've sent you a secure login link. Click the link in your email to access your account instantly.
                        </Alert>
                    )}

                    {loginMode === 'password' && passwordLoginMutation.isError && (
                        <Alert color="red" title="Password login failed">
                            {passwordLoginMutation.error?.message ?? 'Incorrect email or password. Try again, or use the magic link.'}
                        </Alert>
                    )}

                    <form
                        className="space-y-5"
                        onSubmit={loginMode === 'magic' ? handleSubmit(onSubmit) : handlePasswordLogin}
                    >
                        <Controller
                            control={control}
                            name="email"
                            rules={{
                                required: 'Email is required',
                                pattern: {
                                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                    message: 'Invalid email address'
                                }
                            }}
                            render={({ field }) => (
                                <TextInput
                                    label="Email address"
                                    placeholder="you@yourbusiness.com"
                                    description={loginMode === 'magic' ? 'We’ll send a secure link to this email.' : 'Enter the email tied to your account'}
                                    autoComplete="email"
                                    size="md"
                                    error={errors.email?.message}
                                    {...field}
                                />
                            )}
                        />

                        {loginMode === 'password' && (
                            <Controller
                                control={control}
                                name="password"
                                rules={{ required: 'Password is required' }}
                                render={({ field }) => (
                                    <PasswordInput
                                        label="Password"
                                        placeholder="Create or use your existing password"
                                        autoComplete="current-password"
                                        size="md"
                                        error={errors.password?.message}
                                        {...field}
                                    />
                                )}
                            />
                        )}

                        <Button
                            type="submit"
                            fullWidth
                            radius="xl"
                            size="lg"
                            loading={loginMode === 'magic' ? mutation.isPending : passwordLoginMutation.isPending}
                        >
                            {loginMode === 'magic'
                                ? (mutation.isPending ? 'Sending...' : 'Continue →')
                                : (passwordLoginMutation.isPending ? 'Signing in...' : 'Sign in with password')}
                        </Button>

                        <div className="text-center space-y-2">
                            <Text size="xs" className="text-gray-600">
                                Don't have an account? <Link to="/signup" className="font-semibold text-brand-600 hover:text-brand-700 hover:underline">Sign up free</Link>
                            </Text>
                            <Text size="xs" className="text-gray-500">
                                ✨ No password needed • 🔒 Secure verification
                            </Text>
                            <Text size="xs" className="text-gray-500">
                                Forgot your password? <Link to="/forgot-password" className="font-semibold text-brand-600 hover:text-brand-700 hover:underline">Reset it here</Link>
                            </Text>
                        </div>
                    </form>

                    <OAuthButtons mode="login" />

                    {/* Trust indicators */}
                    <Paper p="md" radius="md" className="border border-gray-200 bg-gray-50">
                        <Text size="xs" fw={600} className="text-gray-700 mb-2">💡 How it works</Text>
                        <Text size="xs" className="text-gray-600">
                            {loginMode === 'magic'
                                ? "Enter your email and we'll send you a secure link. Click it to sign in instantly — no password to remember or type!"
                                : 'Use your password to unlock your business workspace. Need help? Use the magic link instead.'}
                        </Text>
                    </Paper>
                </div>
            </div>
        </div>
    )
}
