/**
 * Dynamic Industry-Specific Dashboard Component
 * 
 * Renders dashboard widgets based on business type classification.
 * Fetches layout configuration from backend and dynamically renders:
 * - Industry-specific metric cards
 * - Charts and visualizations
 * - Tables and data grids
 * - Responsive 12-column grid layout
 */

import { Alert, Center, Loader, SimpleGrid, Stack, Text } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { DynamicChart } from './DynamicChart';
import { DynamicMetricCard } from './DynamicMetricCard';
import { DynamicTable } from './DynamicTable';

export interface DashboardWidget {
    id: string;
    type: 'metric_card' | 'chart' | 'table' | 'alert' | 'goal_progress' | 'recommendation' | 'timeline' | 'heatmap';
    title: string;
    metric_id?: string;
    chart_type?: 'line' | 'bar' | 'pie' | 'area' | 'sparkline' | 'gauge';
    col_span: number;
    row_span: number;
    priority: number;
    color_scheme?: string;
    show_trend: boolean;
    show_sparkline: boolean;
    data_source?: string;
    refresh_interval?: number;
    min_confidence?: number;
    config: Record<string, any>;
}

export interface DashboardLayout {
    business_type: string;
    display_name: string;
    description: string;
    theme_color: string;
    icon: string;
    widgets: DashboardWidget[];
}

interface IndustryDashboardProps {
    tenantId: string;
    token: string;
}

export function IndustryDashboard({ tenantId, token }: IndustryDashboardProps) {
    const [layout, setLayout] = useState<DashboardLayout | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchDashboardLayout();
    }, [tenantId]);

    const fetchDashboardLayout = async () => {
        try {
            setLoading(true);
            setError(null);

            // Use relative URL - assumes API is at same origin
            const response = await fetch(
                `/v1/tenants/${tenantId}/dashboard/layout`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(`Failed to fetch dashboard layout: ${response.statusText}`);
            }

            const data = await response.json();
            setLayout(data);
        } catch (err) {
            console.error('Error fetching dashboard layout:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const renderWidget = (widget: DashboardWidget) => {
        const key = `widget-${widget.id}`;

        switch (widget.type) {
            case 'metric_card':
                return (
                    <DynamicMetricCard
                        key={key}
                        widget={widget}
                        tenantId={tenantId}
                        token={token}
                    />
                );

            case 'chart':
                return (
                    <DynamicChart
                        key={key}
                        widget={widget}
                        tenantId={tenantId}
                        token={token}
                    />
                );

            case 'table':
                return (
                    <DynamicTable
                        key={key}
                        widget={widget}
                        tenantId={tenantId}
                        token={token}
                    />
                );

            default:
                return (
                    <div key={key}>
                        <Text size="sm" c="dimmed">
                            Widget type "{widget.type}" not yet implemented
                        </Text>
                    </div>
                );
        }
    };

    if (loading) {
        return (
            <Center h={400}>
                <Stack align="center" gap="md">
                    <Loader size="lg" />
                    <Text c="dimmed">Loading your personalized dashboard...</Text>
                </Stack>
            </Center>
        );
    }

    if (error) {
        return (
            <Alert icon={<IconAlertCircle />} color="red" title="Error Loading Dashboard">
                {error}
            </Alert>
        );
    }

    if (!layout) {
        return (
            <Alert icon={<IconAlertCircle />} color="yellow" title="No Dashboard Layout">
                Dashboard configuration not available
            </Alert>
        );
    }

    // Group widgets by row based on col_span
    // Simple responsive grid: 12-column layout
    const gridCols = { base: 1, sm: 2, md: 3, lg: 4 };

    return (
        <Stack gap="lg">
            {/* Dashboard Header */}
            <Stack gap="xs">
                <Text size="xl" fw={700}>
                    {layout.display_name}
                </Text>
                <Text size="sm" c="dimmed">
                    {layout.description}
                </Text>
            </Stack>

            {/* Dynamic Widget Grid */}
            <SimpleGrid cols={gridCols} spacing="md">
                {layout.widgets
                    .sort((a, b) => a.priority - b.priority)
                    .map((widget) => renderWidget(widget))}
            </SimpleGrid>
        </Stack>
    );
}
