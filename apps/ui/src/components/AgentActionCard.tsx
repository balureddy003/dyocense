import { Box, Button, Heading, Text } from '@chakra-ui/react';

interface AgentActionCardProps {
    label: string;
    description?: string;
    actionType?: string;
    payload?: any;
    onAction?: () => void;
}

export default function AgentActionCard({ label, description, actionType, payload, onAction }: AgentActionCardProps) {
    const handleAction = onAction ?? (() => { });
    return (
        <Box borderWidth={1} borderRadius="lg" p={4} mb={3} bg="gray.50">
            <Heading size="sm" mb={2}>{label}</Heading>
            {description && <Text mb={2}>{description}</Text>}
            {actionType && <Text fontSize="xs" color="gray.500" mb={2}>Type: {actionType}</Text>}
            {payload && <Text fontSize="xs" color="gray.400" mb={2}>Payload: {JSON.stringify(payload)}</Text>}
            <Button colorScheme="blue" onClick={handleAction}>
                {label}
            </Button>
        </Box>
    );
}
