/**
 * Dynamic Table Component
 * 
 * Renders data tables based on widget configuration
 */

import { Card, Stack, Text } from '@mantine/core';
import type { DashboardWidget } from './IndustryDashboard';

interface DynamicTableProps {
    widget: DashboardWidget;
    tenantId: string;
    token: string;
}

export function DynamicTable({ widget }: DynamicTableProps) {
    // TODO: Implement table rendering with data fetching
    // For now, show placeholder

    return (
        <Card withBorder padding="lg" radius="md" h="100%">
            <Stack gap="xs">
                <Text size="sm" c="dimmed" fw={500}>
                    {widget.title}
                </Text>
                <Text size="xs" c="dimmed">
                    Table implementation pending
                </Text>
            </Stack>
        </Card>
    );
}
