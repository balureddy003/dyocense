import { Badge, Button, Card, Container, Divider, Group, Modal, Paper, Progress, SimpleGrid, Stack, Tabs, Text, ThemeIcon, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import confetti from 'canvas-confetti';
import { useState } from 'react';
import { ShareButton } from '../components/SocialShare';
import { get, post } from '../lib/api';
import { useAuthStore } from '../stores/auth';

interface Achievement {
    id: string;
    title: string;
    description: string;
    icon: string;
    category: 'goals' | 'streaks' | 'tasks' | 'health' | 'special';
    tier: 'bronze' | 'silver' | 'gold' | 'platinum';
    unlocked: boolean;
    unlockedDate?: string;
    progress?: number;
    target?: number;
    reward?: string;
}

export function Achievements() {
    const tenantId = useAuthStore((s) => s.tenantId);
    const apiToken = useAuthStore((s) => s.apiToken);
    const queryClient = useQueryClient();

    const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);
    const [activeTab, setActiveTab] = useState('all');

    // Fetch achievements
    const { data: achievements = [], refetch } = useQuery({
        queryKey: ['achievements', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/achievements`, apiToken),
        enabled: !!tenantId && !!apiToken,
    });

    // Fetch XP stats
    const { data: xpStats } = useQuery({
        queryKey: ['achievements-xp', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/achievements/xp`, apiToken),
        enabled: !!tenantId && !!apiToken,
    });

    // Check for new unlocks mutation
    const checkAchievements = useMutation({
        mutationFn: () => post(`/v1/tenants/${tenantId}/achievements/check`, {}, apiToken),
        onSuccess: (data: any) => {
            if (data.newly_unlocked && data.newly_unlocked.length > 0) {
                // Show confetti and notifications for new unlocks
                data.newly_unlocked.forEach((achievement: Achievement) => {
                    confetti({
                        particleCount: 100,
                        spread: 70,
                        origin: { y: 0.6 },
                        colors: ['#FFD700', '#FFA500', '#FF6347'],
                    });

                    notifications.show({
                        title: '🎉 Achievement Unlocked!',
                        message: `${achievement.title}: ${achievement.description}`,
                        color: 'teal',
                        autoClose: 5000,
                    });
                });
            }
            // Refresh achievements list
            queryClient.invalidateQueries({ queryKey: ['achievements', tenantId] });
            queryClient.invalidateQueries({ queryKey: ['achievements-xp', tenantId] });
        },
    });

    // Share achievement mutation
    const shareAchievement = useMutation({
        mutationFn: (achievementId: string) =>
            post(`/v1/tenants/${tenantId}/achievements/${achievementId}/share`, {}, apiToken),
        onSuccess: () => {
            notifications.show({
                title: 'Shared!',
                message: 'Achievement shared successfully',
                color: 'blue',
            });
            queryClient.invalidateQueries({ queryKey: ['achievements', tenantId] });
        },
    });

    const unlockedCount = achievements.filter((a: Achievement) => a.unlocked).length;
    const totalXP = xpStats?.total_xp || 0;

    const getTierColor = (tier: Achievement['tier']) => {
        switch (tier) {
            case 'bronze': return '#CD7F32';
            case 'silver': return '#C0C0C0';
            case 'gold': return '#FFD700';
            case 'platinum': return '#E5E4E2';
            default: return '#666';
        }
    };

    const getCategoryIcon = (category: Achievement['category']) => {
        switch (category) {
            case 'goals': return '🎯';
            case 'streaks': return '🔥';
            case 'tasks': return '✅';
            case 'health': return '💚';
            case 'special': return '⭐';
        }
    };

    const filteredAchievements = activeTab === 'all'
        ? achievements
        : achievements.filter((a: Achievement) => a.category === activeTab);

    const handleUnlockDemo = (achievement: Achievement) => {
        if (achievement.unlocked) return;

        // Simulate unlocking (for demo purposes)
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FFD700', '#FFA500', '#FF6347'],
        });

        notifications.show({
            title: '🎉 Achievement Unlocked!',
            message: `${achievement.title}: ${achievement.description}`,
            color: 'teal',
            autoClose: 5000,
        });
    };

    return (
        <Container size="xl" py="xl">
            {/* Header */}
            <Group justify="space-between" mb="xl">
                <div>
                    <Title order={1} size="h2">🏆 Achievements</Title>
                    <Text c="dimmed" mt="xs">Unlock badges and track your business fitness journey</Text>
                </div>
                <Group>
                    <Button
                        onClick={() => checkAchievements.mutate()}
                        loading={checkAchievements.isPending}
                        variant="light"
                        color="teal"
                    >
                        Check Progress
                    </Button>
                    <Paper p="md" withBorder>
                        <Group gap="xl">
                            <div>
                                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Total XP</Text>
                                <Text size="xl" fw={700} c="indigo">{totalXP}</Text>
                            </div>
                            <div>
                                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Achievements</Text>
                                <Text size="xl" fw={700}>{unlockedCount}/{achievements.length}</Text>
                            </div>
                        </Group>
                    </Paper>
                </Group>
            </Group>

            {/* Progress Overview */}
            <Card shadow="sm" padding="lg" radius="md" withBorder mb="xl">
                <Group justify="space-between" mb="md">
                    <Text fw={600} size="lg">Overall Progress</Text>
                    <Badge size="lg" variant="light" color="teal">
                        {Math.round((unlockedCount / achievements.length) * 100)}% Complete
                    </Badge>
                </Group>
                <Progress
                    value={(unlockedCount / achievements.length) * 100}
                    size="xl"
                    radius="xl"
                    color="teal"
                    animated
                />
                <Group justify="space-between" mt="md">
                    <Text size="sm" c="dimmed">{unlockedCount} unlocked</Text>
                    <Text size="sm" c="dimmed">{achievements.length - unlockedCount} remaining</Text>
                </Group>
            </Card>

            {/* Category Stats */}
            <SimpleGrid cols={{ base: 1, sm: 2, lg: 5 }} mb="xl">
                {(['all', 'goals', 'streaks', 'tasks', 'health', 'special'] as const).map((category) => {
                    const categoryAchievements = category === 'all'
                        ? achievements
                        : achievements.filter((a: Achievement) => a.category === category);
                    const unlockedInCategory = categoryAchievements.filter((a: Achievement) => a.unlocked).length;

                    return (
                        <Card key={category} shadow="sm" padding="md" radius="md" withBorder style={{ cursor: 'pointer' }} onClick={() => setActiveTab(category)}>
                            <Group justify="space-between">
                                <div>
                                    <Text size="xs" tt="uppercase" c="dimmed" fw={700}>
                                        {category === 'all' ? 'All' : category.charAt(0).toUpperCase() + category.slice(1)}
                                    </Text>
                                    <Text size="xl" fw={700} mt={4}>{unlockedInCategory}/{categoryAchievements.length}</Text>
                                </div>
                                <ThemeIcon size="lg" variant="light" color={activeTab === category ? 'indigo' : 'gray'}>
                                    {category === 'all' ? '🏆' : getCategoryIcon(category as Achievement['category'])}
                                </ThemeIcon>
                            </Group>
                        </Card>
                    );
                })}
            </SimpleGrid>

            {/* Achievements Grid */}
            <Tabs value={activeTab} onChange={(val) => setActiveTab(val || 'all')}>
                <Tabs.List mb="xl">
                    <Tabs.Tab value="all">All Achievements</Tabs.Tab>
                    <Tabs.Tab value="goals">Goals 🎯</Tabs.Tab>
                    <Tabs.Tab value="streaks">Streaks 🔥</Tabs.Tab>
                    <Tabs.Tab value="tasks">Tasks ✅</Tabs.Tab>
                    <Tabs.Tab value="health">Health 💚</Tabs.Tab>
                    <Tabs.Tab value="special">Special ⭐</Tabs.Tab>
                </Tabs.List>

                <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
                    {filteredAchievements.map((achievement: Achievement) => (
                        <Card
                            key={achievement.id}
                            shadow="sm"
                            padding="lg"
                            radius="md"
                            withBorder
                            style={{
                                opacity: achievement.unlocked ? 1 : 0.6,
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                            }}
                            onClick={() => setSelectedAchievement(achievement)}
                        >
                            <Stack gap="md">
                                <Group justify="space-between">
                                    <ThemeIcon
                                        size={60}
                                        radius="md"
                                        variant="light"
                                        style={{
                                            backgroundColor: achievement.unlocked ? getTierColor(achievement.tier) + '20' : '#f0f0f0',
                                            fontSize: '2rem',
                                        }}
                                    >
                                        {achievement.unlocked ? achievement.icon : '🔒'}
                                    </ThemeIcon>
                                    <Badge
                                        color={achievement.tier === 'platinum' ? 'gray' : achievement.tier === 'gold' ? 'yellow' : achievement.tier === 'silver' ? 'gray' : 'orange'}
                                        variant="filled"
                                        style={{ backgroundColor: getTierColor(achievement.tier) }}
                                    >
                                        {achievement.tier.toUpperCase()}
                                    </Badge>
                                </Group>

                                <div>
                                    <Text fw={600} size="lg">{achievement.title}</Text>
                                    <Text size="sm" c="dimmed" mt={4}>{achievement.description}</Text>
                                </div>

                                {achievement.unlocked ? (
                                    <div>
                                        <Group justify="space-between">
                                            <Badge color="teal" variant="light">✓ Unlocked</Badge>
                                            <Text size="xs" c="dimmed">{achievement.unlockedDate}</Text>
                                        </Group>
                                        {achievement.reward && (
                                            <Text size="sm" c="indigo" fw={600} mt="xs">{achievement.reward}</Text>
                                        )}
                                    </div>
                                ) : (
                                    <div>
                                        {achievement.progress !== undefined && achievement.target !== undefined && (
                                            <>
                                                <Group justify="space-between" mb="xs">
                                                    <Text size="sm" fw={500}>Progress</Text>
                                                    <Text size="sm" c="dimmed">{achievement.progress}/{achievement.target}</Text>
                                                </Group>
                                                <Progress
                                                    value={(achievement.progress / achievement.target) * 100}
                                                    size="md"
                                                    radius="xl"
                                                    color="indigo"
                                                />
                                            </>
                                        )}
                                        {achievement.reward && (
                                            <Text size="sm" c="dimmed" mt="xs">Reward: {achievement.reward}</Text>
                                        )}
                                    </div>
                                )}
                            </Stack>
                        </Card>
                    ))}
                </SimpleGrid>
            </Tabs>

            {/* Leaderboard Section */}
            <Card shadow="sm" padding="lg" radius="md" withBorder mt="xl">
                <Group justify="space-between" mb="md">
                    <div>
                        <Text fw={600} size="lg">🏅 Industry Leaderboard</Text>
                        <Text size="sm" c="dimmed">Compare your progress with similar businesses</Text>
                    </div>
                    <Badge color="blue" variant="light">Outdoor Equipment</Badge>
                </Group>

                <Stack gap="md">
                    {[
                        { rank: 1, name: 'TrailBlaze Gear', score: 95, xp: 2850, achievements: 18 },
                        { rank: 2, name: 'Summit Outfitters', score: 92, xp: 2640, achievements: 17 },
                        { rank: 3, name: 'CycloneRake (You)', score: 80, xp: totalXP, achievements: unlockedCount, highlight: true },
                        { rank: 4, name: 'Adventure Co.', score: 78, xp: 2180, achievements: 14 },
                        { rank: 5, name: 'Peak Performance', score: 75, xp: 2050, achievements: 13 },
                    ].map((entry) => (
                        <Paper
                            key={entry.rank}
                            p="md"
                            withBorder
                            style={{
                                backgroundColor: entry.highlight ? '#EEF2FF' : 'transparent',
                                borderColor: entry.highlight ? '#4F46E5' : undefined,
                                borderWidth: entry.highlight ? 2 : 1,
                            }}
                        >
                            <Group justify="space-between">
                                <Group gap="md">
                                    <ThemeIcon
                                        size="lg"
                                        radius="xl"
                                        variant={entry.rank <= 3 ? 'filled' : 'light'}
                                        color={entry.rank === 1 ? 'yellow' : entry.rank === 2 ? 'gray' : entry.rank === 3 ? 'orange' : 'blue'}
                                    >
                                        {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                                    </ThemeIcon>
                                    <div>
                                        <Text fw={600}>{entry.name}</Text>
                                        <Group gap="xs">
                                            <Text size="sm" c="dimmed">Score: {entry.score}</Text>
                                            <Text size="sm" c="dimmed">•</Text>
                                            <Text size="sm" c="dimmed">{entry.achievements} achievements</Text>
                                        </Group>
                                    </div>
                                </Group>
                                <Text fw={700} c="indigo">{entry.xp} XP</Text>
                            </Group>
                        </Paper>
                    ))}
                </Stack>

                <Divider my="md" />
                <Text size="xs" c="dimmed" ta="center">
                    Rankings update daily • Only businesses in similar industries are compared
                </Text>
            </Card>

            {/* Achievement Detail Modal */}
            <Modal
                opened={selectedAchievement !== null}
                onClose={() => setSelectedAchievement(null)}
                title={
                    <Group>
                        <Text size="2rem">{selectedAchievement?.unlocked ? selectedAchievement.icon : '🔒'}</Text>
                        <div>
                            <Text fw={600} size="lg">{selectedAchievement?.title}</Text>
                            <Badge
                                size="sm"
                                color={selectedAchievement?.tier === 'platinum' ? 'gray' : selectedAchievement?.tier === 'gold' ? 'yellow' : selectedAchievement?.tier === 'silver' ? 'gray' : 'orange'}
                                variant="filled"
                                style={{ backgroundColor: selectedAchievement ? getTierColor(selectedAchievement.tier) : undefined }}
                            >
                                {selectedAchievement?.tier.toUpperCase()}
                            </Badge>
                        </div>
                    </Group>
                }
                centered
                size="md"
            >
                {selectedAchievement && (
                    <Stack gap="md">
                        <Text>{selectedAchievement.description}</Text>

                        {selectedAchievement.unlocked ? (
                            <>
                                <Divider />
                                <Group justify="space-between">
                                    <Text size="sm" c="dimmed">Unlocked on</Text>
                                    <Text fw={600}>{selectedAchievement.unlockedDate}</Text>
                                </Group>
                                <Group justify="space-between">
                                    <Text size="sm" c="dimmed">Reward</Text>
                                    <Text fw={600} c="indigo">{selectedAchievement.reward}</Text>
                                </Group>
                            </>
                        ) : (
                            <>
                                {selectedAchievement.progress !== undefined && selectedAchievement.target !== undefined && (
                                    <>
                                        <Divider />
                                        <div>
                                            <Group justify="space-between" mb="xs">
                                                <Text fw={500}>Your Progress</Text>
                                                <Text c="dimmed">{selectedAchievement.progress}/{selectedAchievement.target}</Text>
                                            </Group>
                                            <Progress
                                                value={(selectedAchievement.progress / selectedAchievement.target) * 100}
                                                size="xl"
                                                radius="xl"
                                                color="indigo"
                                                animated
                                            />
                                        </div>
                                        <Text size="sm" c="dimmed">
                                            {selectedAchievement.target - selectedAchievement.progress} more to unlock
                                        </Text>
                                    </>
                                )}
                                <Divider />
                                <Group justify="space-between">
                                    <Text size="sm" c="dimmed">Reward when unlocked</Text>
                                    <Text fw={600} c="indigo">{selectedAchievement.reward}</Text>
                                </Group>

                                {/* Demo unlock button */}
                                <Button
                                    fullWidth
                                    variant="light"
                                    onClick={() => handleUnlockDemo(selectedAchievement)}
                                >
                                    🎁 Unlock Now (Demo)
                                </Button>
                            </>
                        )}

                        <Divider />
                        <Group justify="space-between">
                            <Text size="sm" c="dimmed">Category</Text>
                            <Badge variant="light">
                                {getCategoryIcon(selectedAchievement.category)} {selectedAchievement.category.charAt(0).toUpperCase() + selectedAchievement.category.slice(1)}
                            </Badge>
                        </Group>

                        {/* Social Share Button for unlocked achievements */}
                        {selectedAchievement.unlocked && (
                            <>
                                <Divider />
                                <ShareButton
                                    achievement={{
                                        id: selectedAchievement.id,
                                        title: selectedAchievement.title,
                                        description: selectedAchievement.description,
                                        icon: selectedAchievement.icon,
                                        type: 'achievement',
                                        value: selectedAchievement.reward,
                                        date: selectedAchievement.unlockedDate || new Date().toLocaleDateString(),
                                    }}
                                    businessName="CycloneRake"
                                    variant="light"
                                />
                            </>
                        )}
                    </Stack>
                )}
            </Modal>
        </Container>
    );
}
