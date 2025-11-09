
import { Box, Button, Input, Spinner, Text, VStack } from '@chakra-ui/react';
import axios from 'axios';
import React, { useState } from 'react';
import { useTenantWorkspace } from '../context/useTenantWorkspace';
import AgentActionCard from './AgentActionCard';

interface ActionItem {
    label: string;
    description?: string;
    action?: string;
    type?: string;
    actionType?: string;
    payload?: any;
    onAction?: () => void;
}

interface Message {
    sender: 'user' | 'agent';
    text: string;
    actions?: ActionItem[];
}

export default function ChatShell() {
    const { tenant, workspace, user } = useTenantWorkspace();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);

    const sendMessage = async (): Promise<void> => {
        if (!input.trim()) return;
        setMessages([...messages, { sender: 'user', text: input }]);
        setLoading(true);
        try {
            const res = await axios.post('/api/agent/message', {
                tenant_id: tenant,
                workspace_id: workspace,
                user_id: user?.id,
                message: input,
            });
            // Map backend actions to UI cards
            const actions = (res.data.actions || []).map((a: any) => ({
                label: a.label,
                description: a.description,
                actionType: a.type,
                payload: a.payload,
                onAction: () => {
                    if (a.type === 'analytics') {
                        alert('Opening analytics dashboard for workspace: ' + (a.payload?.workspace_id || ''));
                    } else if (a.type === 'workflow') {
                        alert('Triggering workflow for tenant: ' + (a.payload?.tenant_id || ''));
                    } else if (a.type === 'calculator') {
                        alert('Calculator result: ' + (a.payload?.expression || ''));
                    } else {
                        alert(`Action: ${a.action}`);
                    }
                }
            }));
            setMessages((prev: Message[]) => [...prev, { sender: 'agent', text: res.data.reply, actions }]);
        } catch (err) {
            setMessages((prev: Message[]) => [...prev, { sender: 'agent', text: 'Error: Unable to get agent response.' }]);
        }
        setInput('');
        setLoading(false);
    };

    return (
        <Box p={4} borderWidth={1} borderRadius="lg" w="100%" maxW="600px" mx="auto" bg="white">
            <VStack gap={3}>
                {messages.map((msg: Message, idx: number) => (
                    <React.Fragment key={"msg-" + idx}>
                        <Text textAlign={msg.sender === 'user' ? 'right' : 'left'} color={msg.sender === 'user' ? 'blue.600' : 'gray.800'}>
                            {msg.text}
                        </Text>
                        {msg.actions && msg.actions.map((a, i) => (
                            <AgentActionCard
                                key={"action-" + i}
                                label={a.label}
                                description={a.description}
                                actionType={a.actionType}
                                payload={a.payload}
                                onAction={a.onAction}
                            />
                        ))}
                    </React.Fragment>
                ))}
                {loading && <Spinner size="sm" />}
                <Box display="flex" gap={2}>
                    <Input
                        value={input}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
                        placeholder="Type your question..."
                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && sendMessage()}
                        disabled={loading}
                    />
                    <Button onClick={sendMessage} colorScheme="blue" disabled={loading || !input.trim()}>
                        Send
                    </Button>
                </Box>
            </VStack>
        </Box>
    );
}
