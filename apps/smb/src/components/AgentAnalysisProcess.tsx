import { Box, Collapse, Group, Text, UnstyledButton } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { useState } from 'react';

interface AgentStep {
    id: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

interface AgentAnalysisProcessProps {
    steps: AgentStep[];
    isStreaming?: boolean;
}

export function AgentAnalysisProcess({ steps, isStreaming = false }: AgentAnalysisProcessProps) {
    const [isOpen, setIsOpen] = useState(isStreaming);

    if (!steps || steps.length === 0) {
        return null;
    }

    const completedSteps = steps.filter(s => s.status === 'completed').length;
    const failedSteps = steps.filter(s => s.status === 'failed').length;
    const totalSteps = steps.length;

    return (
        <Box
            style={{
                border: '1px solid #e5e7eb',
                borderRadius: 8,
                background: '#f9fafb',
                marginTop: 12,
                marginBottom: 12,
            }}
        >
            <UnstyledButton
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    width: '100%',
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'background 0.2s',
                }}
                onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f3f4f6';
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                }}
            >
                <Group gap={8}>
                    {isOpen ? (
                        <IconChevronDown size={16} color="#6b7280" />
                    ) : (
                        <IconChevronRight size={16} color="#6b7280" />
                    )}
                    <Text size="sm" fw={600} c="#374151">
                        🤖 Agent Analysis Process
                    </Text>
                    <Text size="xs" c="#6b7280">
                        {isStreaming ? (
                            `${completedSteps}/${totalSteps} steps completed...`
                        ) : failedSteps > 0 ? (
                            `${completedSteps} completed, ${failedSteps} failed`
                        ) : (
                            `${totalSteps} steps completed`
                        )}
                    </Text>
                </Group>
            </UnstyledButton>

            <Collapse in={isOpen}>
                <Box
                    style={{
                        padding: '0 16px 12px 16px',
                        borderTop: '1px solid #e5e7eb',
                        marginTop: 0,
                    }}
                >
                    {steps.map((step, idx) => (
                        <Group
                            key={step.id}
                            gap={8}
                            style={{
                                marginTop: idx === 0 ? 12 : 8,
                                alignItems: 'flex-start',
                            }}
                        >
                            <Box style={{ marginTop: 2 }}>
                                {step.status === 'completed' ? (
                                    <span style={{ color: '#10b981', fontSize: 14 }}>✓</span>
                                ) : step.status === 'failed' ? (
                                    <span style={{ color: '#ef4444', fontSize: 14 }}>✗</span>
                                ) : step.status === 'in_progress' ? (
                                    <span style={{ color: '#f59e0b', fontSize: 14 }}>⏳</span>
                                ) : (
                                    <span style={{ color: '#9ca3af', fontSize: 14 }}>○</span>
                                )}
                            </Box>
                            <Text
                                size="sm"
                                c={
                                    step.status === 'completed'
                                        ? '#059669'
                                        : step.status === 'failed'
                                            ? '#dc2626'
                                            : step.status === 'in_progress'
                                                ? '#d97706'
                                                : '#6b7280'
                                }
                                style={{
                                    flex: 1,
                                    textDecoration: step.status === 'completed' ? 'none' : undefined,
                                }}
                            >
                                {step.description}
                            </Text>
                        </Group>
                    ))}
                </Box>
            </Collapse>
        </Box>
    );
}
