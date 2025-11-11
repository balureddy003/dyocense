import { Alert, Button, Paper, Text, TextInput, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { OAuthButtons } from '../components/OAuthButtons'
import { post } from '../lib/api'

type LoginForm = {
    email: string
}

export default function Login() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const next = searchParams.get('next') ?? '/home'

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginForm>({
        defaultValues: {
            email: '',
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

    const onSubmit = (values: LoginForm) => mutation.mutate(values)

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
                            We'll send you a secure access link — no password needed
                        </Text>
                    </div>

                    {mutation.isError && (
                        <Alert color="red" title="Login failed">
                            We couldn't find your account. Please check your email and try again, or <Link to="/signup" className="font-semibold underline">create a new account</Link>.
                        </Alert>
                    )}

                    {mutation.isSuccess && (
                        <Alert color="green" title="Check your email! 📧">
                            We've sent you a secure login link. Click the link in your email to access your account instantly.
                        </Alert>
                    )}

                    {/* OAuth Buttons */}
                    <OAuthButtons mode="login" />

                    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
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
                                    description="We'll send you a secure login link"
                                    autoComplete="email"
                                    size="md"
                                    error={errors.email?.message}
                                    {...field}
                                />
                            )}
                        />

                        <Button type="submit" fullWidth radius="xl" size="lg" loading={mutation.isPending}>
                            {mutation.isPending ? 'Sending...' : 'Continue →'}
                        </Button>

                        <div className="text-center space-y-2">
                            <Text size="xs" className="text-gray-600">
                                Don't have an account? <Link to="/signup" className="font-semibold text-brand-600 hover:text-brand-700 hover:underline">Sign up free</Link>
                            </Text>
                            <Text size="xs" className="text-gray-500">
                                ✨ No password needed • 🔒 Secure verification
                            </Text>
                        </div>
                    </form>

                    {/* Trust indicators */}
                    <Paper p="md" radius="md" className="border border-gray-200 bg-gray-50">
                        <Text size="xs" fw={600} className="text-gray-700 mb-2">💡 How it works</Text>
                        <Text size="xs" className="text-gray-600">
                            Enter your email and we'll send you a secure link. Click it to sign in instantly — no password to remember or type!
                        </Text>
                    </Paper>
                </div>
            </div>
        </div>
    )
}
