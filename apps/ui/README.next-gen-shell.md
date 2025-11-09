# Next-Gen Conversational UI Shell (Scaffold)

This scaffold sets up a modern, multi-tenant, workspace-aware conversational UI shell using the best open-source frameworks:

- **Next.js**: App shell, routing, SSR, and multi-tenant/workspace support
- **Chakra UI**: Modern, accessible UI components
- **Zustand**: Global state management (tenant, workspace, user)
- **Botpress Webchat** (or Rasa Webchat): Conversational chat UI and agent flows
- **LangChain.js**: Agent orchestration and GenAI integration

## Folder Structure

```
apps/ui/
  src/
    components/
      ChatShell.tsx         # Main conversational shell (chat + action cards)
      TenantWorkspaceNav.tsx # Tenant/workspace navigation
      AgentActionCard.tsx   # Modular action cards surfaced by agent
    context/
      useTenantWorkspace.ts # Zustand store for tenant/workspace/user
      useAgentContext.ts    # Agent context provider (LangChain.js)
    pages/
      _app.tsx              # Chakra UI provider, global state
      index.tsx             # Entry point, shell layout
      [tenant]/[workspace]/index.tsx # Dynamic routing for tenant/workspace
    lib/
      langchain/            # LangChain.js agent logic
      botpress/             # Botpress Webchat integration
  README.next-gen-shell.md  # This guide
```

## Getting Started

1. Install dependencies:
   - `next`, `chakra-ui`, `@chakra-ui/react`, `zustand`, `@langchain/langchain`, `botpress/webchat` (or `rasa-webchat`)
2. Scaffold pages and components as above.
3. Implement `useTenantWorkspace` for global context.
4. Integrate Botpress/Rasa Webchat in `ChatShell.tsx`.
5. Connect LangChain.js agent logic to chat UI and backend APIs.
6. Use Chakra UI for all cards, modals, and navigation.

## Example: Tenant/Workspace Routing

```tsx
// pages/[tenant]/[workspace]/index.tsx
import ChatShell from '../../components/ChatShell';
import TenantWorkspaceNav from '../../components/TenantWorkspaceNav';

export default function WorkspacePage() {
  return (
    <TenantWorkspaceNav />
    <ChatShell />
  );
}
```

## Example: Zustand Store

```ts
// context/useTenantWorkspace.ts
import create from 'zustand';

export const useTenantWorkspace = create((set) => ({
  tenant: null,
  workspace: null,
  user: null,
  setTenant: (tenant) => set({ tenant }),
  setWorkspace: (workspace) => set({ workspace }),
  setUser: (user) => set({ user }),
}));
```

## Example: ChatShell Integration

```tsx
// components/ChatShell.tsx
import { Webchat } from '@botpress/webchat';
import { useTenantWorkspace } from '../context/useTenantWorkspace';

export default function ChatShell() {
  const { tenant, workspace, user } = useTenantWorkspace();
  return (
    <Webchat
      botId="dyocense-agent"
      userId={user?.id}
      tenantId={tenant}
      workspaceId={workspace}
      // ...other props
    />
  );
}
```

---
*This scaffold enables rapid, innovative development of agentic SMB business tools with best-in-class open source frameworks.*
