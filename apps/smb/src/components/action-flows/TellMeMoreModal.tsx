/**
 * TellMeMoreModal - Contextual chat interface for asking questions about recommendations
 * 
 * Features:
 * - Pre-loaded context about the recommendation
 * - Chat interface with AI coach
 * - Quick questions (suggested prompts)
 * - Follow-up questions
 */

import {
    ActionIcon,
    Badge,
    Button,
    Card,
    Group,
    Loader,
    Modal,
    ScrollArea,
    Stack,
    Text,
    TextInput,
} from '@mantine/core';
import { IconSend, IconSparkles, IconUser } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import type { CoachRecommendation } from '../coach-v6/types';

interface TellMeMoreModalProps {
    opened: boolean;
    onClose: () => void;
    recommendation: CoachRecommendation | null;
}

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

/**
 * Quick question suggestions based on recommendation type
 */
function getQuickQuestions(recommendation: CoachRecommendation): string[] {
    const baseQuestions = [
        'What specific actions should I take first?',
        'How urgent is this issue?',
        'What are the potential risks if I ignore this?',
        'Can you explain the data behind this recommendation?',
    ];

    // Customize based on priority
    if (recommendation.priority === 'critical') {
        baseQuestions.unshift('What happens if I delay action?');
    }

    return baseQuestions;
}

/**
 * Generate initial context message from AI coach
 */
function generateInitialMessage(recommendation: CoachRecommendation): ChatMessage {
    return {
        id: 'initial',
        role: 'assistant',
        content: `I'm here to help you understand this recommendation better. "${recommendation.title}"

${recommendation.reasoning || recommendation.description}

Ask me anything about this situation, and I'll provide detailed guidance based on your business data.`,
        timestamp: new Date(),
    };
}

/**
 * Mock AI response generator
 * In production, this would call the actual coach API
 */
async function generateAIResponse(userMessage: string, recommendation: CoachRecommendation): Promise<string> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simple mock responses based on keywords
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('first') || lowerMessage.includes('start')) {
        return `Great question! Here's what I recommend doing first:

1. **Immediate action (Today)**: ${recommendation.actions[0]?.label || 'Review the situation'}
   
2. **This week**: Set up a system to monitor the key metrics involved
   
3. **Within 2 weeks**: Implement preventive measures to avoid this situation recurring

The most important thing is to start with the highest-impact action first, which is why I suggested "${recommendation.actions[0]?.label || 'taking action'}" as your primary next step.`;
    }

    if (lowerMessage.includes('urgent') || lowerMessage.includes('quickly')) {
        const urgencyLevel = recommendation.priority === 'critical' ? 'Very High' :
            recommendation.priority === 'important' ? 'Moderate' : 'Low';
        return `The urgency level for this recommendation is **${urgencyLevel}**.

${recommendation.priority === 'critical' ?
                'This requires immediate attention - ideally within the next 24-48 hours. Delaying could lead to serious consequences for your business operations.' :
                recommendation.priority === 'important' ?
                    'This should be addressed within the next week. While not an emergency, taking action soon will prevent the situation from escalating.' :
                    'This can be scheduled for the next 2-4 weeks. It\'s a good opportunity for improvement but not time-critical.'}

Would you like help creating an action plan to address this?`;
    }

    if (lowerMessage.includes('risk') || lowerMessage.includes('ignore') || lowerMessage.includes('delay')) {
        return `If this recommendation isn't addressed, here are the potential risks:

**Short-term (1-2 weeks):**
- The underlying issue will continue to worsen
- You may lose opportunities for early intervention
- Data shows the trend is already negative

**Medium-term (1-3 months):**
- The problem could compound and become more expensive to fix
- Your business health score may decline further
- You might face operational disruptions

**Long-term (3+ months):**
- Significant impact on profitability
- Potential cash flow challenges
- Competitive disadvantage

The good news is that acting now gives you the best outcome. Should I walk you through the specific steps?`;
    }

    if (lowerMessage.includes('data') || lowerMessage.includes('numbers') || lowerMessage.includes('metrics')) {
        return `This recommendation is based on analysis of your business data:

**Data points analyzed:**
- Recent transaction patterns (last 30 days)
- Historical trends (last 90 days)
- Industry benchmarks for businesses like yours
- Seasonal patterns in your business type

**Key findings:**
- Your current trajectory shows a concerning trend
- The data suggests action is needed to reverse this direction
- Similar businesses that addressed this proactively saw 25-40% improvement

Would you like to see a detailed breakdown of the specific metrics? I can show you charts and historical comparisons.`;
    }

    // Default response
    return `That's an interesting question. Based on the recommendation "${recommendation.title}", here's what I can tell you:

${recommendation.reasoning || recommendation.description}

The actions I've suggested are designed to directly address the root cause of this issue. Each action has a specific purpose:

${recommendation.actions.map((action, i) => `${i + 1}. **${action.label}** - This helps by providing immediate impact`).join('\n')}

Is there a specific aspect you'd like me to elaborate on?`;
}

export function TellMeMoreModal({
    opened,
    onClose,
    recommendation,
}: TellMeMoreModalProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const viewport = useRef<HTMLDivElement>(null);

    // Initialize chat when modal opens
    useEffect(() => {
        if (opened && recommendation && messages.length === 0) {
            setMessages([generateInitialMessage(recommendation)]);
        }
    }, [opened, recommendation]);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (viewport.current) {
            viewport.current.scrollTo({ top: viewport.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages]);

    // Reset on close
    const handleClose = () => {
        setMessages([]);
        setInputValue('');
        setIsLoading(false);
        onClose();
    };

    // Send user message
    const handleSendMessage = async () => {
        if (!inputValue.trim() || !recommendation || isLoading) return;

        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: inputValue,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const aiResponse = await generateAIResponse(inputValue, recommendation);
            const assistantMessage: ChatMessage = {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: aiResponse,
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error generating AI response:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Send quick question
    const handleQuickQuestion = (question: string) => {
        setInputValue(question);
    };

    if (!recommendation) return null;

    const quickQuestions = getQuickQuestions(recommendation);

    return (
        <Modal
            opened={opened}
            onClose={handleClose}
            title={
                <Group gap="xs">
                    <IconSparkles size={20} />
                    <Text>Ask Coach</Text>
                </Group>
            }
            size="lg"
            padding="md"
        >
            <Stack gap="md" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
                {/* Recommendation Context */}
                <Card withBorder padding="sm" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Group justify="space-between">
                        <Text size="sm" fw={600} lineClamp={1}>{recommendation.title}</Text>
                        <Badge size="sm" color={
                            recommendation.priority === 'critical' ? 'red' :
                                recommendation.priority === 'important' ? 'orange' : 'blue'
                        }>
                            {recommendation.priority}
                        </Badge>
                    </Group>
                </Card>

                {/* Chat Messages */}
                <ScrollArea
                    style={{ flex: 1 }}
                    viewportRef={viewport}
                    type="auto"
                >
                    <Stack gap="md" pr="sm">
                        {messages.map((message) => (
                            <Card
                                key={message.id}
                                padding="md"
                                withBorder={message.role === 'user'}
                                style={{
                                    backgroundColor: message.role === 'assistant' ? 'var(--mantine-color-gray-0)' : 'white',
                                    alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '85%',
                                }}
                            >
                                <Group gap="xs" mb="xs">
                                    {message.role === 'assistant' ? (
                                        <IconSparkles size={16} color="var(--mantine-color-blue-6)" />
                                    ) : (
                                        <IconUser size={16} color="var(--mantine-color-gray-6)" />
                                    )}
                                    <Text size="xs" fw={600} c="dimmed">
                                        {message.role === 'assistant' ? 'Coach' : 'You'}
                                    </Text>
                                </Group>
                                <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                                    {message.content}
                                </Text>
                            </Card>
                        ))}

                        {isLoading && (
                            <Card padding="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)', maxWidth: '85%' }}>
                                <Group gap="xs">
                                    <Loader size="xs" />
                                    <Text size="sm" c="dimmed">Coach is thinking...</Text>
                                </Group>
                            </Card>
                        )}
                    </Stack>
                </ScrollArea>

                {/* Quick Questions (show only if no messages yet) */}
                {messages.length === 1 && (
                    <Stack gap="xs">
                        <Text size="xs" fw={600} c="dimmed">Quick Questions:</Text>
                        <Group gap="xs">
                            {quickQuestions.slice(0, 3).map((question, index) => (
                                <Button
                                    key={index}
                                    size="xs"
                                    variant="light"
                                    onClick={() => handleQuickQuestion(question)}
                                >
                                    {question}
                                </Button>
                            ))}
                        </Group>
                    </Stack>
                )}

                {/* Input */}
                <Group gap="xs">
                    <TextInput
                        placeholder="Ask a question..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.currentTarget.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessage();
                            }
                        }}
                        style={{ flex: 1 }}
                        disabled={isLoading}
                    />
                    <ActionIcon
                        size="lg"
                        color="blue"
                        variant="filled"
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading}
                    >
                        <IconSend size={18} />
                    </ActionIcon>
                </Group>
            </Stack>
        </Modal>
    );
}
