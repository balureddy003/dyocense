import {
    Badge,
    Button,
    Card,
    Container,
    Divider,
    Group,
    SegmentedControl,
    Select,
    Stack,
    Switch,
    Text,
    TextInput,
    Title
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
    IconBell,
    IconCheck,
    IconDeviceFloppy,
    IconLock,
    IconMail,
    IconMessageCircle,
    IconMoon,
    IconPalette,
    IconShield,
    IconUser,
    IconWorldWww
} from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { get, put } from '../lib/api'
import { useAuthStore } from '../stores/auth'

interface NotificationSettings {
    emailEnabled: boolean
    pushEnabled: boolean
    slackEnabled: boolean
    teamsEnabled: boolean
    inAppEnabled: boolean
    quietHoursEnabled: boolean
    quietHoursStart: string
    quietHoursEnd: string
    goalMilestones: boolean
    taskCompletions: boolean
    weeklyRecap: boolean
    nudges: boolean
    alerts: boolean
}

export default function Settings() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const queryClient = useQueryClient()

    const [activeTab, setActiveTab] = useState<string>('notifications')

    // Fetch settings from API
    const { data: settings } = useQuery({
        queryKey: ['settings', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/settings`, apiToken),
        enabled: !!tenantId && !!apiToken,
    })

    // Notification preferences
    const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
        emailEnabled: true,
        pushEnabled: false,
        slackEnabled: false,
        teamsEnabled: false,
        inAppEnabled: true,
        quietHoursEnabled: false,
        quietHoursStart: '22:00',
        quietHoursEnd: '08:00',
        goalMilestones: true,
        taskCompletions: true,
        weeklyRecap: true,
        nudges: true,
        alerts: true,
    })

    // Account settings
    const [name, setName] = useState(user?.name || 'Business Owner')
    const [email, setEmail] = useState(user?.email || 'owner@business.com')
    const [businessName, setBusinessName] = useState('My Business')
    const [timezone, setTimezone] = useState('America/Los_Angeles')

    // Appearance settings
    const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>('light')
    const [colorScheme, setColorScheme] = useState('blue')

    // Load settings from API when available
    useEffect(() => {
        if (settings) {
            // Update notification settings
            if (settings.notifications) {
                setNotificationSettings({
                    emailEnabled: settings.notifications.email_enabled ?? true,
                    pushEnabled: settings.notifications.push_enabled ?? false,
                    slackEnabled: settings.notifications.slack_enabled ?? false,
                    teamsEnabled: settings.notifications.teams_enabled ?? false,
                    inAppEnabled: settings.notifications.in_app_enabled ?? true,
                    quietHoursEnabled: settings.notifications.quiet_hours_enabled ?? false,
                    quietHoursStart: settings.notifications.quiet_hours_start ?? '22:00',
                    quietHoursEnd: settings.notifications.quiet_hours_end ?? '08:00',
                    goalMilestones: settings.notifications.goal_milestones ?? true,
                    taskCompletions: settings.notifications.task_completions ?? true,
                    weeklyRecap: settings.notifications.weekly_recap ?? true,
                    nudges: settings.notifications.nudges ?? true,
                    alerts: settings.notifications.alerts ?? true,
                })
            }

            // Update account settings
            if (settings.account) {
                setName(settings.account.name || user?.name || 'Business Owner')
                setEmail(settings.account.email || user?.email || 'owner@business.com')
                setBusinessName(settings.account.business_name || 'My Business')
                setTimezone(settings.account.timezone || 'America/Los_Angeles')
            }

            // Update appearance settings
            if (settings.appearance) {
                setTheme(settings.appearance.theme as 'light' | 'dark' | 'auto' || 'light')
                setColorScheme(settings.appearance.color_scheme || 'blue')
            }
        }
    }, [settings, user])

    // Mutation for notification settings
    const updateNotifications = useMutation({
        mutationFn: (data: any) =>
            put(`/v1/tenants/${tenantId}/settings/notifications`, {
                email_enabled: data.emailEnabled,
                push_enabled: data.pushEnabled,
                slack_enabled: data.slackEnabled,
                teams_enabled: data.teamsEnabled,
                in_app_enabled: data.inAppEnabled,
                quiet_hours_enabled: data.quietHoursEnabled,
                quiet_hours_start: data.quietHoursStart,
                quiet_hours_end: data.quietHoursEnd,
                goal_milestones: data.goalMilestones,
                task_completions: data.taskCompletions,
                weekly_recap: data.weeklyRecap,
                nudges: data.nudges,
                alerts: data.alerts,
            }, apiToken),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings', tenantId] })
            notifications.show({
                title: 'Preferences Saved',
                message: 'Your notification settings have been updated',
                color: 'teal',
                icon: <IconCheck size={18} />,
            })
        },
    })

    // Mutation for account settings
    const updateAccount = useMutation({
        mutationFn: (data: any) =>
            put(`/v1/tenants/${tenantId}/settings/account`, {
                name: data.name,
                email: data.email,
                business_name: data.businessName,
                timezone: data.timezone,
            }, apiToken),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings', tenantId] })
            notifications.show({
                title: 'Account Updated',
                message: 'Your account information has been saved',
                color: 'teal',
                icon: <IconCheck size={18} />,
            })
        },
    })

    // Mutation for appearance settings
    const updateAppearance = useMutation({
        mutationFn: (data: any) =>
            put(`/v1/tenants/${tenantId}/settings/appearance`, {
                theme: data.theme,
                color_scheme: data.colorScheme,
            }, apiToken),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings', tenantId] })
            notifications.show({
                title: 'Appearance Updated',
                message: 'Your appearance settings have been saved',
                color: 'teal',
                icon: <IconCheck size={18} />,
            })
        },
    })

    const handleSaveNotifications = () => {
        updateNotifications.mutate(notificationSettings)
    }

    const handleSaveAccount = () => {
        updateAccount.mutate({ name, email, businessName, timezone })
    }

    const handleSaveAppearance = () => {
        updateAppearance.mutate({ theme, colorScheme })
    }

    const handleTestNotification = (channel: string) => {
        notifications.show({
            title: `Test ${channel} Notification`,
            message: 'This is how notifications will appear',
            color: 'blue',
        })
    }

    return (
        <Container size="lg" className="py-6">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        Account
                    </Text>
                    <Title order={1} size="h2" c="gray.9" mt={4}>
                        Settings
                    </Title>
                    <Text size="sm" c="gray.6" mt={4}>
                        Manage your account, notifications, and preferences
                    </Text>
                </div>

                {/* Tab Navigation */}
                <SegmentedControl
                    value={activeTab}
                    onChange={setActiveTab}
                    data={[
                        { label: 'Notifications', value: 'notifications' },
                        { label: 'Account', value: 'account' },
                        { label: 'Appearance', value: 'appearance' },
                        { label: 'Security', value: 'security' },
                    ]}
                    size="md"
                />

                {/* Notifications Tab */}
                {activeTab === 'notifications' && (
                    <Stack gap="lg">
                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconBell size={20} color="#0ea5e9" />
                                    <Text fw={600} size="sm">
                                        Notification Channels
                                    </Text>
                                </Group>

                                <Text size="sm" c="dimmed">
                                    Choose how you want to receive updates from your Business Coach
                                </Text>

                                <Stack gap="sm">
                                    <Group justify="space-between">
                                        <div>
                                            <Group gap="xs">
                                                <IconMail size={18} />
                                                <Text size="sm" fw={500}>
                                                    Email Notifications
                                                </Text>
                                            </Group>
                                            <Text size="xs" c="dimmed">
                                                Daily summaries and milestone celebrations
                                            </Text>
                                        </div>
                                        <Group gap="sm">
                                            <Switch
                                                checked={notificationSettings.emailEnabled}
                                                onChange={(e) =>
                                                    setNotificationSettings({
                                                        ...notificationSettings,
                                                        emailEnabled: e.currentTarget.checked,
                                                    })
                                                }
                                            />
                                            {notificationSettings.emailEnabled && (
                                                <Button
                                                    size="xs"
                                                    variant="light"
                                                    onClick={() => handleTestNotification('Email')}
                                                >
                                                    Test
                                                </Button>
                                            )}
                                        </Group>
                                    </Group>

                                    <Divider />

                                    <Group justify="space-between">
                                        <div>
                                            <Group gap="xs">
                                                <IconWorldWww size={18} />
                                                <Text size="sm" fw={500}>
                                                    Push Notifications
                                                </Text>
                                                <Badge size="xs" variant="light" color="blue">
                                                    Web
                                                </Badge>
                                            </Group>
                                            <Text size="xs" c="dimmed">
                                                Browser notifications for important updates
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.pushEnabled}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    pushEnabled: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Divider />

                                    <Group justify="space-between">
                                        <div>
                                            <Group gap="xs">
                                                <IconMessageCircle size={18} />
                                                <Text size="sm" fw={500}>
                                                    Slack
                                                </Text>
                                                <Badge size="xs" variant="light" color="violet">
                                                    Pro
                                                </Badge>
                                            </Group>
                                            <Text size="xs" c="dimmed">
                                                Send updates to your Slack workspace
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.slackEnabled}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    slackEnabled: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Divider />

                                    <Group justify="space-between">
                                        <div>
                                            <Group gap="xs">
                                                <IconMessageCircle size={18} />
                                                <Text size="sm" fw={500}>
                                                    Microsoft Teams
                                                </Text>
                                                <Badge size="xs" variant="light" color="violet">
                                                    Pro
                                                </Badge>
                                            </Group>
                                            <Text size="xs" c="dimmed">
                                                Send updates to your Teams channel
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.teamsEnabled}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    teamsEnabled: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>
                                </Stack>
                            </Stack>
                        </Card>

                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconMoon size={20} color="#0ea5e9" />
                                    <Text fw={600} size="sm">
                                        Quiet Hours
                                    </Text>
                                </Group>

                                <Text size="sm" c="dimmed">
                                    Pause non-urgent notifications during these hours
                                </Text>

                                <Group justify="space-between">
                                    <Text size="sm" fw={500}>
                                        Enable Quiet Hours
                                    </Text>
                                    <Switch
                                        checked={notificationSettings.quietHoursEnabled}
                                        onChange={(e) =>
                                            setNotificationSettings({
                                                ...notificationSettings,
                                                quietHoursEnabled: e.currentTarget.checked,
                                            })
                                        }
                                    />
                                </Group>

                                {notificationSettings.quietHoursEnabled && (
                                    <Group grow>
                                        <TextInput
                                            label="Start Time"
                                            placeholder="22:00"
                                            value={notificationSettings.quietHoursStart}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    quietHoursStart: e.currentTarget.value,
                                                })
                                            }
                                        />
                                        <TextInput
                                            label="End Time"
                                            placeholder="08:00"
                                            value={notificationSettings.quietHoursEnd}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    quietHoursEnd: e.currentTarget.value,
                                                })
                                            }
                                        />
                                    </Group>
                                )}
                            </Stack>
                        </Card>

                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Text fw={600} size="sm">
                                    Notification Types
                                </Text>

                                <Text size="sm" c="dimmed">
                                    Choose which types of notifications you want to receive
                                </Text>

                                <Stack gap="sm">
                                    <Group justify="space-between">
                                        <div>
                                            <Text size="sm" fw={500}>
                                                🎯 Goal Milestones
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                When you reach 25%, 50%, 75%, 100% of a goal
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.goalMilestones}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    goalMilestones: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Group justify="space-between">
                                        <div>
                                            <Text size="sm" fw={500}>
                                                ✅ Task Completions
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                Celebrations when you complete tasks
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.taskCompletions}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    taskCompletions: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Group justify="space-between">
                                        <div>
                                            <Text size="sm" fw={500}>
                                                📊 Weekly Recap
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                Summary of your progress every week
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.weeklyRecap}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    weeklyRecap: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Group justify="space-between">
                                        <div>
                                            <Text size="sm" fw={500}>
                                                👋 Activity Nudges
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                Gentle reminders if you haven't checked in
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.nudges}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    nudges: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>

                                    <Group justify="space-between">
                                        <div>
                                            <Text size="sm" fw={500}>
                                                ⚠️ Critical Alerts
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                Important warnings (metric drops, goal off-track)
                                            </Text>
                                        </div>
                                        <Switch
                                            checked={notificationSettings.alerts}
                                            onChange={(e) =>
                                                setNotificationSettings({
                                                    ...notificationSettings,
                                                    alerts: e.currentTarget.checked,
                                                })
                                            }
                                        />
                                    </Group>
                                </Stack>
                            </Stack>
                        </Card>

                        <Group justify="flex-end">
                            <Button leftSection={<IconDeviceFloppy size={18} />} onClick={handleSaveNotifications}>
                                Save Notification Preferences
                            </Button>
                        </Group>
                    </Stack>
                )}

                {/* Account Tab */}
                {activeTab === 'account' && (
                    <Stack gap="lg">
                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconUser size={20} color="#0ea5e9" />
                                    <Text fw={600} size="sm">
                                        Personal Information
                                    </Text>
                                </Group>

                                <TextInput
                                    label="Full Name"
                                    placeholder="Your name"
                                    value={name}
                                    onChange={(e) => setName(e.currentTarget.value)}
                                />

                                <TextInput
                                    label="Email Address"
                                    placeholder="your@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.currentTarget.value)}
                                    disabled
                                    description="Contact support to change your email"
                                />

                                <TextInput
                                    label="Business Name"
                                    placeholder="Your business name"
                                    value={businessName}
                                    onChange={(e) => setBusinessName(e.currentTarget.value)}
                                />

                                <Select
                                    label="Timezone"
                                    placeholder="Select timezone"
                                    value={timezone}
                                    onChange={(value) => setTimezone(value || 'UTC')}
                                    data={[
                                        { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
                                        { value: 'America/Denver', label: 'Mountain Time (MT)' },
                                        { value: 'America/Chicago', label: 'Central Time (CT)' },
                                        { value: 'America/New_York', label: 'Eastern Time (ET)' },
                                        { value: 'UTC', label: 'UTC' },
                                    ]}
                                />
                            </Stack>
                        </Card>

                        <Group justify="flex-end">
                            <Button leftSection={<IconDeviceFloppy size={18} />} onClick={handleSaveAccount}>
                                Save Account Settings
                            </Button>
                        </Group>
                    </Stack>
                )}

                {/* Appearance Tab */}
                {activeTab === 'appearance' && (
                    <Stack gap="lg">
                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconPalette size={20} color="#0ea5e9" />
                                    <Text fw={600} size="sm">
                                        Theme
                                    </Text>
                                </Group>

                                <SegmentedControl
                                    value={theme}
                                    onChange={(value) => setTheme(value as 'light' | 'dark' | 'auto')}
                                    data={[
                                        { label: '☀️ Light', value: 'light' },
                                        { label: '🌙 Dark', value: 'dark' },
                                        { label: '🔄 Auto', value: 'auto' },
                                    ]}
                                />

                                <Text size="sm" c="dimmed" mt="xs">
                                    Dark mode coming soon! Currently in light mode only.
                                </Text>
                            </Stack>
                        </Card>
                    </Stack>
                )}

                {/* Security Tab */}
                {activeTab === 'security' && (
                    <Stack gap="lg">
                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconShield size={20} color="#0ea5e9" />
                                    <Text fw={600} size="sm">
                                        Password & Security
                                    </Text>
                                </Group>

                                <Text size="sm" c="dimmed">
                                    Dyocense uses magic link authentication. No password needed!
                                </Text>

                                <div>
                                    <Text size="sm" fw={500} mb="xs">
                                        Current Login Method
                                    </Text>
                                    <Badge size="lg" variant="light" color="blue">
                                        🔐 Magic Link (Passwordless)
                                    </Badge>
                                </div>

                                <Text size="xs" c="dimmed">
                                    You'll receive a secure login link via email each time you sign in. No passwords to
                                    remember or manage.
                                </Text>
                            </Stack>
                        </Card>

                        <Card withBorder radius="md" p="lg">
                            <Stack gap="md">
                                <Group gap="xs">
                                    <IconLock size={20} color="#f76707" />
                                    <Text fw={600} size="sm">
                                        Data & Privacy
                                    </Text>
                                </Group>

                                <Text size="sm" c="dimmed">
                                    Your data is encrypted at rest and in transit. We never sell your information.
                                </Text>

                                <Group gap="sm">
                                    <Button variant="light" color="gray">
                                        Export My Data
                                    </Button>
                                    <Button variant="light" color="red">
                                        Delete Account
                                    </Button>
                                </Group>
                            </Stack>
                        </Card>
                    </Stack>
                )}
            </Stack>
        </Container>
    )
}
