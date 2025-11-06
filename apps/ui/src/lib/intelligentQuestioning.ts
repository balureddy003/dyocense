import type { DataSource } from "../components/DataUploader";

export type Question = {
  id: string;
  text: string;
  category: "goal" | "data" | "metrics" | "timeline" | "constraints";
  reason: string;
  suggestedAnswers?: string[];
  required: boolean;
  answered?: boolean;
  answer?: string;
};

export type AnalysisContext = {
  goal?: string;
  businessType?: string;
  dataSources: DataSource[];
  existingMetrics?: string[];
  budget?: string;
  timeline?: string;
};

/**
 * Analyzes the current context and generates intelligent questions to fill gaps
 */
export function generateQuestions(context: AnalysisContext): Question[] {
  const questions: Question[] = [];

  // Goal clarity questions
  if (context.goal) {
    // Check if goal is SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
    if (!hasQuantifiableMetric(context.goal)) {
      questions.push({
        id: "goal-metric",
        text: "What specific number or percentage improvement do you want to achieve?",
        category: "goal",
        reason: "A measurable target helps track progress and determine success",
        suggestedAnswers: ["10% reduction", "15% increase", "20% improvement", "Custom amount"],
        required: true,
      });
    }

    if (!hasTimeframe(context.goal)) {
      questions.push({
        id: "goal-timeframe",
        text: "What is your target timeframe for achieving this goal?",
        category: "timeline",
        reason: "A deadline creates urgency and helps plan resources",
        suggestedAnswers: ["3 months", "6 months", "12 months", "Custom timeframe"],
        required: true,
      });
    }

    // Context-specific questions based on goal type
    if (context.goal.toLowerCase().includes("cost") || context.goal.toLowerCase().includes("reduce")) {
      questions.push({
        id: "baseline-cost",
        text: "What is your current monthly/annual cost for this area?",
        category: "metrics",
        reason: "Knowing the baseline helps validate if your target reduction is achievable",
        required: true,
      });
    }

    if (context.goal.toLowerCase().includes("revenue") || context.goal.toLowerCase().includes("sales")) {
      questions.push({
        id: "baseline-revenue",
        text: "What is your current monthly/annual revenue?",
        category: "metrics",
        reason: "This helps validate if your growth target is realistic and ambitious enough",
        required: true,
      });
    }

    if (context.goal.toLowerCase().includes("customer") || context.goal.toLowerCase().includes("satisfaction")) {
      questions.push({
        id: "current-satisfaction",
        text: "What is your current customer satisfaction score (e.g., NPS, CSAT)?",
        category: "metrics",
        reason: "Baseline satisfaction helps measure improvement and set realistic targets",
        required: true,
      });
    }
  }

  // Data availability questions
  if (context.dataSources.length === 0) {
    questions.push({
      id: "data-availability",
      text: "Do you have historical data about your operations (sales, costs, customer behavior)?",
      category: "data",
      reason: "Data helps create more accurate plans and baselines",
      suggestedAnswers: ["Yes, I can upload it", "Yes, it's in a system", "No, I'll need to start tracking"],
      required: false,
    });
  } else {
    // Analyze uploaded data for gaps
    const hasFinancialData = context.dataSources.some((s) =>
      s.metadata?.columns?.some((c) => /revenue|cost|profit|sales/i.test(c))
    );
    const hasCustomerData = context.dataSources.some((s) =>
      s.metadata?.columns?.some((c) => /customer|client|satisfaction|nps/i.test(c))
    );

    if (!hasFinancialData && (context.goal?.toLowerCase().includes("cost") || context.goal?.toLowerCase().includes("revenue"))) {
      questions.push({
        id: "missing-financial-data",
        text: "I don't see financial data (revenue, costs) in your uploads. Can you provide this?",
        category: "data",
        reason: "Financial data is crucial for validating cost reduction or revenue growth goals",
        required: true,
      });
    }

    if (!hasCustomerData && context.goal?.toLowerCase().includes("customer")) {
      questions.push({
        id: "missing-customer-data",
        text: "I don't see customer data in your uploads. Can you provide satisfaction scores or feedback?",
        category: "data",
        reason: "Customer data helps validate service improvement goals",
        required: false,
      });
    }
  }

  // Budget and resource questions
  if (!context.budget) {
    questions.push({
      id: "budget-available",
      text: "What budget do you have available for implementing this plan?",
      category: "constraints",
      reason: "Budget determines which solutions are feasible and helps prioritize activities",
      suggestedAnswers: ["<$10K", "$10K-$50K", "$50K-$100K", ">$100K"],
      required: true,
    });
  }

  // Team and capacity questions
  if (context.goal?.toLowerCase().includes("automat") || context.goal?.toLowerCase().includes("digital")) {
    questions.push({
      id: "technical-capacity",
      text: "Do you have technical staff or will you need external help for implementation?",
      category: "constraints",
      reason: "Implementation approach depends on available technical expertise",
      suggestedAnswers: ["Internal team available", "Need external consultants", "Will train existing staff"],
      required: true,
    });
  }

  // Market and competitive context
  if (context.businessType === "retail" || context.businessType === "ecommerce") {
    questions.push({
      id: "competitive-position",
      text: "How do your current metrics compare to competitors or industry benchmarks?",
      category: "metrics",
      reason: "Competitive context helps set ambitious but achievable targets",
      suggestedAnswers: ["Above average", "Average", "Below average", "Don't know"],
      required: false,
    });
  }

  return questions;
}

/**
 * Checks if goal contains quantifiable metrics
 */
function hasQuantifiableMetric(goal: string): boolean {
  const metricPatterns = [/\d+%/, /\d+x/, /\$\d+/, /by \d+/i, /to \d+/i];
  return metricPatterns.some((pattern) => pattern.test(goal));
}

/**
 * Checks if goal contains a timeframe
 */
function hasTimeframe(goal: string): boolean {
  const timePatterns = [
    /\d+\s*(month|months|quarter|quarters|year|years)/i,
    /by\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,
    /within/i,
  ];
  return timePatterns.some((pattern) => pattern.test(goal));
}

/**
 * Validates if an answer is sufficient
 */
export function validateAnswer(question: Question, answer: string): { valid: boolean; suggestion?: string } {
  if (!answer || answer.trim().length === 0) {
    return { valid: false, suggestion: "Please provide an answer to continue" };
  }

  if (question.category === "metrics") {
    // Check for numbers in metrics questions
    if (!/\d/.test(answer)) {
      return { valid: false, suggestion: "Please provide a specific number or percentage" };
    }
  }

  if (question.id === "baseline-cost" || question.id === "baseline-revenue") {
    // Validate reasonable financial numbers
    const match = answer.match(/\d+/);
    if (!match || parseInt(match[0]) < 0) {
      return { valid: false, suggestion: "Please provide a valid positive number" };
    }
  }

  return { valid: true };
}

/**
 * Generates follow-up questions based on answers
 */
export function generateFollowUpQuestions(question: Question, answer: string, context: AnalysisContext): Question[] {
  const followUps: Question[] = [];

  // If user said they have data but haven't uploaded it
  if (question.id === "data-availability" && answer.includes("Yes") && context.dataSources.length === 0) {
    followUps.push({
      id: "data-upload-prompt",
      text: "Great! Please upload your data files or connect to your data source so I can analyze them.",
      category: "data",
      reason: "Analyzing your actual data will make the plan much more accurate",
      required: true,
    });
  }

  // If user has low budget, suggest phased approach
  if (question.id === "budget-available" && answer.includes("<$10K")) {
    followUps.push({
      id: "phased-approach",
      text: "With this budget, would you prefer a phased approach starting with quick wins?",
      category: "constraints",
      reason: "Limited budget often means focusing on high-impact, low-cost activities first",
      suggestedAnswers: ["Yes, show me quick wins first", "No, show me the full plan"],
      required: false,
    });
  }

  // If baseline is provided, ask about target improvement
  if (question.id.includes("baseline-") && /\d+/.test(answer)) {
    const metric = question.id.replace("baseline-", "");
    followUps.push({
      id: `target-${metric}`,
      text: `What is your target ${metric} after achieving this goal?`,
      category: "metrics",
      reason: "Comparing baseline to target shows the gap we need to close",
      required: true,
    });
  }

  return followUps;
}

/**
 * Enriches a goal with SMART criteria based on answers
 */
export function enrichGoalWithAnswers(goal: string, answers: Map<string, string>): string {
  let enrichedGoal = goal;

  // Add metric if provided
  const metricAnswer = answers.get("goal-metric");
  if (metricAnswer && !hasQuantifiableMetric(enrichedGoal)) {
    enrichedGoal += ` by ${metricAnswer}`;
  }

  // Add timeframe if provided
  const timeframeAnswer = answers.get("goal-timeframe");
  if (timeframeAnswer && !hasTimeframe(enrichedGoal)) {
    enrichedGoal += ` within ${timeframeAnswer}`;
  }

  // Add baseline context if provided
  const baselineCost = answers.get("baseline-cost");
  const baselineRevenue = answers.get("baseline-revenue");
  if (baselineCost) {
    enrichedGoal += ` (current: ${baselineCost})`;
  } else if (baselineRevenue) {
    enrichedGoal += ` (current: ${baselineRevenue})`;
  }

  return enrichedGoal;
}
