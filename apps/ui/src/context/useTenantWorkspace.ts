import create from 'zustand';

interface TenantWorkspaceState {
    tenant: string | null;
    workspace: string | null;
    user: { id: string; name?: string } | null;
    setTenant: (tenant: string) => void;
    setWorkspace: (workspace: string) => void;
    setUser: (user: { id: string; name?: string }) => void;
}

export const useTenantWorkspace = create<TenantWorkspaceState>((set) => ({
    tenant: null,
    workspace: null,
    user: null,
    setTenant: (tenant) => set({ tenant }),
    setWorkspace: (workspace) => set({ workspace }),
    setUser: (user) => set({ user }),
}));
