import { ActionIcon, Badge, Button, Card, CopyButton, Divider, Group, Modal, Select, Stack, Text, Textarea, TextInput, ThemeIcon, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import confetti from 'canvas-confetti';
import { useState } from 'react';

interface ShareableAchievement {
    id: string;
    title: string;
    description: string;
    icon: string;
    type: 'achievement' | 'milestone' | 'streak' | 'health';
    value?: string;
    date: string;
}

interface SocialShareProps {
    achievement: ShareableAchievement;
    businessName?: string;
    onClose?: () => void;
}

export function SocialShareModal({ achievement, businessName = 'CycloneRake', onClose }: SocialShareProps) {
    const [platform, setPlatform] = useState<'linkedin' | 'twitter' | 'facebook'>('linkedin');
    const [customMessage, setCustomMessage] = useState('');

    const generateShareText = () => {
        const baseMessages: Record<ShareableAchievement['type'], string> = {
            achievement: `🎉 Just unlocked "${achievement.title}" on my business fitness journey! ${achievement.description} #BusinessGrowth #Entrepreneur`,
            milestone: `🎯 Milestone achieved: ${achievement.title}! ${achievement.value || ''} #BusinessSuccess #Growth`,
            streak: `🔥 ${achievement.title}! Consistency is key to business success. ${achievement.value || ''} #Dedication #BusinessFitness`,
            health: `💪 Business Health Update: ${achievement.title}! ${achievement.value || ''} #HealthyBusiness #Progress`,
        };

        if (customMessage.trim()) {
            return customMessage;
        }

        return baseMessages[achievement.type];
    };

    const getShareUrl = () => {
        const text = encodeURIComponent(generateShareText());
        const url = encodeURIComponent('https://dyocense.com'); // Replace with actual URL

        switch (platform) {
            case 'linkedin':
                return `https://www.linkedin.com/sharing/share-offsite/?url=${url}&summary=${text}`;
            case 'twitter':
                return `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
            case 'facebook':
                return `https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${text}`;
            default:
                return '';
        }
    };

    const handleShare = () => {
        const shareUrl = getShareUrl();
        window.open(shareUrl, '_blank', 'width=600,height=400');

        confetti({
            particleCount: 50,
            spread: 60,
            origin: { y: 0.7 },
        });

        notifications.show({
            title: 'Opening share dialog...',
            message: `Sharing to ${platform.charAt(0).toUpperCase() + platform.slice(1)}`,
            color: 'blue',
            autoClose: 3000,
        });

        // Track sharing event (mock)
        console.log('Share event:', { achievement: achievement.id, platform });
    };

    const generateImageUrl = () => {
        // In production, this would call an API to generate a shareable image
        return `https://api.dyocense.com/share/${achievement.id}.png`;
    };

    return (
        <Modal opened={true} onClose={onClose || (() => { })} title="Share Your Achievement" size="lg" centered>
            <Stack gap="lg">
                {/* Preview Card */}
                <Card shadow="md" padding="xl" radius="lg" withBorder style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                    <Stack gap="md" align="center">
                        <ThemeIcon size={80} radius="xl" variant="white" color="white">
                            <Text size="3rem">{achievement.icon}</Text>
                        </ThemeIcon>
                        <div style={{ textAlign: 'center' }}>
                            <Text size="xl" fw={700} c="white">{achievement.title}</Text>
                            <Text size="sm" c="rgba(255,255,255,0.9)" mt="xs">{achievement.description}</Text>
                            {achievement.value && (
                                <Badge size="lg" variant="white" color="dark" mt="md">{achievement.value}</Badge>
                            )}
                        </div>
                        <Divider style={{ width: '100%', borderColor: 'rgba(255,255,255,0.3)' }} />
                        <Group gap="xs">
                            <Text size="sm" c="rgba(255,255,255,0.8)">🏢 {businessName}</Text>
                            <Text size="sm" c="rgba(255,255,255,0.6)">•</Text>
                            <Text size="sm" c="rgba(255,255,255,0.8)">📅 {achievement.date}</Text>
                        </Group>
                    </Stack>
                </Card>

                {/* Platform Selection */}
                <Select
                    label="Share to"
                    placeholder="Select platform"
                    value={platform}
                    onChange={(value) => setPlatform(value as typeof platform)}
                    data={[
                        { value: 'linkedin', label: 'LinkedIn' },
                        { value: 'twitter', label: 'Twitter / X' },
                        { value: 'facebook', label: 'Facebook' },
                    ]}
                />

                {/* Custom Message */}
                <Textarea
                    label="Custom message (optional)"
                    placeholder={generateShareText()}
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.currentTarget.value)}
                    minRows={3}
                    maxRows={6}
                    description={`${customMessage.length}/280 characters`}
                    maxLength={280}
                />

                {/* Share URL Preview */}
                <div>
                    <Text size="sm" fw={500} mb="xs">Share URL</Text>
                    <Group gap="xs">
                        <TextInput
                            value="https://dyocense.com"
                            readOnly
                            style={{ flex: 1 }}
                        />
                        <CopyButton value="https://dyocense.com">
                            {({ copied, copy }) => (
                                <Tooltip label={copied ? 'Copied!' : 'Copy link'}>
                                    <ActionIcon variant="light" onClick={copy} size="lg">
                                        {copied ? '✓' : '📋'}
                                    </ActionIcon>
                                </Tooltip>
                            )}
                        </CopyButton>
                    </Group>
                </div>

                {/* Action Buttons */}
                <Group justify="space-between">
                    <Button variant="subtle" onClick={onClose}>Cancel</Button>
                    <Group gap="xs">
                        <Button variant="light" leftSection="🖼️">
                            Download Image
                        </Button>
                        <Button onClick={handleShare} leftSection="📤">
                            Share Now
                        </Button>
                    </Group>
                </Group>

                <Divider />

                {/* Privacy Notice */}
                <Text size="xs" c="dimmed" ta="center">
                    🔒 Your privacy matters. Only achievements you choose to share will be public.
                </Text>
            </Stack>
        </Modal>
    );
}

export function ShareButton({ achievement, businessName, variant = 'filled' }: { achievement: ShareableAchievement; businessName?: string; variant?: 'filled' | 'light' | 'outline' }) {
    const [showModal, setShowModal] = useState(false);

    return (
        <>
            <Button
                variant={variant}
                leftSection="📤"
                onClick={() => setShowModal(true)}
                size="sm"
            >
                Share
            </Button>
            {showModal && (
                <SocialShareModal
                    achievement={achievement}
                    businessName={businessName}
                    onClose={() => setShowModal(false)}
                />
            )}
        </>
    );
}

// Sample usage component
export function SocialShareDemo() {
    const sampleAchievements: ShareableAchievement[] = [
        {
            id: 'health_80',
            title: 'Business Health Score: 80',
            description: 'Reached a healthy business score of 80/100',
            icon: '💪',
            type: 'health',
            value: '80/100',
            date: new Date().toLocaleDateString(),
        },
        {
            id: 'streak_4week',
            title: '4-Week Streak',
            description: 'Maintained consistent progress for 4 weeks',
            icon: '🔥',
            type: 'streak',
            value: '28 days',
            date: new Date().toLocaleDateString(),
        },
        {
            id: 'goal_complete',
            title: 'Q4 Sales Goal Achieved',
            description: 'Successfully increased quarterly sales by 25%',
            icon: '🎯',
            type: 'milestone',
            value: '+25% Growth',
            date: new Date().toLocaleDateString(),
        },
        {
            id: 'achievement_unlock',
            title: 'Goal Master',
            description: 'Completed 20 business goals',
            icon: '👑',
            type: 'achievement',
            value: '20 Goals',
            date: new Date().toLocaleDateString(),
        },
    ];

    return (
        <Stack gap="lg" p="xl">
            <div>
                <Text size="xl" fw={700} mb="xs">📤 Social Sharing Demo</Text>
                <Text c="dimmed" size="sm">Share your business achievements with your network</Text>
            </div>

            {sampleAchievements.map((achievement) => (
                <Card key={achievement.id} shadow="sm" padding="lg" radius="md" withBorder>
                    <Group justify="space-between">
                        <Group>
                            <ThemeIcon size="lg" variant="light" color="indigo">
                                {achievement.icon}
                            </ThemeIcon>
                            <div>
                                <Text fw={600}>{achievement.title}</Text>
                                <Text size="sm" c="dimmed">{achievement.description}</Text>
                            </div>
                        </Group>
                        <ShareButton achievement={achievement} />
                    </Group>
                </Card>
            ))}

            <Divider my="md" />

            <Card shadow="sm" padding="lg" radius="md" withBorder style={{ backgroundColor: '#F0F7FF' }}>
                <Stack gap="md">
                    <Group>
                        <ThemeIcon size="lg" variant="light" color="blue">
                            💡
                        </ThemeIcon>
                        <div>
                            <Text fw={600}>Pro Tips for Sharing</Text>
                            <Text size="sm" c="dimmed">Maximize engagement with your posts</Text>
                        </div>
                    </Group>
                    <Stack gap="xs" pl="md">
                        <Group gap="xs">
                            <Text size="sm">•</Text>
                            <Text size="sm">Share during peak hours (9-11 AM, 1-3 PM on weekdays)</Text>
                        </Group>
                        <Group gap="xs">
                            <Text size="sm">•</Text>
                            <Text size="sm">Add context about your journey and lessons learned</Text>
                        </Group>
                        <Group gap="xs">
                            <Text size="sm">•</Text>
                            <Text size="sm">Use relevant hashtags: #BusinessGrowth #Entrepreneur #SmallBusiness</Text>
                        </Group>
                        <Group gap="xs">
                            <Text size="sm">•</Text>
                            <Text size="sm">Tag Dyocense (@dyocense) to inspire other business owners</Text>
                        </Group>
                    </Stack>
                </Stack>
            </Card>
        </Stack>
    );
}
