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
  storedAt?: string;
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

const parseDeltaText = (text: string): Record<string, string> => {
  const entries = text
    .split(/[,;\n]/)
    .map((piece) => piece.trim())
    .filter(Boolean);
  const delta: Record<string, string> = {};
  entries.forEach((entry) => {
    const parts = entry.split(/[:=]/);
    if (parts.length >= 2) {
      const key = parts[0].trim().replace(/\s+/g, "_").toLowerCase();
      const value = parts.slice(1).join(":").trim();
      if (key && value) {
        delta[key] = value;
      }
    }
  });
  return delta;
};

function mapWhatIfs(
  source?: Array<string | { title?: string; summary?: string; delta?: Record<string, unknown>; deltas?: Record<string, unknown>; delta_kpis?: Record<string, unknown> }>,
  fallback = FALLBACK_PLAYBOOK.whatIfs
): WhatIfScenario[] {
  if (!source || !source.length) return fallback;
  return source.map((item, index) => {
    if (typeof item === "string") {
      return {
        title: `Scenario ${index + 1}`,
        summary: item,
        delta: parseDeltaText(item),
      };
    }
    const summary = item.summary || "";
    const candidateDelta =
      item.delta || item.deltas || item.delta_kpis || (summary ? parseDeltaText(summary) : {});
    const normalisedDelta = Object.entries(candidateDelta || {}).reduce<Record<string, string>>(
      (acc, [key, value]) => {
        const label = key.replace(/[_-]+/g, " ");
        acc[label] = typeof value === "number" ? value.toFixed(2) : String(value);
        return acc;
      },
      {}
    );
    return {
      title: item.title || `Scenario ${index + 1}`,
      summary,
      delta: Object.keys(normalisedDelta).length ? normalisedDelta : parseDeltaText(summary),
    };
  });
}

function mapArtifacts(
  artifacts: Record<string, any> | undefined,
  defaults?: { stored_at?: string }
): EvidenceItem[] {
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
      storedAt: info.stored_at || defaults?.stored_at,
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
  const runHistory = buildHistory(run);
  const evidenceHistory: PlaybookHistoryEntry[] = evidence
    .filter((item) => item.storedAt)
    .map((item) => ({
      timestamp: item.storedAt as string,
      event: `Evidence captured: ${item.name}`,
      author: "Evidence service",
    }));
  const history = [...runHistory, ...evidenceHistory].sort((a, b) => {
    const aTime = new Date(a.timestamp).getTime();
    const bTime = new Date(b.timestamp).getTime();
    return bTime - aTime;
  });

  return {
    title: run.goal || FALLBACK_PLAYBOOK.title,
    goal: run.goal || FALLBACK_PLAYBOOK.goal,
    summary,
    plan: FALLBACK_PLAYBOOK.plan,
    whatIfs: mapWhatIfs(explanation?.what_ifs),
    unscheduled: FALLBACK_PLAYBOOK.unscheduled,
    notes: FALLBACK_PLAYBOOK.notes,
    itinerary: FALLBACK_PLAYBOOK.itinerary,
    history: history.length ? history : FALLBACK_PLAYBOOK.history,
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
          const evidenceResponse = await getEvidence<{
            artifacts?: Record<string, any>;
            stored_at?: string;
          }>(runId, { artifacts: {} });
          evidence = mapArtifacts(evidenceResponse.artifacts, {
            stored_at: (evidenceResponse as any).stored_at,
          });
        } catch (err) {
          console.warn("Falling back to list evidence", err);
          try {
            const listResponse = await listEvidence<{
              items?: Array<{ artifacts?: Record<string, any>; stored_at?: string; run_id?: string }>;
            }>({ items: [] });
            const matching = listResponse.items?.find((item: any) => item.run_id === runId);
            evidence = mapArtifacts(matching?.artifacts, { stored_at: matching?.stored_at });
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
