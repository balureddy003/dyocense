/**
 * Simplified Coach Layout - SMB-Friendly Design
 * 
 * Based on UX/UI critique:
 * - Single column layout (no three panes)
 * - Clear visual hierarchy with spacing
 * - Plain language (no jargon)
 * - Mobile-first approach
 * - Progressive disclosure
 */

import {
    Badge,
    Box,
    Button,
    Card,
    Collapse,
    Group,
    Paper,
    Stack,
    Text
} from '@mantine/core';
import {
    IconAlertTriangle,
    IconCheck,
    IconChevronDown,
    IconChevronUp,
    IconClock
} from '@tabler/icons-react';
import React from 'react';

// Improved spacing constants (8px grid system)
const SPACING = {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 24,
    xl: 32,
} as const;

// Critical action card with better visual hierarchy
export const CriticalActionCard: React.FC<{
    icon: string;
    title: string;
    deadline: string;
    why: string;
    clients?: Array<{ name: string; amount: number; days_overdue: number }>;
    products?: Array<{ name: string; current: number; min: number }>;
}> = ({ icon, title, deadline, why, clients, products }) => {
    const [showDetails, setShowDetails] = React.useState(false);

    return (
        <Card
            shadow="md"
            padding={SPACING.md}
            radius="lg"
            style={{
                borderLeft: '4px solid #fa5252',  // Red accent for critical
                backgroundColor: '#fff5f5'  // Light red background
            }}
        >
            <Stack gap={SPACING.sm}>
                {/* Header */}
                <Group justify="apart" align="flex-start">
                    <Group gap={SPACING.sm}>
                        <Text size="24px">{icon}</Text>
                        <Stack gap={4}>
                            <Badge color="red" size="sm" variant="filled">URGENT</Badge>
                            <Text size="xs" c="dimmed" fw={500}>{deadline}</Text>
                        </Stack>
                    </Group>
                    <IconAlertTriangle size={20} color="#fa5252" />
                </Group>

                {/* Action Title - Large and Clear */}
                <Text size="lg" fw={700} c="dark.8" lh={1.3}>
                    {title}
                </Text>

                {/* Why it matters - Plain language */}
                <Paper bg="white" p={SPACING.sm} radius="md">
                    <Text size="sm" fw={600} c="dark.6" mb={4}>
                        Why this matters:
                    </Text>
                    <Text size="sm" c="dark.7">
                        {why}
                    </Text>
                </Paper>

                {/* Client/Product Details - Expandable */}
                {(clients || products) && (
                    <>
                        <Button
                            variant="subtle"
                            color="dark"
                            size="sm"
                            fullWidth
                            onClick={() => setShowDetails(!showDetails)}
                            rightSection={showDetails ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                        >
                            {showDetails ? 'Hide details' : `Show details (${clients?.length || products?.length} items)`}
                        </Button>

                        <Collapse in={showDetails}>
                            <Stack gap={SPACING.xs} mt={SPACING.xs}>
                                {clients?.map((client, idx) => (
                                    <Paper key={idx} p={SPACING.sm} bg="white" radius="md">
                                        <Group justify="apart">
                                            <Text size="sm" fw={600}>{client.name}</Text>
                                            <Text size="sm" fw={700} c="red">
                                                ${client.amount.toLocaleString()}
                                            </Text>
                                        </Group>
                                        <Text size="xs" c="dimmed">
                                            {client.days_overdue} days overdue
                                        </Text>
                                    </Paper>
                                ))}
                                {products?.map((product, idx) => (
                                    <Paper key={idx} p={SPACING.sm} bg="white" radius="md">
                                        <Group justify="apart">
                                            <Text size="sm" fw={600}>{product.name}</Text>
                                            <Group gap={SPACING.xs}>
                                                <Badge color="red" size="sm">{product.current}</Badge>
                                                <Text size="xs" c="dimmed">/ {product.min} needed</Text>
                                            </Group>
                                        </Group>
                                    </Paper>
                                ))}
                            </Stack>
                        </Collapse>
                    </>
                )}

                {/* Primary Action Button - Large and Clear */}
                <Button
                    color="red"
                    size="md"
                    fullWidth
                    radius="md"
                    mt={SPACING.sm}
                    leftSection={<IconCheck size={20} />}
                >
                    Take Action Now
                </Button>
            </Stack>
        </Card>
    );
};

// Progress indicator - simplified and less intrusive
export const SimplifiedProgress: React.FC<{
    message: string;
    current?: number;
    total?: number;
}> = ({ message, current, total }) => {
    return (
        <Paper bg="blue.0" p={SPACING.md} radius="lg">
            <Group gap={SPACING.sm}>
                <IconClock size={20} color="#228be6" />
                <Stack gap={4} style={{ flex: 1 }}>
                    <Text size="sm" fw={600} c="blue.7">
                        {message}
                    </Text>
                    {current !== undefined && total !== undefined && (
                        <Text size="xs" c="dimmed">
                            Step {current} of {total}
                        </Text>
                    )}
                </Stack>
            </Group>
        </Paper>
    );
};

// Quick action buttons - at the top, clear purpose
export const QuickActions: React.FC = () => {
    const actions = [
        { icon: '💰', label: 'Check Cash Flow', color: 'red' },
        { icon: '📦', label: 'Review Inventory', color: 'orange' },
        { icon: '📊', label: 'See Revenue', color: 'green' },
        { icon: '👥', label: 'Customer Status', color: 'blue' },
    ];

    return (
        <Box>
            <Text size="sm" fw={600} c="dimmed" mb={SPACING.sm}>
                What do you need help with?
            </Text>
            <Group gap={SPACING.sm}>
                {actions.map((action) => (
                    <Button
                        key={action.label}
                        variant="light"
                        color={action.color as any}
                        size="md"
                        leftSection={<Text size="lg">{action.icon}</Text>}
                        radius="md"
                        styles={{
                            root: {
                                flex: 1,
                                height: 'auto',
                                minHeight: '64px',
                            },
                            label: {
                                flexDirection: 'column',
                                gap: 4,
                            }
                        }}
                    >
                        <Text size="xs" fw={600}>
                            {action.label}
                        </Text>
                    </Button>
                ))}
            </Group>
        </Box>
    );
};

// Health score widget - simplified
export const SimplifiedHealthScore: React.FC<{ score: number }> = ({ score }) => {
    const getColor = (score: number) => {
        if (score >= 70) return 'green';
        if (score >= 40) return 'orange';
        return 'red';
    };

    const color = getColor(score);

    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg">
            <Stack gap={SPACING.sm}>
                <Text size="sm" fw={600} c="dimmed">
                    Your Business Health
                </Text>
                <Group gap={SPACING.md} align="center">
                    <Text size="48px" fw={700} c={color}>
                        {score}
                    </Text>
                    <Stack gap={4}>
                        <Text size="xs" c="dimmed">out of 100</Text>
                        <Badge color={color} size="md">
                            {score >= 70 ? 'Good' : score >= 40 ? 'Needs Attention' : 'Critical'}
                        </Badge>
                    </Stack>
                </Group>
                <Text size="xs" c="dimmed">
                    {score < 40 && '⚠️ Your business needs immediate attention'}
                    {score >= 40 && score < 70 && '📊 Room for improvement - check action items below'}
                    {score >= 70 && '✅ You\'re doing great! Keep it up'}
                </Text>
            </Stack>
        </Card>
    );
};

export default {
    CriticalActionCard,
    SimplifiedProgress,
    QuickActions,
    SimplifiedHealthScore,
};

export { SPACING };
