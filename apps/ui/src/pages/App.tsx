import { useEffect, useState } from "react";
import { TopNav } from "../components/TopNav";
import { Header } from "../components/Header";
import { AssistantPanel } from "../components/AssistantPanel";
import { ItineraryColumn } from "../components/ItineraryColumn";
import { InsightsPanel } from "../components/InsightsPanel";
import { PlanDrawer } from "../components/PlanDrawer";
import { ExportModal } from "../components/ExportModal";
import { CreatePlaybook } from "../components/CreatePlaybook";
import { CreatePlaybookPayload, usePlaybook } from "../hooks/usePlaybook";

export default function App() {
  const {
    runs,
    selectedRunId,
    playbook,
    loading,
    createPlaybook,
    selectRun,
  } = usePlaybook();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "playbook">("create");

  const handleCreate = async (payload: CreatePlaybookPayload) => {
    await createPlaybook(payload);
    setMode("playbook");
  };

  useEffect(() => {
    if (mode === "create" && runs.length) {
      setMode("playbook");
    }
  }, [mode, runs.length]);

  if (mode === "create") {
    return (
      <div className="h-full flex flex-col bg-bg text-gray-900">
        <TopNav />
        <CreatePlaybook onSubmit={handleCreate} submitting={loading} />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-bg text-gray-900">
      <TopNav />
      <Header
        title={playbook.title}
        onOpenDrawer={() => setDrawerOpen(true)}
        onOpenExport={() => setExportOpen(true)}
        onNewPlaybook={() => setMode("create")}
      />
      <div className="flex flex-1 overflow-hidden">
        <AssistantPanel playbook={playbook} />
        <ItineraryColumn playbook={playbook} loading={loading} />
        <InsightsPanel playbook={playbook} />
      </div>
      <PlanDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        runs={runs}
        selectedRunId={selectedRunId}
        onSelect={selectRun}
        onCreateNew={() => setMode("create")}
      />
      <ExportModal open={exportOpen} onClose={() => setExportOpen(false)} playbook={playbook} />
    </div>
  );
}
