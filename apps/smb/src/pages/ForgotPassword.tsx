import { Alert, Button, PasswordInput, Paper, Stack, Text, TextInput, Title } from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { requestPasswordReset, resetPassword } from '../lib/api'

type RequestForm = {
    email: string
}

type ResetForm = {
    password: string
    confirm: string
}

export default function ForgotPassword() {
    const [searchParams] = useSearchParams()
    const token = searchParams.get('token')
    const [submitted, setSubmitted] = useState(false)
    const navigate = useNavigate()

    const requestMutation = useMutation({
        mutationFn: (values: RequestForm) => requestPasswordReset(values.email),
        onSuccess: () => setSubmitted(true),
    })

    const resetMutation = useMutation({
        mutationFn: (values: ResetForm) => {
            return resetPassword(token || '', values.password)
        },
    })

    const { control, handleSubmit, formState: { errors }, setError } = useForm<RequestForm & ResetForm>({
        defaultValues: {
            email: '',
            password: '',
            confirm: '',
        },
    })

    const handleRequest = (values: RequestForm) => {
        requestMutation.mutate(values)
    }

    const handleReset = (values: ResetForm) => {
        if (!token) {
            setError('password', { type: 'manual', message: 'Invalid reset link' })
            return
        }
        if (values.password !== values.confirm) {
            setError('confirm', { type: 'manual', message: 'Passwords must match' })
            return
        }
        resetMutation.mutate(values)
    }

    useEffect(() => {
        if (resetMutation.isSuccess) {
            const timer = setTimeout(() => {
                navigate('/login')
            }, 2500)
            return () => clearTimeout(timer)
        }
    }, [navigate, resetMutation.isSuccess])

    const resetErrorMessage = resetMutation.error ? ((resetMutation.error as any)?.body?.detail || (resetMutation.error as Error).message) : undefined

    return (
        <div className="page-shell">
            <div className="mx-auto max-w-md">
                <div className="glass-panel space-y-6">
                    <div className="text-center space-y-2">
                        <p className="text-xs font-bold uppercase tracking-[0.4em] text-brand-600">Account security</p>
                        <Title order={2} className="text-gray-900">
                            {token ? 'Reset your password' : 'Forgot your password?'}
                        </Title>
                        <Text className="text-gray-700">
                            {token
                                ? 'Enter a new password to secure your account.'
                                : 'Enter your email and we will send a secure link to reset your password.'}
                        </Text>
                    </div>

                    {token ? (
                        <>
                            {resetMutation.isError && (
                                <Alert color="red" title="Reset failed">
                                    {resetErrorMessage || 'Something went wrong. Try again.'}
                                </Alert>
                            )}

                            {resetMutation.isSuccess && (
                                <Alert color="green" title="Success">
                                    Your password has been updated. <Link to="/login" className="font-semibold underline">Sign in</Link>
                                </Alert>
                            )}

                            <form className="space-y-4" onSubmit={handleSubmit(handleReset)}>
                                <Controller
                                    control={control}
                                    name="password"
                                    rules={{ required: 'Password is required' }}
                                    render={({ field }) => (
                                        <PasswordInput
                                            label="New password"
                                            placeholder="••••••••"
                                            error={errors.password?.message}
                                            {...field}
                                        />
                                    )}
                                />
                                <Controller
                                    control={control}
                                    name="confirm"
                                    rules={{ required: 'Confirm your password' }}
                                    render={({ field }) => (
                                        <PasswordInput
                                            label="Confirm password"
                                            placeholder="••••••••"
                                            error={errors.confirm?.message}
                                            {...field}
                                        />
                                    )}
                                />
                                <Button type="submit" fullWidth radius="xl" size="lg" loading={resetMutation.isPending}>
                                    {resetMutation.isPending ? 'Updating...' : 'Update my password'}
                                </Button>
                            </form>
                        </>
                    ) : (
                        <>
                            {requestMutation.isSuccess && submitted ? (
                                <Alert color="green" title="Email sent">
                                    Check your inbox for a password reset link.
                                </Alert>
                            ) : (
                                <form className="space-y-4" onSubmit={handleSubmit(handleRequest)}>
                                    <Controller
                                        control={control}
                                        name="email"
                                        rules={{
                                            required: 'Email is required',
                                            pattern: {
                                                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                                message: 'Invalid email address',
                                            },
                                        }}
                                        render={({ field }) => (
                                            <TextInput
                                                label="Email address"
                                                placeholder="you@yourbusiness.com"
                                                autoComplete="email"
                                                error={errors.email?.message}
                                                {...field}
                                            />
                                        )}
                                    />
                                    <Button type="submit" fullWidth radius="xl" size="lg" loading={requestMutation.isPending}>
                                        {requestMutation.isPending ? 'Sending...' : 'Send reset link'}
                                    </Button>
                                </form>
                            )}
                        </>
                    )}

                    <Paper p="md" radius="md" className="border border-gray-200 bg-gray-50">
                        <Text size="xs" c="dimmed" className="text-center">
                            Remembered your password? <Link to="/login" className="font-semibold text-brand-600 hover:underline">Sign in</Link>.
                        </Text>
                    </Paper>
                </div>
            </div>
        </div>
    )
}
