// Minimal stubbed goal-planning chat agent used to drive a "GenAI-first" flow in the UI.
// This is UI-only and deterministic. It extracts intent from user text and suggests
// clarifying questions. It can build a partial GoalRequest that the page can send to
// analyzeGoal().

import type { GoalRequest, ObjectiveWeights } from "./goalPlanner";

export type Role = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: Role;
  text: string;
  files?: Array<{ name: string; size: number; type?: string }>;
  at: number;
};

export type AgentContext = {
  goalText?: string;
  businessUnit?: string;
  markets?: string[];
  horizon?: { unit: "weeks" | "months"; value: number };
  objectives?: ObjectiveWeights;
  needsData?: string[]; // list of data gaps requested
};

export type AgentTurn = {
  assistant: ChatMessage;
  context: AgentContext;
};

const id = () => Math.random().toString(36).slice(2, 10);

function extractPercentage(text: string): number | undefined {
  const m = text.match(/(\d{1,2})(?:\s*)%/);
  if (!m) return undefined;
  const pct = parseInt(m[1], 10);
  if (isNaN(pct)) return undefined;
  return Math.min(95, Math.max(1, pct)) / 100;
}

function guessMarkets(text: string): string[] | undefined {
  const known = ["US", "EU", "UK", "IN", "APAC", "MEA"];
  const hits = known.filter((k) => new RegExp(`\\b${k}\\b`, "i").test(text));
  return hits.length ? hits : undefined;
}

/**
 * nextAgentTurn implements a tiny intent extractor:
 * - If user mentions "reduce inventory cost by X%", set goal and increase cost focus.
 * - If horizon not set, ask for horizon.
 * - If markets missing but mentioned in text, capture them.
 * - If files uploaded, acknowledge and clear needsData for those names.
 */
export function nextAgentTurn(messages: ChatMessage[], context: AgentContext): AgentTurn {
  // latest user message
  const last = [...messages].reverse().find((m) => m.role === "user");
  let ctx: AgentContext = { ...context };

  if (last) {
    // Extract a simple inventory-cost intent example
    if (/reduce\s+inventory\s+cost/i.test(last.text)) {
      const pct = extractPercentage(last.text) ?? 0.05;
      const markets = guessMarkets(last.text) ?? context.markets;
      ctx.goalText = `Reduce inventory cost by ${Math.round(pct * 100)}% without impacting quality`;
      ctx.objectives = { ...(context.objectives || {}), cost: 0.7 };
      if (markets) ctx.markets = markets;
    }

    // Capture simple horizon mentions
    const hm = last.text.match(/(\d{1,2})\s*(weeks|months)\b/i);
    if (hm) {
      ctx.horizon = { unit: hm[2].toLowerCase() as any, value: parseInt(hm[1], 10) };
    }

    // Business unit hint
    const bu = last.text.match(/for\s+my\s+([\w\-\s]+)\s+unit/i);
    if (bu) ctx.businessUnit = bu[1].trim();
  }

  // Determine next question
  const questions: string[] = [];
  if (!ctx.goalText) questions.push("What business outcome do you want to achieve?");
  if (!ctx.horizon) questions.push("What planning horizon should I use (e.g. 12 weeks or 6 months)?");
  if (!ctx.businessUnit) questions.push("Which business unit or store does this apply to?");
  if (!ctx.markets) questions.push("Which markets should we consider (e.g. EU, US)?");

  // Data gaps stub: ask for uploads when goal mentions suppliers or purchase orders
  const needs: string[] = [...(ctx.needsData || [])];
  const goal = (ctx.goalText || "").toLowerCase();
  if (/supplier|purchase|vendor/.test(goal) && !needs.includes("supplier_list.csv")) {
    needs.push("supplier_list.csv");
  }
  if (/inventory|stock/.test(goal) && !needs.includes("inventory_snapshot.csv")) {
    needs.push("inventory_snapshot.csv");
  }
  ctx.needsData = needs;

  const q = questions[0];
  const dataAsk = needs.length ? ` If you have them, upload: ${needs.join(", ")}.` : "";
  const assistantText = q
    ? `${q}${dataAsk}`
    : `Great. I can analyze now. Say "plan" to generate variants.${dataAsk}`;

  return {
    assistant: { id: id(), role: "assistant", text: assistantText, at: Date.now() },
    context: ctx,
  };
}

export function buildPartialRequest(ctx: AgentContext): Partial<GoalRequest> {
  const req: Partial<GoalRequest> = {
    goal_text: ctx.goalText || "",
    business_context: {
      business_unit_id: ctx.businessUnit,
      markets: ctx.markets,
    },
    horizon: ctx.horizon || { unit: "weeks", value: 12 },
    objectives: ctx.objectives,
  };
  return req;
}
