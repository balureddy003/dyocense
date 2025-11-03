import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createRun,
  getEvidence,
  getRun,
  listEvidence,
  listRuns,
} from "../lib/api";
import mockTrip from "../data/mockTrip.json";

export interface Activity {
  name: string;
  description: string;
  impact?: string;
}

export interface PlanStage {
  title: string;
  description: string;
  activities: Activity[];
}

export interface WhatIfScenario {
  title: string;
  summary: string;
  delta: Record<string, string>;
}

export interface PlaybookSummary {
  context: string;
  primaryKpis: { label: string; value: string }[];
  quickWins: string[];
}

export interface EvidenceItem {
  id: string;
  name: string;
  type: string;
  summary: string;
  link?: string;
}

export interface PlaybookHistoryEntry {
  timestamp: string;
  event: string;
  author: string;
}

export interface Playbook {
  title: string;
  goal: string;
  summary: PlaybookSummary;
  plan: PlanStage[];
  whatIfs: WhatIfScenario[];
  unscheduled: string[];
  notes: string[];
  itinerary: PlaybookStage[];
  history: PlaybookHistoryEntry[];
  evidence: EvidenceItem[];
}

export interface PlaybookStage {
  id: string;
  date: string;
  title: string;
  entries: string[];
}

export interface CreatePlaybookPayload {
  goal: string;
  horizon: number;
  archetype_id: string;
  project_id?: string;
  data_inputs?: Record<string, unknown>;
}

interface DyocenseRun {
  run_id: string;
  goal?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  result?: {
    solution?: {
      summary?: string | string[];
      metadata?: Record<string, unknown>;
      kpis?: Record<string, number>;
    };
    explanation?: {
      summary?: string | string[];
      highlights?: string[];
      what_ifs?: Array<string | { title?: string; summary?: string }>;
    };
  };
}

interface DyocenseRunListResponse {
  runs?: DyocenseRun[];
  items?: DyocenseRun[];
}

const FALLBACK_PLAYBOOK = mockTrip as Playbook;

const FALLBACK_RUN: DyocenseRun = {
  run_id: "mock-run",
  goal: FALLBACK_PLAYBOOK.goal,
};

function normaliseSummary(summary?: string | string[]): string {
  if (!summary) return "";
  return Array.isArray(summary) ? summary.join(" ") : summary;
}

function formatKpis(kpis?: Record<string, number>, fallback = FALLBACK_PLAYBOOK.summary.primaryKpis) {
  if (!kpis || !Object.keys(kpis).length) return fallback;
  return Object.entries(kpis)
    .slice(0, 3)
    .map(([label, value]) => ({
      label,
      value: typeof value === "number" ? value.toFixed(2) : String(value),
    }));
}

function mapWhatIfs(
  source?: Array<string | { title?: string; summary?: string }>,
  fallback = FALLBACK_PLAYBOOK.whatIfs
): WhatIfScenario[] {
  if (!source || !source.length) return fallback;
  return source.map((item, index) => {
    if (typeof item === "string") {
      return {
        title: `Scenario ${index + 1}`,
        summary: item,
        delta: {},
      };
    }
    return {
      title: item.title || `Scenario ${index + 1}`,
      summary: item.summary || "",
      delta: {},
    };
  });
}

function mapArtifacts(artifacts: Record<string, any> | undefined): EvidenceItem[] {
  if (!artifacts) return [];
  return Object.entries(artifacts).map(([key, value]) => {
    const info = value ?? {};
    const link = info.path || info.uri || undefined;
    return {
      id: key,
      name: info.name || key,
      type: info.type || info.format || "artifact",
      summary: info.description || info.summary || "Artifact captured for this run.",
      link,
    };
  });
}

function buildHistory(run: DyocenseRun): PlaybookHistoryEntry[] {
  const entries: PlaybookHistoryEntry[] = [];
  if (run.created_at) {
    entries.push({
      timestamp: run.created_at,
      event: "Playbook created",
      author: "Dyocense",
    });
  }
  if (run.updated_at && run.updated_at !== run.created_at) {
    entries.push({
      timestamp: run.updated_at,
      event: `Status: ${run.status ?? "updated"}`,
      author: "Dyocense",
    });
  }
  return entries.length ? entries : FALLBACK_PLAYBOOK.history;
}

function composePlaybook(run: DyocenseRun | null, evidenceItems: EvidenceItem[]): Playbook {
  if (!run) {
    return FALLBACK_PLAYBOOK;
  }
  const explanation = run.result?.explanation;
  const solution = run.result?.solution;

  const summaryText = normaliseSummary(explanation?.summary || solution?.summary);
  const summary: PlaybookSummary = {
    context: summaryText || FALLBACK_PLAYBOOK.summary.context,
    primaryKpis: formatKpis(solution?.kpis),
    quickWins:
      explanation?.highlights && explanation.highlights.length
        ? explanation.highlights
        : FALLBACK_PLAYBOOK.summary.quickWins,
  };

  const evidence = evidenceItems.length ? evidenceItems : FALLBACK_PLAYBOOK.evidence;

  return {
    title: run.goal || FALLBACK_PLAYBOOK.title,
    goal: run.goal || FALLBACK_PLAYBOOK.goal,
    summary,
    plan: FALLBACK_PLAYBOOK.plan,
    whatIfs: mapWhatIfs(explanation?.what_ifs),
    unscheduled: FALLBACK_PLAYBOOK.unscheduled,
    notes: FALLBACK_PLAYBOOK.notes,
    itinerary: FALLBACK_PLAYBOOK.itinerary,
    history: buildHistory(run),
    evidence,
  };
}

export interface RunSummary {
  id: string;
  goal: string;
  status: string;
  updatedAt?: string;
}

export const usePlaybook = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [playbook, setPlaybook] = useState<Playbook>(FALLBACK_PLAYBOOK);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = useCallback(async () => {
    try {
      const response = await listRuns<DyocenseRunListResponse>({ runs: [] });
      const data = response.runs ?? response.items ?? [];
      if (!data.length) {
        setRuns([
          {
            id: FALLBACK_RUN.run_id,
            goal: FALLBACK_PLAYBOOK.goal,
            status: "mock",
          },
        ]);
        setSelectedRunId(FALLBACK_RUN.run_id);
        return;
      }
      const summaries = data.map((run) => ({
        id: run.run_id,
        goal: run.goal || "Untitled playbook",
        status: run.status || "unknown",
        updatedAt: run.updated_at || run.created_at,
      }));
      setRuns(summaries);
      setSelectedRunId((prev) => prev ?? summaries[0]?.id ?? null);
    } catch (err) {
      console.warn("Falling back to mock runs", err);
      setRuns([
        {
          id: FALLBACK_RUN.run_id,
          goal: FALLBACK_PLAYBOOK.goal,
          status: "mock",
        },
      ]);
      setSelectedRunId(FALLBACK_RUN.run_id);
    }
  }, []);

  const loadPlaybook = useCallback(
    async (runId: string) => {
      setLoading(true);
      setError(null);
      try {
        const run = await getRun<DyocenseRun>(runId, FALLBACK_RUN);
        let evidence: EvidenceItem[] = [];
        try {
          const evidenceResponse = await getEvidence<{ artifacts?: Record<string, any> }>(
            runId,
            { artifacts: {} }
          );
          evidence = mapArtifacts(evidenceResponse.artifacts);
        } catch (err) {
          console.warn("Falling back to list evidence", err);
          try {
            const listResponse = await listEvidence<{ items?: Array<{ artifacts?: Record<string, any> }> }>(
              { items: [] }
            );
            const matching = listResponse.items?.find((item: any) => item.run_id === runId);
            evidence = mapArtifacts(matching?.artifacts);
          } catch (e) {
            console.warn("Evidence fallback failed", e);
            evidence = [];
          }
        }
        setPlaybook(composePlaybook(run, evidence));
      } catch (err: any) {
        console.warn("Failed to load run detail", err);
        setError(err?.message || "Failed to load playbook");
        setPlaybook(FALLBACK_PLAYBOOK);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    refreshRuns();
  }, [refreshRuns]);

  useEffect(() => {
    if (selectedRunId) {
      loadPlaybook(selectedRunId);
    }
  }, [selectedRunId, loadPlaybook]);

  const createPlaybook = useCallback(
    async (payload: CreatePlaybookPayload) => {
      setLoading(true);
      setError(null);
      try {
        const response = await createRun<{ run_id?: string }>(payload, { run_id: FALLBACK_RUN.run_id });
        await refreshRuns();
        if (response.run_id) {
          setSelectedRunId(response.run_id);
        }
      } catch (err: any) {
        console.warn("Failed to create run, using mock", err);
        setSelectedRunId(FALLBACK_RUN.run_id);
      } finally {
        setLoading(false);
      }
    },
    [refreshRuns]
  );

  const selectRun = useCallback((runId: string) => {
    setSelectedRunId(runId);
  }, []);

  return {
    runs,
    selectedRunId,
    playbook,
    loading,
    error,
    refreshRuns,
    selectRun,
    createPlaybook,
  };
};
