import { useEffect, useState } from "react";
import { getRuns } from "../lib/api";
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

export interface TripSummary {
  context: string;
  primaryKpis: { label: string; value: string }[];
  quickWins: string[];
}

export interface TripPlan {
  title: string;
  goal: string;
  summary: TripSummary;
  plan: PlanStage[];
  whatIfs: WhatIfScenario[];
  unscheduled: string[];
  notes: string[];
}

interface DyocenseRun {
  run_id: string;
  goal?: string;
  status?: string;
  result?: {
    solution?: {
      summary?: string;
      metadata?: Record<string, unknown>;
      kpis?: Record<string, number>;
    };
    explanation?: {
      summary?: string | string[];
      highlights?: string[];
      what_ifs?: string[];
    };
  };
}

function transformRuns(runs: DyocenseRun[]): TripPlan {
  if (!runs.length) return mockTrip;
  const latest = runs[0];
  const goal = latest.goal || mockTrip.goal;
  const summaryText =
    latest.result?.explanation?.summary || latest.result?.solution?.summary;
  const summary = Array.isArray(summaryText)
    ? summaryText.join(" ")
    : summaryText || mockTrip.summary.context;
  const highlights =
    latest.result?.explanation?.highlights && latest.result?.explanation?.highlights.length
      ? latest.result.explanation.highlights
      : mockTrip.summary.quickWins;

  const kpis = latest.result?.solution?.kpis || {};
  const primaryKpis = Object.entries(kpis).slice(0, 3).map(([label, value]) => ({
    label,
    value: typeof value === "number" ? value.toFixed(2) : String(value),
  }));

  return {
    title: mockTrip.title,
    goal,
    summary: {
      context: summary,
      primaryKpis: primaryKpis.length ? primaryKpis : mockTrip.summary.primaryKpis,
      quickWins: highlights,
    },
    plan: mockTrip.plan,
    whatIfs: mockTrip.whatIfs,
    unscheduled: mockTrip.unscheduled,
    notes: mockTrip.notes,
  };
}

export const useItinerary = () => {
  const [trip, setTrip] = useState<TripPlan>(mockTrip);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await getRuns<{ runs: DyocenseRun[] } | { items: DyocenseRun[] }>(
          { runs: [] }
        );
        const runs = "runs" in data ? data.runs ?? [] : data.items ?? [];
        if (isMounted) {
          setTrip(transformRuns(runs));
        }
      } catch (error) {
        console.warn("Using mock trip data due to error", error);
        if (isMounted) setTrip(mockTrip);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  return { trip, loading };
};
