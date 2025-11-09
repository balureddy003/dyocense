import { Box, Heading } from '@chakra-ui/react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import BotpressWebchat from '../../components/BotpressWebchat';
import ChatShell from '../../components/ChatShell';
import { useTenantWorkspace } from '../../context/useTenantWorkspace';

export default function WorkspacePage() {
    const router = useRouter();
    const { tenant, workspace } = router.query;
    const setTenant = useTenantWorkspace((s: any) => s.setTenant);
    const setWorkspace = useTenantWorkspace((s: any) => s.setWorkspace);

    useEffect(() => {
        if (typeof tenant === 'string') setTenant(tenant);
        if (typeof workspace === 'string') setWorkspace(workspace);
    }, [tenant, workspace, setTenant, setWorkspace]);

    return (
        <Box p={6}>
            <Heading size="md" mb={4}>
                Workspace: {workspace} (Tenant: {tenant})
            </Heading>
            <ChatShell />
            <BotpressWebchat botId="YOUR_BOTPRESS_BOT_ID" userId={typeof tenant === 'string' ? tenant : undefined} />
        </Box>
    );
}
