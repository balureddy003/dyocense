import { useEffect, useState } from "react";
import { TopNav } from "../components/TopNav";
import { Header } from "../components/Header";
import { AssistantPanel } from "../components/AssistantPanel";
import { ItineraryColumn } from "../components/ItineraryColumn";
import { InsightsPanel } from "../components/InsightsPanel";
import { PlanDrawer } from "../components/PlanDrawer";
import { ExportModal } from "../components/ExportModal";
import { CreatePlaybook } from "../components/CreatePlaybook";
import { InviteTeammateCard } from "../components/InviteTeammateCard";
import { CreatePlaybookPayload, usePlaybook } from "../hooks/usePlaybook";
import { useAccount } from "../hooks/useAccount";

export const HomePage = () => {
  const { playbook, runs, selectedRunId, loading, error, selectRun, createPlaybook } = usePlaybook();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "playbook">(runs.length ? "playbook" : "create");
  const [allowAutoSwitch, setAllowAutoSwitch] = useState(true);
  const { profile, projects, error: accountError, createProject, apiTokens, createApiToken, refreshApiTokens } = useAccount();
  const [tokenSecret, setTokenSecret] = useState<string | null>(null);
  const [tokenLoading, setTokenLoading] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);

  const handleCreate = async (payload: CreatePlaybookPayload) => {
    await createPlaybook(payload);
    setMode("playbook");
    setAllowAutoSwitch(false);
  };

  useEffect(() => {
    if (allowAutoSwitch && runs.length && mode === "create" && !loading) {
      setMode("playbook");
      setAllowAutoSwitch(false);
    }
  }, [runs.length, mode, loading, allowAutoSwitch]);

  if (mode === "create") {
    return (
      <div className="min-h-screen flex flex-col bg-bg text-gray-900">
        <TopNav />
        <div className="max-w-6xl mx-auto w-full px-6 pt-6 space-y-4">
          {profile && (
            <div className="rounded-2xl border border-blue-100 bg-white shadow-sm px-6 py-4 text-sm text-gray-700 flex flex-wrap items-center gap-3">
              <span className="text-primary font-semibold text-xs uppercase tracking-wide">Current plan</span>
              <span className="font-medium text-gray-900">{profile.plan.name}</span>
              <span className="text-gray-500">
                {profile.plan.limits.max_projects} projects · {profile.plan.limits.max_playbooks} playbooks · {profile.plan.limits.support_level} support
              </span>
            </div>
          )}
          {accountError && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {accountError}
            </div>
          )}
          <div className="rounded-2xl border border-gray-100 bg-white shadow-sm px-6 py-5 space-y-4">
            <header className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Developer access</p>
                <h2 className="text-sm font-semibold text-gray-900">User API tokens</h2>
              </div>
              <button
                className="text-xs text-primary font-semibold"
                onClick={() => {
                  setTokenError(null);
                  setTokenSecret(null);
                  setTokenLoading(true);
                  createApiToken(`Token ${apiTokens.length + 1}`)
                    .then((secret) => {
                      if (secret) {
                        setTokenSecret(secret);
                        refreshApiTokens().catch(() => undefined);
                      } else {
                        setTokenError("Unable to generate token.");
                      }
                    })
                    .catch((err: any) => {
                      setTokenError(err?.message || "Unable to generate token.");
                    })
                    .finally(() => setTokenLoading(false));
                }}
                disabled={tokenLoading}
              >
                {tokenLoading ? "Creating…" : "Generate new token"}
              </button>
            </header>
            {tokenError && <p className="text-xs text-red-500">{tokenError}</p>}
            {tokenSecret && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-700">
                <p className="font-semibold text-emerald-800">Copy your token secret</p>
                <p className="mt-1 break-all">{tokenSecret}</p>
              </div>
            )}
            <div className="space-y-2 text-xs text-gray-600">
              {apiTokens.length ? (
                apiTokens.map((token) => (
                  <div key={token.token_id} className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 bg-gray-50">
                    <span className="font-medium text-gray-800">{token.name}</span>
                    <span className="text-gray-400">{new Date(token.created_at).toLocaleString()}</span>
                  </div>
                ))
              ) : (
                <p className="text-gray-400">No user tokens yet. Generate one to automate API calls.</p>
              )}
            </div>
          </div>
          <InviteTeammateCard />
        </div>
        <CreatePlaybook
          onSubmit={handleCreate}
          submitting={loading}
          projects={projects.map((project) => ({ project_id: project.project_id, name: project.name }))}
          onCreateProject={async (name, description) => {
            const project = await createProject(name, description);
            return project ? { project_id: project.project_id, name: project.name } : null;
          }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg text-gray-900">
      <TopNav />
      <Header
        title={playbook.title}
        onOpenDrawer={() => setDrawerOpen(true)}
        onOpenExport={() => setExportOpen(true)}
        onNewPlaybook={() => {
          setAllowAutoSwitch(false);
          setMode("create");
        }}
      />
      <div className="flex flex-1 overflow-hidden">
        <AssistantPanel playbook={playbook} />
        <div className="flex flex-1 flex-col min-w-0">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 mx-6 mt-4 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}
          <ItineraryColumn playbook={playbook} loading={loading} />
        </div>
        <InsightsPanel playbook={playbook} />
      </div>
      <PlanDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        runs={runs}
        selectedRunId={selectedRunId}
        onSelect={selectRun}
        onCreateNew={() => {
          setDrawerOpen(false);
          setAllowAutoSwitch(false);
          setMode("create");
        }}
      />
      <ExportModal open={exportOpen} onClose={() => setExportOpen(false)} playbook={playbook} />
    </div>
  );
};
