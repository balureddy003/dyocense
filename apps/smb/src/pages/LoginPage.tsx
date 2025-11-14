import { Alert, Button, Paper, PasswordInput, Stack, TextInput, Title } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authLogin, authMe } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [tenantId, setTenantId] = useState('8278e5e6-574b-429f-9f65-2c25fa776ee9') // Default test tenant
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const { setAuth } = useAuthStore()
    const navigate = useNavigate()

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setLoading(true)

        try {
            // Login and get token
            const { access_token } = await authLogin(email, password, tenantId)

            // Fetch user info
            const user = await authMe(access_token)

            // Store in auth store
            setAuth(access_token, user)

            // Navigate to dashboard
            navigate('/dashboard')
        } catch (err: any) {
            setError(err.body?.detail || err.message || 'Login failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8f9fa' }}>
            <Paper shadow="md" p="xl" radius="md" style={{ width: 400 }}>
                <Title order={2} mb="lg" ta="center">
                    Dyocense
                </Title>

                <form onSubmit={handleLogin}>
                    <Stack gap="md">
                        {error && (
                            <Alert icon={<IconAlertCircle size={16} />} color="red">
                                {error}
                            </Alert>
                        )}

                        <Alert color="blue" title="Test Credentials">
                            Email: admin@acme.com<br />
                            Password: password123
                        </Alert>

                        <TextInput
                            label="Email"
                            placeholder="you@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.currentTarget.value)}
                            required
                            type="email"
                        />

                        <PasswordInput
                            label="Password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.currentTarget.value)}
                            required
                        />

                        <Button type="submit" fullWidth loading={loading}>
                            Sign In
                        </Button>
                    </Stack>
                </form>
            </Paper>
        </div>
    )
}

export default LoginPage
