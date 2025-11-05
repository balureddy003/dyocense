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
import { TrialBanner } from "../components/TrialBanner";
import { WelcomeModal } from "../components/WelcomeModal";
import { GettingStartedCard } from "../components/GettingStartedCard";
import { RecommendedPlaybooks } from "../components/RecommendedPlaybooks";
import { CreatePlaybookPayload, usePlaybook } from "../hooks/usePlaybook";
import { useAccount } from "../hooks/useAccount";
import { useAuth } from "../context/AuthContext";
import { BusinessMetrics } from "../components/BusinessMetrics";

export const HomePage = () => {
  const { playbook, runs, selectedRunId, loading, error, selectRun, createPlaybook } = usePlaybook();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "playbook">(runs.length ? "playbook" : "create");
  const [allowAutoSwitch, setAllowAutoSwitch] = useState(true);
  const { profile, projects, error: accountError, createProject, apiTokens, createApiToken, refreshApiTokens } = useAccount();
  const { user } = useAuth();
  const [tokenSecret, setTokenSecret] = useState<string | null>(null);
  const [tokenLoading, setTokenLoading] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [showWelcome, setShowWelcome] = useState(false);
  const [showGettingStarted, setShowGettingStarted] = useState(true);
  const [selectedArchetypeId, setSelectedArchetypeId] = useState<string | undefined>(undefined);

  // Check if user has seen the welcome modal
  useEffect(() => {
    if (user?.id && profile) {
      const hasSeenWelcome = localStorage.getItem(`dyocense-welcome-${user.id}`);
      if (!hasSeenWelcome) {
        setShowWelcome(true);
      }
    }
  }, [user?.id, profile]);

  // Check if user has created any playbooks
  useEffect(() => {
    if (runs.length > 0 || projects.length > 1) {
      setShowGettingStarted(false);
    }
  }, [runs.length, projects.length]);

  const handleCloseWelcome = () => {
    if (user?.id) {
      localStorage.setItem(`dyocense-welcome-${user.id}`, "true");
    }
    setShowWelcome(false);
  };

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
        <WelcomeModal
          open={showWelcome}
          onClose={handleCloseWelcome}
          companyName={profile?.name}
        />
        
        {/* Trial Banner - only if in trial */}
        {profile && profile.status === "trial" && (
          <div className="max-w-6xl mx-auto w-full px-6 pt-4">
            <TrialBanner
              status={profile.status}
              planTier={profile.plan.tier}
              trialEndsAt={profile.usage?.cycle_started_at ? new Date(new Date(profile.usage.cycle_started_at).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString() : null}
            />
          </div>
        )}

        {/* Business Metrics - simplified header */}
        {!showGettingStarted && (
          <div className="max-w-6xl mx-auto w-full px-6 pt-6">
            <BusinessMetrics />
          </div>
        )}

        {/* Recommended Templates */}
        {!showGettingStarted && profile && (
          <RecommendedPlaybooks
            onSelectPlaybook={(archetypeId) => {
              setSelectedArchetypeId(archetypeId);
              const createSection = document.querySelector('[data-create-playbook]');
              createSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }}
          />
        )}

        {/* Main Create Playbook Form */}
        <div data-create-playbook>
          <CreatePlaybook
            onSubmit={handleCreate}
            submitting={loading}
            projects={projects.map((project) => ({ project_id: project.project_id, name: project.name }))}
            initialArchetypeId={selectedArchetypeId}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg text-gray-900">
      <TopNav />
      <WelcomeModal
        open={showWelcome}
        onClose={handleCloseWelcome}
        companyName={profile?.name}
      />
      {profile && profile.status === "trial" && (
        <div className="px-6 pt-4">
          <TrialBanner
            status={profile.status}
            planTier={profile.plan.tier}
            trialEndsAt={profile.usage?.cycle_started_at ? new Date(new Date(profile.usage.cycle_started_at).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString() : null}
          />
        </div>
      )}
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
