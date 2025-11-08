import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AgentAssistant } from "../components/AgentAssistant";
import { BusinessMetrics } from "../components/BusinessMetrics";
import { CollapsiblePanel } from "../components/CollapsiblePanel";
import { CreatePlaybook } from "../components/CreatePlaybook";
import { ExecutionPanel } from "../components/ExecutionPanel";
import { MetricsPanel } from "../components/MetricsPanel";
import { PlanNameModal } from "../components/PlanNameModal";
import { PlanSelector, SavedPlan } from "../components/PlanSelector";
import { PlanVersionsSidebar } from "../components/PlanVersionsSidebar";
import { RecommendedPlaybooks } from "../components/RecommendedPlaybooks";
import { TopNav } from "../components/TopNav";
import { TrialBanner } from "../components/TrialBanner";
import { VersionComparisonModal } from "../components/VersionComparisonModal";
import { useAuth } from "../context/AuthContext";
import { useAccount } from "../hooks/useAccount";
import { CreatePlaybookPayload, usePlaybook } from "../hooks/usePlaybook";
import { clearActivePlan, deletePlan, getActivePlanId, getSavedPlans, savePlan, setActivePlanId } from "../lib/planPersistence";
import { tenantConnectorStore } from "../lib/tenantConnectors";
import { PlaybookResultsPage } from "./PlaybookResultsPage";

type PlanOverview = {
  title: string;
  summary: string;
  stages: Array<{
    id: string;
    title: string;
    description: string;
    todos: string[];
  }>;
  quickWins: string[];
  estimatedDuration: string;
  dataSources?: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
  }>;
};

export const HomePage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Current project context (tenant -> project -> plan hierarchy)
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const { playbook, runs, selectedRunId, loading, error, selectRun, createPlaybook } = usePlaybook(currentProjectId);
  const [mode, setMode] = useState<"create" | "results" | "agent" | "plan-selector">("plan-selector");
  const [allowAutoSwitch, setAllowAutoSwitch] = useState(true);
  const [lastCreatedPayload, setLastCreatedPayload] = useState<CreatePlaybookPayload | null>(null);
  const { profile, projects, createProject } = useAccount();
  const { user } = useAuth();
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>(undefined);
  const [generatedPlan, setGeneratedPlan] = useState<PlanOverview | null>(null);
  const [hasConnectors, setHasConnectors] = useState(false);
  const [forceAgentMode, setForceAgentMode] = useState(false);
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);
  const [savedPlans, setSavedPlans] = useState<SavedPlan[]>([]);
  const [currentPlanId, setCurrentPlanId] = useState<string | null>(null);
  const [showPlanNameModal, setShowPlanNameModal] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<PlanOverview | null>(null);
  const [showVersionsSidebar, setShowVersionsSidebar] = useState(false);
  // Header-only title when no plan exists yet
  const [unsavedPlanName, setUnsavedPlanName] = useState<string | undefined>(undefined);
  // Signal to reinitialize assistant and left panel for a fresh new plan flow
  const [newPlanSignal, setNewPlanSignal] = useState(0);
  // Seed goal passed from PlanSelector quick-start
  const [seedGoal, setSeedGoal] = useState<string | null>(null);
  // Version comparison state
  const [showVersionComparison, setShowVersionComparison] = useState(false);
  const [previousPlanVersion, setPreviousPlanVersion] = useState<SavedPlan | null>(null);
  const [newPlanVersion, setNewPlanVersion] = useState<SavedPlan | null>(null);

  // Memoize current project name to avoid repeated lookups
  const currentProjectName = useMemo(() => {
    return projects.find(p => p.project_id === currentProjectId)?.name;
  }, [projects, currentProjectId]);

  // Welcome modal removed - users get direct access after login
  // No need for additional welcome screens that interrupt workflow

  // Handle mode from URL parameter
  useEffect(() => {
    const modeParam = searchParams.get("mode");
    if (modeParam === "agent") {
      setMode("agent");
      setForceAgentMode(true);
    } else if (modeParam === "connectors") {
      // Open connectors view - you can add this mode or navigate to settings
      setMode("agent");
    }
  }, [searchParams]);

  // (moved up) currentProjectId state declared above to pass into usePlaybook

  // Initialise current project from storage or default to first project
  useEffect(() => {
    if (!profile?.tenant_id) return;
    const storageKey = `dyocense-active-project-${profile.tenant_id}`;
    const stored = localStorage.getItem(storageKey);
    const first = projects[0]?.project_id || null;
    const next = stored || first;
    if (next !== currentProjectId) {
      setCurrentProjectId(next);
    }
  }, [projects, profile?.tenant_id]);

  useEffect(() => {
    if (profile?.tenant_id && currentProjectId) {
      const key = `dyocense-active-project-${profile.tenant_id}`;
      localStorage.setItem(key, currentProjectId);
    }
  }, [currentProjectId, profile?.tenant_id]);

  // Load saved plans for current project
  useEffect(() => {
    if (profile?.tenant_id) {
      const plans = getSavedPlans(profile.tenant_id, currentProjectId);
      setSavedPlans(plans);

      // Check for active plan
      const activePlanId = getActivePlanId(profile.tenant_id, currentProjectId);
      if (activePlanId) {
        const activePlan = plans.find(p => p.id === activePlanId);
        if (activePlan) {
          setCurrentPlanId(activePlanId);
          setGeneratedPlan(activePlan);
          setMode("agent");
        } else {
          // Active plan not found, show selector
          setMode(plans.length > 0 ? "plan-selector" : "agent");
        }
      } else {
        // No active plan, show selector if plans exist
        setMode(plans.length > 0 ? "plan-selector" : "agent");
      }
    }
  }, [profile?.tenant_id, currentProjectId]);

  // Check if user has connectors
  useEffect(() => {
    if (profile?.tenant_id) {
      (async () => {
        try {
          const connectors = await tenantConnectorStore.getAll(profile.tenant_id);
          setHasConnectors(connectors.filter((c) => c.status === "active").length > 0);
        } catch (err) {
          console.warn("Failed to load connectors for hasConnectors check", err);
          setHasConnectors(false);
        }
      })();
    }
  }, [profile?.tenant_id]);

  // Handler functions for playbook creation and management
  const handleCreate = async (payload: CreatePlaybookPayload) => {
    setLastCreatedPayload(payload);
    await createPlaybook(payload);
    setMode("results");
    setAllowAutoSwitch(false);
  };

  const handleRegenerate = async (payload: CreatePlaybookPayload) => {
    setLastCreatedPayload(payload);
    await createPlaybook(payload);
  };

  const handleViewFullPlan = () => {
    setMode("agent");
  };

  const handlePlanGenerated = (plan: PlanOverview) => {
    // Always update the working plan view
    setGeneratedPlan(plan);

    if (!profile?.tenant_id) return;

    // If we already have a current plan, this is a modification → auto-increment version and show comparison
    if (currentPlanId) {
      const existingPlan = savedPlans.find((p) => p.id === currentPlanId);
      if (existingPlan) {
        const updatedPlan: SavedPlan = {
          ...existingPlan,
          ...plan,
          id: existingPlan.id,
          userProvidedName: existingPlan.userProvidedName, // Keep the user's chosen name
          version: existingPlan.version + 1,
          createdAt: existingPlan.createdAt,
          updatedAt: new Date().toISOString(),
        };

        // Store both versions for comparison
        setPreviousPlanVersion(existingPlan);
        setNewPlanVersion(updatedPlan);
        setShowVersionComparison(true);

        // Don't auto-save yet - let user decide via comparison modal
        return;
      }
    }

    // This is a brand new plan → decide whether to prompt for naming
    let shouldPrompt = true;
    const dismissedPending = sessionStorage.getItem(`dyocense-skip-name-pending-${profile.tenant_id}`) === "true";
    if (unsavedPlanName || dismissedPending) {
      shouldPrompt = false;
    }

    if (shouldPrompt) {
      setPendingPlan(plan);
      setShowPlanNameModal(true);
    } else {
      setPendingPlan(null);
      setShowPlanNameModal(false);
    }
  };

  const handleSavePlanName = (userProvidedName: string) => {
    if (!pendingPlan || !profile?.tenant_id) return;

    // Get existing plan if updating
    const existingPlan = currentPlanId ? savedPlans.find(p => p.id === currentPlanId) : null;

    const savedPlan: SavedPlan = {
      id: currentPlanId || `plan-${Date.now()}`,
      projectId: currentProjectId || undefined,
      ...pendingPlan,
      userProvidedName,
      version: existingPlan ? existingPlan.version + 1 : 1,
      createdAt: existingPlan?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    savePlan(profile.tenant_id, savedPlan, currentProjectId);
    setActivePlanId(profile.tenant_id, savedPlan.id, currentProjectId);
    setCurrentPlanId(savedPlan.id);
    // Ensure any previous "skip naming" suppression for this plan is cleared once it has a name
    try {
      localStorage.removeItem(`dyocense-skip-name-${profile.tenant_id}-${savedPlan.id}`);
      sessionStorage.removeItem(`dyocense-skip-name-pending-${profile.tenant_id}`);
    } catch { }

    // Refresh saved plans list
    const plans = getSavedPlans(profile.tenant_id, currentProjectId);
    setSavedPlans(plans);

    setPendingPlan(null);
    // Clear any unsaved header override once saved
    setUnsavedPlanName(undefined);
  };

  const handleSkipPlanName = () => {
    if (!pendingPlan || !profile?.tenant_id) return;

    // Save without user-provided name
    const existingPlan = currentPlanId ? savedPlans.find(p => p.id === currentPlanId) : null;

    const savedPlan: SavedPlan = {
      id: currentPlanId || `plan-${Date.now()}`,
      projectId: currentProjectId || undefined,
      ...pendingPlan,
      version: existingPlan ? existingPlan.version + 1 : 1,
      createdAt: existingPlan?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    savePlan(profile.tenant_id, savedPlan, currentProjectId);
    setActivePlanId(profile.tenant_id, savedPlan.id, currentProjectId);
    setCurrentPlanId(savedPlan.id);
    // Persist suppression so we don't re-open the name modal for this plan until the user actually names it
    try {
      localStorage.setItem(`dyocense-skip-name-${profile.tenant_id}-${savedPlan.id}`, "true");
      sessionStorage.removeItem(`dyocense-skip-name-pending-${profile.tenant_id}`);
    } catch { }

    // Refresh saved plans list
    const plans = getSavedPlans(profile.tenant_id, currentProjectId);
    setSavedPlans(plans);

    setPendingPlan(null);
    // Clear any unsaved header override once saved
    setUnsavedPlanName(undefined);
  };

  const handleUpdatePlanName = (newName: string) => {
    // Case 1: Editing a saved plan name
    if (currentPlanId && profile?.tenant_id) {
      const currentPlan = savedPlans.find(p => p.id === currentPlanId);
      if (!currentPlan) return;
      const updatedPlan: SavedPlan = {
        ...currentPlan,
        userProvidedName: newName,
        updatedAt: new Date().toISOString(),
      };
      savePlan(profile.tenant_id, updatedPlan, currentProjectId);
      const plans = getSavedPlans(profile.tenant_id, currentProjectId);
      setSavedPlans(plans);
      setGeneratedPlan(updatedPlan);
      return;
    }

    // Case 2: Editing a generated (unsaved) plan title
    if (generatedPlan) {
      setGeneratedPlan({ ...generatedPlan, title: newName });
      return;
    }

    // Case 3: No plan yet – just update header title
    setUnsavedPlanName(newName);
  };

  const handleKeepNewVersion = () => {
    if (!newPlanVersion || !profile?.tenant_id) return;

    savePlan(profile.tenant_id, newPlanVersion, currentProjectId);
    setActivePlanId(profile.tenant_id, newPlanVersion.id, currentProjectId);

    // Refresh saved plans list
    const plans = getSavedPlans(profile.tenant_id, currentProjectId);
    setSavedPlans(plans);

    // Update local state
    setGeneratedPlan(newPlanVersion);

    // Close modal
    setShowVersionComparison(false);
    setPreviousPlanVersion(null);
    setNewPlanVersion(null);
  };

  const handleReturnToPreviousVersion = () => {
    if (!previousPlanVersion) return;

    // Revert to previous version
    setGeneratedPlan(previousPlanVersion);

    // Close modal
    setShowVersionComparison(false);
    setPreviousPlanVersion(null);
    setNewPlanVersion(null);
  };

  const calculateChanges = () => {
    if (!previousPlanVersion || !newPlanVersion) {
      return { added: [], removed: [], modified: [] };
    }

    const changes: { added: string[]; removed: string[]; modified: string[] } = {
      added: [],
      removed: [],
      modified: [],
    };

    // Compare stages
    const prevStageIds = new Set(previousPlanVersion.stages.map(s => s.id));
    const newStageIds = new Set(newPlanVersion.stages.map(s => s.id));

    newPlanVersion.stages.forEach(stage => {
      if (!prevStageIds.has(stage.id)) {
        changes.added.push(`Added stage: ${stage.title}`);
      }
    });

    previousPlanVersion.stages.forEach(stage => {
      if (!newStageIds.has(stage.id)) {
        changes.removed.push(`Removed stage: ${stage.title}`);
      }
    });

    // Compare quick wins count
    if (newPlanVersion.quickWins.length !== previousPlanVersion.quickWins.length) {
      changes.modified.push(
        `Quick wins changed from ${previousPlanVersion.quickWins.length} to ${newPlanVersion.quickWins.length}`
      );
    }

    // Compare duration
    if (newPlanVersion.estimatedDuration !== previousPlanVersion.estimatedDuration) {
      changes.modified.push(
        `Duration changed from ${previousPlanVersion.estimatedDuration} to ${newPlanVersion.estimatedDuration}`
      );
    }

    return changes;
  };

  const handleSelectPlan = (plan: SavedPlan) => {
    setGeneratedPlan(plan);
    setCurrentPlanId(plan.id);
    if (profile?.tenant_id) {
      setActivePlanId(profile.tenant_id, plan.id, currentProjectId);
    }
    setMode("agent");
  };

  const handleCreateNewPlan = () => {
    setGeneratedPlan(null);
    setCurrentPlanId(null);
    setForceAgentMode(true);
    setUnsavedPlanName(undefined);
    if (profile?.tenant_id) {
      clearActivePlan(profile.tenant_id, currentProjectId);
      // Clear any pending name-modal suppression for a fresh plan flow
      try {
        sessionStorage.removeItem(`dyocense-skip-name-pending-${profile.tenant_id}`);
      } catch { }
    }
    setMode("agent");
    // Kick off assistant reset and ensure left panel re-mounts expanded
    setNewPlanSignal((s) => s + 1);

    // Reset the page to ensure clean state
    setTimeout(() => {
      window.scrollTo(0, 0);
    }, 100);
  };

  const handleDeletePlan = (planId: string) => {
    if (profile?.tenant_id) {
      deletePlan(profile.tenant_id, planId, currentProjectId);
      const plans = getSavedPlans(profile.tenant_id, currentProjectId);
      setSavedPlans(plans);

      // If deleting current plan, clear it
      if (planId === currentPlanId) {
        setGeneratedPlan(null);
        setCurrentPlanId(null);
        clearActivePlan(profile.tenant_id, currentProjectId);
      }
    }
  };

  useEffect(() => {
    if (allowAutoSwitch && runs.length && mode === "create" && !loading) {
      setMode("results");
      setAllowAutoSwitch(false);
    }
  }, [runs.length, mode, loading, allowAutoSwitch]);

  // Show plan selector
  if (mode === "plan-selector") {
    return (
      <>
        <TopNav
          projectOptions={projects.map((p) => ({ id: p.project_id, name: p.name }))}
          currentProjectId={currentProjectId}
          tenantName={profile?.name}
          showHierarchyBreadcrumb={true}
          onProjectChange={(id) => {
            setCurrentProjectId(id);
            setCurrentPlanId(null);
            if (profile?.tenant_id) clearActivePlan(profile.tenant_id, id);
          }}
          onCreateProject={async () => {
            const name = window.prompt("New project name?")?.trim();
            if (!name) return;
            const created = await createProject(name);
            if (created?.project_id) {
              setCurrentProjectId(created.project_id);
              setCurrentPlanId(null);
              if (profile?.tenant_id) clearActivePlan(profile.tenant_id, created.project_id);
            } else {
              window.alert("Failed to create project. Please try again.");
            }
          }}
        />
        <PlanSelector
          plans={savedPlans}
          onSelectPlan={handleSelectPlan}
          onCreateNew={handleCreateNewPlan}
          onDeletePlan={handleDeletePlan}
          currentProjectName={currentProjectName}
          tenantName={profile?.name}
          onStartWithGoal={(goal) => {
            setSeedGoal(goal);
            handleCreateNewPlan();
          }}
        />
      </>
    );
  }

  // Show results page after creating playbook
  if (mode === "results" && lastCreatedPayload) {
    return (
      <PlaybookResultsPage
        playbook={playbook}
        originalPayload={lastCreatedPayload}
        onRegenerate={handleRegenerate}
        onViewFullPlan={handleViewFullPlan}
        loading={loading}
      />
    );
  }

  if (mode === "create") {
    return (
      <div className="min-h-screen flex flex-col bg-bg text-gray-900">
        <TopNav
          projectOptions={projects.map((p) => ({ id: p.project_id, name: p.name }))}
          currentProjectId={currentProjectId}
          tenantName={profile?.name}
          showHierarchyBreadcrumb={true}
          onProjectChange={(id) => {
            setCurrentProjectId(id);
            setCurrentPlanId(null);
            if (profile?.tenant_id) clearActivePlan(profile.tenant_id, id);
          }}
          onCreateProject={async () => {
            const name = window.prompt("New project name?")?.trim();
            if (!name) return;
            const created = await createProject(name);
            if (created?.project_id) {
              setCurrentProjectId(created.project_id);
              setCurrentPlanId(null);
              if (profile?.tenant_id) clearActivePlan(profile.tenant_id, created.project_id);
            } else {
              window.alert("Failed to create project. Please try again.");
            }
          }}
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
        <div className="max-w-6xl mx-auto w-full px-6 pt-6">
          <BusinessMetrics />
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">Plan smarter in 3 steps: Describe your goal → Generate plan → Review & refine.</div>
            <button
              onClick={() => {
                const createSection = document.querySelector('[data-create-playbook]');
                createSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-primary px-3 py-2 text-primary font-medium hover:bg-blue-50"
            >
              Start a plan
            </button>
          </div>
        </div>

        {/* Recommended Templates */}
        {profile && (
          <RecommendedPlaybooks
            onSelectPlaybook={(templateId) => {
              setSelectedTemplateId(templateId);
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
            initialTemplateId={selectedTemplateId}
            initialProjectId={currentProjectId || projects[0]?.project_id}
          />
        </div>
      </div>
    );
  }

  // Agent-driven 3-panel view
  const currentPlan = currentPlanId ? savedPlans.find(p => p.id === currentPlanId) : null;

  return (
    <div className="min-h-screen flex flex-col bg-bg text-gray-900">
      {/* Unified Two-Level Header like Trip.com */}
      <TopNav
        showPlanControls={true}
        tenantName={profile?.name}
        showHierarchyBreadcrumb={true}
        planName={
          unsavedPlanName
          || (currentPlan ? (currentPlan.userProvidedName || currentPlan.title || "Untitled Plan")
            : (generatedPlan?.title || "AI Business Planner"))
        }
        planVersion={currentPlan?.version}
        planDraftKey={`dyocense-draft-planname-${profile?.tenant_id || 'anon'}-${currentPlanId || 'new'}`}
        projectOptions={projects.map((p) => ({ id: p.project_id, name: p.name }))}
        currentProjectId={currentProjectId}
        onProjectChange={(id) => {
          setCurrentProjectId(id);
          setCurrentPlanId(null);
          if (profile?.tenant_id) clearActivePlan(profile.tenant_id, id);
        }}
        onCreateProject={async () => {
          const name = window.prompt("New project name?")?.trim();
          if (!name) return;
          const created = await createProject(name);
          if (created?.project_id) {
            setCurrentProjectId(created.project_id);
            setCurrentPlanId(null);
            if (profile?.tenant_id) clearActivePlan(profile.tenant_id, created.project_id);
          } else {
            window.alert("Failed to create project. Please try again.");
          }
        }}
        dataSourcesConnected={currentPlan?.dataSources?.length || (hasConnectors ? 1 : 0)}
        onPlanNameChange={handleUpdatePlanName}
        onMenuClick={() => setShowVersionsSidebar(true)}
        onNewPlanClick={() => {
          setAllowAutoSwitch(false);
          handleCreateNewPlan();
        }}
        dataStatusPosition="left"
        steps={{
          goal: !!(generatedPlan || currentPlanId),
          generate: !!generatedPlan,
          refine: !!(currentPlan?.version && currentPlan.version > 1),
          save: !!(currentPlan?.userProvidedName),
        }}
      />

      <PlanNameModal
        open={showPlanNameModal}
        onClose={() => {
          // If we're in a new unsaved plan flow and the user closes the modal, suppress for this session
          if (!currentPlanId && profile?.tenant_id) {
            try {
              sessionStorage.setItem(`dyocense-skip-name-pending-${profile.tenant_id}`, "true");
            } catch { }
          }
          setShowPlanNameModal(false);
        }}
        onSave={handleSavePlanName}
        onSkip={handleSkipPlanName}
        currentName={currentPlanId ? savedPlans.find(p => p.id === currentPlanId)?.userProvidedName : undefined}
        aiGeneratedTitle={pendingPlan?.title}
        tenantName={profile?.name}
        projectName={currentProjectName}
      />

      {/* Version Comparison Modal */}
      {previousPlanVersion && newPlanVersion && (
        <VersionComparisonModal
          open={showVersionComparison}
          onClose={() => {
            setShowVersionComparison(false);
            setPreviousPlanVersion(null);
            setNewPlanVersion(null);
          }}
          onKeepNew={handleKeepNewVersion}
          onReturnToPrevious={handleReturnToPreviousVersion}
          previousVersion={previousPlanVersion}
          newVersion={newPlanVersion}
          changes={calculateChanges()}
          tenantName={profile?.name}
          projectName={currentProjectName}
        />
      )}

      {profile && profile.status === "trial" && (
        <div className="px-6 pt-4">
          <TrialBanner
            status={profile.status}
            planTier={profile.plan.tier}
            trialEndsAt={profile.usage?.cycle_started_at ? new Date(new Date(profile.usage.cycle_started_at).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString() : null}
          />
        </div>
      )}

      {/* Versions Sidebar */}
      <PlanVersionsSidebar
        open={showVersionsSidebar}
        onClose={() => setShowVersionsSidebar(false)}
        plans={savedPlans}
        currentPlanId={currentPlanId}
        onSelectPlan={handleSelectPlan}
        onCreateNew={handleCreateNewPlan}
        tenantName={profile?.name}
        projectName={currentProjectName}
      />

      {/* 3-Panel Layout with Collapsible Panels */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: AI Agent Assistant */}
        <CollapsiblePanel
          key={`left-${currentPlanId || 'new'}-${newPlanSignal}`}
          position="left"
          title="AI Assistant"
          defaultWidth="400px"
          minWidth="320px"
          maxWidth="600px"
          collapsible={true}
          resizable={true}
          defaultCollapsed={false}
          showFullscreenButton={true}
          onCollapseChange={setLeftPanelCollapsed}
        >
          {/* AI Agent Assistant */}
          <AgentAssistant
            key={`${currentPlanId || 'new-plan'}-${newPlanSignal}`}
            onPlanGenerated={handlePlanGenerated}
            profile={profile}
            projectId={currentProjectId}
            projectName={currentProjectName}
            seedGoal={seedGoal || undefined}
            startNewPlanSignal={newPlanSignal}
          />
        </CollapsiblePanel>

        {/* Middle: Execution Playbook (fills remaining space) */}
        <CollapsiblePanel
          position="center"
          title="Execution Plan"
          collapsible={false}
          resizable={false}
          showFullscreenButton={true}
        >
          <ExecutionPanel
            stages={generatedPlan?.stages || []}
            title={generatedPlan ? "Execution Plan" : "Your Plan"}
            estimatedDuration={generatedPlan?.estimatedDuration}
            hideHeader={true}
            tenantName={profile?.name}
            projectName={currentProjectName}
          />
        </CollapsiblePanel>

        {/* Right: KPIs & Evidence */}
        <CollapsiblePanel
          position="right"
          title="Metrics"
          defaultWidth="380px"
          minWidth="300px"
          maxWidth="500px"
          collapsible={true}
          resizable={true}
          defaultCollapsed={false}
          showFullscreenButton={true}
          onCollapseChange={setRightPanelCollapsed}
        >
          <MetricsPanel
            quickWins={generatedPlan?.quickWins}
            tenantName={profile?.name}
            projectName={currentProjectName}
          />
        </CollapsiblePanel>
      </div>
    </div>
  );
};
