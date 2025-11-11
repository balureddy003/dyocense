import { Button, Stack, Text } from '@mantine/core'
import { IconBrandGoogle } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { get } from '../lib/api'

type OAuthProvider = 'google' | 'microsoft' | 'apple'

interface OAuthProvidersResponse {
    enabled_providers: OAuthProvider[]
    providers: Record<string, {
        name: string
        description: string
        icon: string
        color: string
    }>
}

interface OAuthButtonsProps {
    mode: 'signup' | 'login'
}

export function OAuthButtons({ mode }: OAuthButtonsProps) {
    const [loading, setLoading] = useState<OAuthProvider | null>(null)

    // Fetch available OAuth providers
    const { data: providers, isLoading } = useQuery({
        queryKey: ['oauth-providers'],
        queryFn: async () => {
            try {
                const data = await get<OAuthProvidersResponse>('/v1/auth/providers')
                return data
            } catch {
                // If OAuth is not configured, return empty
                return { enabled_providers: [], providers: {} }
            }
        },
    })

    const handleOAuthLogin = async (provider: OAuthProvider) => {
        setLoading(provider)
        try {
            // Get authorization URL from backend
            const response = await get<{ authorization_url: string; state: string }>(
                `/v1/auth/${provider}/authorize`
            )

            // Redirect to OAuth provider
            window.location.href = response.authorization_url
        } catch (error) {
            console.error(`OAuth ${provider} login failed:`, error)
            setLoading(null)
        }
    }

    if (isLoading || !providers || providers.enabled_providers.length === 0) {
        return null
    }

    const getProviderIcon = (provider: OAuthProvider) => {
        switch (provider) {
            case 'google':
                return <IconBrandGoogle size={20} />
            case 'microsoft':
                // Microsoft icon - using a simple SVG
                return (
                    <svg width="20" height="20" viewBox="0 0 23 23" fill="none">
                        <rect width="11" height="11" fill="#F25022" />
                        <rect x="12" width="11" height="11" fill="#7FBA00" />
                        <rect y="12" width="11" height="11" fill="#00A4EF" />
                        <rect x="12" y="12" width="11" height="11" fill="#FFB900" />
                    </svg>
                )
            default:
                return null
        }
    }

    return (
        <Stack gap="sm">
            {providers.enabled_providers.map((provider: OAuthProvider) => {
                const info = providers.providers[provider]
                const isLoading = loading === provider

                return (
                    <Button
                        key={provider}
                        variant="default"
                        size="md"
                        fullWidth
                        leftSection={getProviderIcon(provider)}
                        loading={isLoading}
                        onClick={() => handleOAuthLogin(provider)}
                        styles={{
                            root: {
                                border: '1px solid #e5e7eb',
                                backgroundColor: 'white',
                                '&:hover': {
                                    backgroundColor: '#f9fafb',
                                },
                            },
                        }}
                    >
                        {mode === 'signup' ? 'Sign up' : 'Sign in'} with {info.name}
                    </Button>
                )
            })}

            <Text size="xs" c="dimmed" className="text-center mt-1">
                Works with personal or business {providers.enabled_providers.length > 1 ? 'accounts' : 'account'}
            </Text>

            <div className="relative my-2">
                <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-2 text-gray-500">Or use any email</span>
                </div>
            </div>
        </Stack>
    )
}