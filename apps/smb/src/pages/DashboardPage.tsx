import { Badge, Card, Container, Group, Stack, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import React from 'react'
import { listUsersV4, listWorkspacesV4 } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export const DashboardPage: React.FC = () => {
    const { token, user } = useAuthStore()

    const { data: users } = useQuery({
        queryKey: ['users'],
        queryFn: () => listUsersV4(token!),
        enabled: !!token,
    })

    const { data: workspaces } = useQuery({
        queryKey: ['workspaces'],
        queryFn: () => listWorkspacesV4(token!),
        enabled: !!token,
    })

    return (
        <Container size="lg" py="xl">
            <Stack gap="lg">
                <div>
                    <Title order={1}>Dashboard</Title>
                    <Text c="dimmed">Welcome back, {user?.email}</Text>
                </div>

                <Group>
                    <Badge color="blue">Tenant: {user?.tenant_id}</Badge>
                    <Badge color="grape">Role: {user?.role}</Badge>
                </Group>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Title order={3} mb="md">Users ({users?.length || 0})</Title>
                    <Stack gap="xs">
                        {users?.map((u) => (
                            <div key={u.id}>
                                <Text fw={500}>{u.email}</Text>
                                <Text size="sm" c="dimmed">
                                    Role: {u.role} • {u.is_active ? 'Active' : 'Inactive'}
                                </Text>
                            </div>
                        ))}
                    </Stack>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Title order={3} mb="md">Workspaces ({workspaces?.length || 0})</Title>
                    <Stack gap="xs">
                        {workspaces?.map((w) => (
                            <div key={w.id}>
                                <Text fw={500}>{w.name}</Text>
                                {w.description && <Text size="sm" c="dimmed">{w.description}</Text>}
                            </div>
                        ))}
                    </Stack>
                </Card>
            </Stack>
        </Container>
    )
}

export default DashboardPage
