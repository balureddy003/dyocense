import { ActionIcon, Group, ScrollArea, Stack, Text } from '@mantine/core'
import { IconMessage, IconTrash } from '@tabler/icons-react'
import { Conversation } from '../lib/conversations'
import { formatRelativeTime } from '../lib/time'

interface ConversationHistoryProps {
    conversations: Conversation[]
    currentConversationId?: string
    onSelectConversation: (conversation: Conversation) => void
    onDeleteConversation: (id: string) => void
    onNewConversation: () => void
}

export default function ConversationHistory({
    conversations,
    currentConversationId,
    onSelectConversation,
    onDeleteConversation,
    onNewConversation
}: ConversationHistoryProps) {
    if (conversations.length === 0) {
        return (
            <div style={{ padding: '12px' }}>
                <Text size="xs" c="dimmed" ta="center">
                    No conversation history yet
                </Text>
            </div>
        )
    }

    return (
        <ScrollArea style={{ maxHeight: 300 }}>
            <Stack gap={4} p="xs">
                {conversations.slice(0, 10).map((conv) => (
                    <div
                        key={conv.id}
                        style={{
                            padding: '8px 10px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            background: conv.id === currentConversationId ? '#e0e7ff' : 'transparent',
                            transition: 'background 0.15s ease',
                            position: 'relative'
                        }}
                        onMouseEnter={(e) => {
                            if (conv.id !== currentConversationId) {
                                e.currentTarget.style.background = '#f3f4f6'
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (conv.id !== currentConversationId) {
                                e.currentTarget.style.background = 'transparent'
                            }
                        }}
                        onClick={() => onSelectConversation(conv)}
                    >
                        <Group gap={8} wrap="nowrap">
                            <IconMessage size={14} style={{ flexShrink: 0 }} color="#6b7280" />
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <Text size="xs" fw={500} lineClamp={1} c="#202123">
                                    {conv.title}
                                </Text>
                                <Text size="10px" c="dimmed">
                                    {formatRelativeTime(conv.updatedAt)} • {conv.messages.length} msgs
                                </Text>
                            </div>
                            <ActionIcon
                                size="xs"
                                variant="subtle"
                                color="red"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    onDeleteConversation(conv.id)
                                }}
                            >
                                <IconTrash size={12} />
                            </ActionIcon>
                        </Group>
                    </div>
                ))}
            </Stack>
        </ScrollArea>
    )
}
