import {
    ActionIcon,
    Avatar,
    Badge,
    Group,
    Popover,
    Stack,
    Text,
    UnstyledButton,
} from '@mantine/core'
import {
    IconBrain,
    IconBriefcase,
    IconChartBar,
    IconChevronDown,
    IconRocket,
    IconSparkles,
    IconSettings as IconTool,
} from '@tabler/icons-react'
import { useState } from 'react'

interface Agent {
    id: string
    name: string
    emoji: string
    icon: any
    description: string
    color: string
}

interface AgentSelectorProps {
    agents: any[]
    selectedAgent: string
    onAgentChange: (agentId: string) => void
    compact?: boolean
}

const agentIcons: Record<string, any> = {
    business_analyst: IconChartBar,
    data_scientist: IconBrain,
    consultant: IconBriefcase,
    operations_manager: IconTool,
    growth_strategist: IconRocket,
}

const agentColors: Record<string, string> = {
    business_analyst: '#3b82f6',
    data_scientist: '#8b5cf6',
    consultant: '#0ea5e9',
    operations_manager: '#f59e0b',
    growth_strategist: '#10b981',
}

export function AgentSelector({ agents, selectedAgent, onAgentChange, compact = false }: AgentSelectorProps) {
    const [opened, setOpened] = useState(false)

    const selected = agents.find((a) => a.id === selectedAgent)
    const Icon = selected ? agentIcons[selected.id] || IconSparkles : IconSparkles
    const color = selected ? agentColors[selected.id] || '#6b7280' : '#6b7280'

    if (compact) {
        return (
            <Popover
                opened={opened}
                onChange={setOpened}
                position="top-start"
                withArrow
                shadow="md"
                styles={{
                    dropdown: {
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        padding: '8px',
                    },
                }}
            >
                <Popover.Target>
                    <UnstyledButton
                        onClick={() => setOpened(!opened)}
                        style={{
                            padding: '6px 12px',
                            borderRadius: '8px',
                            backgroundColor: '#374151',
                            border: '1px solid #4b5563',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#4b5563'
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = '#374151'
                        }}
                    >
                        <Avatar size="xs" radius="sm" style={{ backgroundColor: color }}>
                            <Icon size={14} color="white" />
                        </Avatar>
                        <Text size="sm" c="white" fw={500} style={{ lineHeight: 1 }}>
                            {selected?.name || 'Select Agent'}
                        </Text>
                        <IconChevronDown size={14} color="#9ca3af" />
                    </UnstyledButton>
                </Popover.Target>
                <Popover.Dropdown>
                    <Stack gap={4}>
                        <Text size="xs" c="#9ca3af" fw={500} px="xs" py={4}>
                            SELECT AGENT
                        </Text>
                        {agents.map((agent) => {
                            const AgentIcon = agentIcons[agent.id] || IconSparkles
                            const agentColor = agentColors[agent.id] || '#6b7280'
                            const isSelected = agent.id === selectedAgent

                            return (
                                <UnstyledButton
                                    key={agent.id}
                                    onClick={() => {
                                        onAgentChange(agent.id)
                                        setOpened(false)
                                    }}
                                    style={{
                                        padding: '10px 12px',
                                        borderRadius: '6px',
                                        backgroundColor: isSelected ? '#374151' : 'transparent',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        cursor: 'pointer',
                                        transition: 'background-color 0.15s',
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!isSelected) {
                                            e.currentTarget.style.backgroundColor = '#2d3748'
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isSelected) {
                                            e.currentTarget.style.backgroundColor = 'transparent'
                                        }
                                    }}
                                >
                                    <Avatar size="sm" radius="sm" style={{ backgroundColor: agentColor }}>
                                        <AgentIcon size={16} color="white" />
                                    </Avatar>
                                    <div style={{ flex: 1 }}>
                                        <Group gap={6}>
                                            <Text size="sm" c="white" fw={500} style={{ lineHeight: 1 }}>
                                                {agent.name}
                                            </Text>
                                            {isSelected && (
                                                <Badge size="xs" variant="light" color="blue">
                                                    Active
                                                </Badge>
                                            )}
                                        </Group>
                                        <Text size="xs" c="#9ca3af" style={{ lineHeight: 1.3, marginTop: 4 }}>
                                            {agent.description}
                                        </Text>
                                    </div>
                                    <ActionIcon
                                        size="xs"
                                        variant="transparent"
                                        style={{ opacity: isSelected ? 1 : 0 }}
                                    >
                                        <div
                                            style={{
                                                width: 6,
                                                height: 6,
                                                borderRadius: '50%',
                                                backgroundColor: '#3b82f6',
                                            }}
                                        />
                                    </ActionIcon>
                                </UnstyledButton>
                            )
                        })}
                    </Stack>
                </Popover.Dropdown>
            </Popover>
        )
    }

    return null
}
