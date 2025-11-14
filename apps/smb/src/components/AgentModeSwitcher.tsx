/**
 * Agent Mode & Context Switcher - Like GitHub Copilot with data source awareness
 * 
 * Modes:
 * - Analyze: Deep analysis with visualizations (current behavior)
 * - Chat: Fast conversational responses
 * - Task: Generate specific actionable tasks
 * 
 * Context: Available data sources/connectors for analysis
 */
import { Badge, Box, Group, MultiSelect, SegmentedControl, Stack, Text, Tooltip } from '@mantine/core';
import { IconChartBar, IconCheckbox, IconCloudDataConnection, IconCurrencyDollar, IconDatabase, IconFileSpreadsheet, IconMessageCircle, IconShoppingCart } from '@tabler/icons-react';
import React from 'react';

export type AgentMode = 'analyze' | 'chat' | 'task';

export interface DataSource {
    id: string;
    type: string;
    name: string;
    category: string;
    icon: string;
    recordCount?: number;
}

interface AgentModeSwitcherProps {
    mode: AgentMode;
    onChange: (mode: AgentMode) => void;
    availableDataSources?: DataSource[];
    selectedDataSources?: string[];
    onDataSourceChange?: (sources: string[]) => void;
}

const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
        case 'finance':
        case 'accounting':
            return <IconCurrencyDollar size={14} />;
        case 'ecommerce':
        case 'sales':
            return <IconShoppingCart size={14} />;
        case 'spreadsheet':
        case 'csv':
            return <IconFileSpreadsheet size={14} />;
        case 'cloud':
            return <IconCloudDataConnection size={14} />;
        default:
            return <IconDatabase size={14} />;
    }
};

export const AgentModeSwitcher: React.FC<AgentModeSwitcherProps> = ({
    mode,
    onChange,
    availableDataSources = [],
    selectedDataSources = [],
    onDataSourceChange
}) => {
    const formatNumber = (num?: number) => {
        if (!num) return '';
        if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
        return num.toString();
    };

    return (
        <Stack gap="sm" mb="md">
            {/* Agent Mode Selector */}
            <Box>
                <Text size="xs" fw={600} c="dimmed" mb={6}>Agent Mode</Text>
                <SegmentedControl
                    value={mode}
                    onChange={(value) => onChange(value as AgentMode)}
                    data={[
                        {
                            value: 'analyze',
                            label: (
                                <Stack gap={4} align="center" py={4}>
                                    <IconChartBar size={16} />
                                    <Text size="xs">Analyze</Text>
                                </Stack>
                            ),
                        },
                        {
                            value: 'chat',
                            label: (
                                <Stack gap={4} align="center" py={4}>
                                    <IconMessageCircle size={16} />
                                    <Text size="xs">Chat</Text>
                                </Stack>
                            ),
                        },
                        {
                            value: 'task',
                            label: (
                                <Stack gap={4} align="center" py={4}>
                                    <IconCheckbox size={16} />
                                    <Text size="xs">Tasks</Text>
                                </Stack>
                            ),
                        },
                    ]}
                    fullWidth
                />
                <Text size="xs" c="dimmed" mt={6}>
                    {mode === 'analyze' && '📊 Deep analysis with charts, tables, and evidence-based insights'}
                    {mode === 'chat' && '💬 Quick conversational answers without heavy processing'}
                    {mode === 'task' && '✅ Generate specific actionable tasks from your data'}
                </Text>
            </Box>

            {/* Data Sources Context */}
            {availableDataSources.length > 0 && onDataSourceChange && (
                <Box>
                    <Group gap={4} mb={6}>
                        <IconDatabase size={12} />
                        <Text size="xs" fw={600} c="dimmed">
                            Data Sources ({selectedDataSources.length} of {availableDataSources.length})
                        </Text>
                    </Group>
                    <MultiSelect
                        placeholder="Select data sources to analyze..."
                        data={availableDataSources.map(ds => ({
                            value: ds.id,
                            label: ds.name,
                            description: `${ds.category} • ${formatNumber(ds.recordCount)} records`,
                        }))}
                        value={selectedDataSources}
                        onChange={onDataSourceChange}
                        searchable
                        clearable
                        size="xs"
                        leftSection={<IconDatabase size={14} />}
                        styles={{
                            input: {
                                fontSize: '12px',
                                minHeight: '32px',
                            }
                        }}
                    />

                    {/* Selected Sources Summary */}
                    {selectedDataSources.length > 0 && (
                        <Group gap={4} mt={6}>
                            {selectedDataSources.map(sourceId => {
                                const source = availableDataSources.find(ds => ds.id === sourceId);
                                if (!source) return null;

                                return (
                                    <Tooltip key={sourceId} label={`${source.type} • ${formatNumber(source.recordCount)} records`}>
                                        <Badge
                                            size="xs"
                                            variant="light"
                                            leftSection={getCategoryIcon(source.category)}
                                        >
                                            {source.name}
                                        </Badge>
                                    </Tooltip>
                                );
                            })}
                        </Group>
                    )}

                    <Text size="xs" c="dimmed" mt={6}>
                        {selectedDataSources.length === 0 && '💡 Select data sources to give the agent clear context'}
                        {selectedDataSources.length === 1 && '✓ Agent will focus on this data source'}
                        {selectedDataSources.length > 1 && `✓ Agent will analyze across ${selectedDataSources.length} sources`}
                    </Text>
                </Box>
            )}
        </Stack>
    );
};

export default AgentModeSwitcher;
