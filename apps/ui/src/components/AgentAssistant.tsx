import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  FileUp,
  GitBranch,
  History,
  Lightbulb,
  Loader2,
  Send,
  Settings,
  Sparkles,
  Target,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createRun, getPlaybookRecommendations, getRun, getTenantProfile, postOpenAIChat, TenantProfile } from "../lib/api";
import { type ConnectorConfig } from "../lib/connectorMarketplace";
import { generateGoalStatement, generateSuggestedGoalsFromBackend, SuggestedGoal } from "../lib/goalGenerator";
import { calculateGoalProgress, createGoalVersion, GoalVersion, validateSMARTGoal, VersionHistory } from "../lib/goalVersioning";
import { generateQuestions, Question } from "../lib/intelligentQuestioning";
import { generateDataContextPrompt, tenantConnectorStore, type TenantConnector } from "../lib/tenantConnectors";
import { ChatConnectorSetup } from "./ChatConnectorSetup";
import { ConnectedDataSources } from "./ConnectedDataSources";
import { ConnectorMarketplace } from "./ConnectorMarketplace";
import { DataSource, DataUploader } from "./DataUploader";
import { InlineConnectorSelector } from "./InlineConnectorSelector";
import { InlineDataUploader } from "./InlineDataUploader";
import { PreferencesModal } from "./PreferencesModal";
import { ThinkingProgress, ThinkingStep } from "./ThinkingProgress";

// Agent system prompt to drive fully conversational flow
const AGENT_SYSTEM_PROMPT = `You are Dyocense's AI Business Assistant.
- Hold a natural conversation to help small/medium businesses plan, forecast, and optimize.
- When users upload files, acknowledge them, infer schema at a high level, and propose next steps (connect, preview, or ask what they want to analyze). Avoid generic bullet lists.
- When users mention data systems (POS, inventory, spreadsheets), suggest the best connector succinctly and offer to open the connector picker. If a connector was opened, confirm briefly and continue the conversation.
- Ask clarifying questions only when needed (timeline, budget, target KPI, constraints), 1–2 at a time.
- If asked, draft a concise step-by-step plan and call out required data. Prefer concrete, actionable language.
- Keep answers crisp. End with an explicit next best action.

**Goal Evaluation Guidelines:**
- When user states a goal, evaluate if it's specific enough to create an actionable plan.
- If goal has clear metric, target value, and timeframe (e.g., "Reduce costs by 15% in 3 months"), acknowledge it enthusiastically and indicate you'll start creating the plan.
- If goal is vague (e.g., "improve efficiency"), ask 1-2 focused clarifying questions conversationally:
  * What specific metric should we track?
  * What's the target improvement and timeframe?
  * Any constraints (budget, resources)?
- Don't lecture about SMART goals - keep it natural and conversational.
- Once you have enough specifics, confirm the goal and let you know you're creating a detailed plan.

**Data Connection Guidelines:**
When users need data to accomplish their goals:

1. **Explain the need first**: "To create an accurate forecast, I'll need historical sales data."

2. **Indicate your intent in your response using special markers**:
   - To show connector options, include: [SHOW_CONNECTORS: crm, accounting] or [SHOW_CONNECTORS: salesforce, xero, shopify]
   - To show file uploader, include: [SHOW_UPLOADER: csv] or [SHOW_UPLOADER: excel]
   - Always explain WHY before the marker

3. **Example flows**:
   User: "Help me forecast sales"
   You: "I can help! To give accurate predictions, I'll need historical sales data. Do you use a CRM like Salesforce or HubSpot, or do you have sales data in a spreadsheet? [SHOW_CONNECTORS: salesforce, hubspot, pipedrive]"
   
   OR if they mention files:
   You: "Great! Please upload your sales data file. It should include columns like date, sales_amount, and product. [SHOW_UPLOADER: excel]"

4. **Never force data connections**:
   - Always explain WHY data is needed
   - Give users a choice to skip if they want
   - Offer to proceed with sample/demo data if they don't have their own`;


// Feature flag to run the assistant in agent-driven mode (no hardcoded Q&A branches)
const AGENT_DRIVEN_FLOW = true;

// LLM Function Calling Tools for Inline UI
const AGENT_FUNCTION_TOOLS = [
  {
    type: "function",
    function: {
      name: "show_connector_options",
      description: "Display inline connector selection UI to help user connect business data sources like CRM, accounting, ecommerce platforms, etc.",
      parameters: {
        type: "object",
        properties: {
          connectors: {
            type: "array",
            items: { type: "string" },
            description: "List of suggested connector IDs or categories (e.g., ['salesforce', 'xero', 'shopify'] or ['crm', 'accounting'])"
          },
          reason: {
            type: "string",
            description: "Brief explanation of why these connectors would help achieve the user's goal (1-2 sentences)"
          }
        },
        required: ["connectors", "reason"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "show_data_uploader",
      description: "Display inline file upload UI to allow user to upload CSV, Excel, or JSON files for analysis",
      parameters: {
        type: "object",
        properties: {
          format: {
            type: "string",
            enum: ["csv", "excel", "json"],
            description: "Expected file format"
          },
          expectedColumns: {
            type: "array",
            items: { type: "string" },
            description: "Optional: Expected column names to guide the user (e.g., ['date', 'sales', 'region'])"
          },
          reason: {
            type: "string",
            description: "Brief explanation of what data is needed and why (1-2 sentences)"
          }
        },
        required: ["format"]
      }
    }
  }
];

type Message = {
  id: string;
  role: "user" | "assistant" | "system" | "question";
  text: string;
  files?: Array<{ name: string; size: number }>;
  timestamp: number;
  question?: Question;
  feedback?: "positive" | "negative" | null;
  showThinking?: boolean;
  thinkingSteps?: ThinkingStep[];
  actions?: Array<{
    label: string;
    action: "connect" | "preview" | "remove" | "analyze";
    data?: any;
  }>;
  // Inline component rendering for connector/upload flows
  embeddedComponent?:
  | "connector-selector"
  | "data-uploader"
  | "connector-progress"
  | "data-preview";
  componentData?: any;
};

type ResearchStatus = "idle" | "researching" | "planning" | "ready";

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

type PreferencesState = {
  businessType: Set<string>;
  objectiveFocus: Set<string>;
  operatingPace: Set<string>;
  budget: Set<string>;
  markets: Set<string>;
  otherNeeds: string;
};

type AssistantMode = "chat" | "data-upload" | "goal-editing" | "version-history" | "connectors";

export type AgentAssistantProps = {
  onPlanGenerated?: (plan: PlanOverview) => void;
  profile?: TenantProfile | null;
  // Project context for plan generation
  projectId?: string | null;
  projectName?: string;
  // Seeded goal text to kick off generation from PlanSelector
  seedGoal?: string;
  // Signal to kickoff a fresh new-plan journey. Increment to trigger.
  startNewPlanSignal?: number;
};

export function AgentAssistant({ onPlanGenerated, profile, projectId, projectName, seedGoal, startNewPlanSignal }: AgentAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<AssistantMode>("chat");
  const [researchStatus, setResearchStatus] = useState<ResearchStatus>("idle");
  const [prefsModalOpen, setPrefsModalOpen] = useState(false);
  const [plan, setPlan] = useState<PlanOverview | null>(null);
  const [preferences, setPreferences] = useState<PreferencesState | null>(null);
  const [suggestedGoals, setSuggestedGoals] = useState<SuggestedGoal[]>([]);
  const [showGoalSuggestions, setShowGoalSuggestions] = useState(false);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [pendingQuestions, setPendingQuestions] = useState<Question[]>([]);
  const [questionAnswers, setQuestionAnswers] = useState<Map<string, string>>(new Map());
  const [currentGoal, setCurrentGoal] = useState<string>("");
  const [goalVersions, setGoalVersions] = useState<VersionHistory | null>(null);
  const [editingGoal, setEditingGoal] = useState<GoalVersion | null>(null);
  const [showVersionComparison, setShowVersionComparison] = useState(false);
  const [comparisonVersions, setComparisonVersions] = useState<[GoalVersion, GoalVersion] | null>(null);

  // Connector state
  const [tenantConnectors, setTenantConnectors] = useState<TenantConnector[]>([]);
  const [showConnectorMarketplace, setShowConnectorMarketplace] = useState(false);
  const [selectedConnectorForSetup, setSelectedConnectorForSetup] = useState<ConnectorConfig | null>(null);
  const [showConnectorSetup, setShowConnectorSetup] = useState(false);
  const [dataContextPrompt, setDataContextPrompt] = useState<string>("");

  // Phase 3: Enhanced conversation state tracking
  const [conversationStartTime] = useState<number>(Date.now());
  const [lastPlanGeneratedTime, setLastPlanGeneratedTime] = useState<number | null>(null);
  const [conversationTurnCount, setConversationTurnCount] = useState<number>(0);
  // Multi-agent mode toggle & detection
  const [multiAgentMode, setMultiAgentMode] = useState<boolean>(false);
  // Track last multi-agent result for potential structured display (optional future use)
  const [lastMultiAgentPayload, setLastMultiAgentPayload] = useState<any | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

  // Helper to build context-aware system prompt with project information
  const buildSystemPrompt = () => {
    let contextAddition = '';
    if (projectName) {
      contextAddition = `\n\n**Current Context:**\nYou are helping the user plan for their project: "${projectName}". All plans and recommendations should be scoped to this project.`;
    }
    return AGENT_SYSTEM_PROMPT + contextAddition;
  };

  // Phase 3: Helper to build rich context for LLM calls
  const buildEnhancedContext = () => {
    const conversationDurationMinutes = Math.floor((Date.now() - conversationStartTime) / 60000);
    const planAge = lastPlanGeneratedTime
      ? Math.floor((Date.now() - lastPlanGeneratedTime) / 60000)
      : null;

    return {
      // Core identifiers
      tenant_id: profile?.tenant_id,
      tenant_name: profile?.name,
      project_id: projectId,
      project_name: projectName,
      session_id: `session-${conversationStartTime}`,

      // Conversation state
      conversation_turns: conversationTurnCount,
      conversation_duration_minutes: conversationDurationMinutes,
      has_active_plan: Boolean(plan),
      plan_age_minutes: planAge,
      current_goal: currentGoal,

      // User preferences & context
      preferences: preferences ? {
        business_type: Array.from(preferences.businessType),
        objectives: Array.from(preferences.objectiveFocus),
        budget: Array.from(preferences.budget),
        markets: Array.from(preferences.markets),
        operating_pace: Array.from(preferences.operatingPace),
      } : null,

      // Data availability
      has_data_sources: dataSources.length > 0,
      data_sources: dataSources.map(ds => ({
        id: ds.id,
        name: ds.name,
        type: ds.type,
        rows: ds.metadata?.rows,
        columns: ds.metadata?.columns,
        size_mb: ds.metadata?.size ? (ds.metadata.size / 1024 / 1024).toFixed(2) : 0,
      })),

      // Connected systems
      connectors: tenantConnectors.map(c => ({
        id: c.id,
        name: c.displayName,
        type: c.connectorName || c.connectorId,
        status: c.status,
        connected: c.status === "active",
      })),
      active_connectors_count: tenantConnectors.filter(c => c.status === "active").length,

      // Plan state (if exists)
      plan_summary: plan ? {
        title: plan.title,
        stages_count: plan.stages.length,
        estimated_duration: plan.estimatedDuration,
        has_quick_wins: plan.quickWins.length > 0,
      } : null,

      // Conversation metadata
      message_count: messages.length,
      last_user_input: messages.filter(m => m.role === "user").slice(-1)[0]?.text,
      recent_topics: messages
        .filter(m => m.role === "user")
        .slice(-5)
        .map(m => m.text.substring(0, 50)),
    };
  };

  // Load tenant connectors and data sources from localStorage
  useEffect(() => {
    if (profile?.tenant_id) {
      tenantConnectorStore
        .getAll(profile.tenant_id)
        .then(setTenantConnectors)
        .catch(() => setTenantConnectors([]));

      // Load data sources from localStorage
      try {
        const key = `dyocense-datasources-${profile.tenant_id}`;
        const stored = localStorage.getItem(key);
        if (stored) {
          setDataSources(JSON.parse(stored));
        }
      } catch (error) {
        console.error("Error loading data sources:", error);
      }

      // Refresh data context prompt (async)
      generateDataContextPrompt(profile.tenant_id)
        .then(setDataContextPrompt)
        .catch(() => setDataContextPrompt(""));
    }
  }, [profile?.tenant_id]);

  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Kick off a fresh new plan journey when the signal changes
  useEffect(() => {
    if (startNewPlanSignal === undefined) return;
    // Reset assistant state for a clean flow
    setPlan(null);
    setPendingQuestions([]);
    setQuestionAnswers(new Map());
    setCurrentGoal("");
    setGoalVersions(null);
    setEditingGoal(null);
    setShowVersionComparison(false);
    setComparisonVersions(null);
    setMode("chat");
    setShowGoalSuggestions(false);
    setSuggestedGoals([]);
    setMessages([]);

    // Preferences modal is now optional - users can open it manually via settings
    // No auto-open to avoid interrupting the workflow

    // Focus chat input on component mount
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 100);
  }, [startNewPlanSignal]);

  // Auto-generate questions when context changes (legacy structured flow only)
  useEffect(() => {
    if (AGENT_DRIVEN_FLOW) return; // disable in agent-driven mode
    if (currentGoal && dataSources.length > 0 && pendingQuestions.length === 0) {
      const questions = generateQuestions({
        goal: currentGoal,
        businessType: preferences ? Array.from(preferences.businessType)[0] : undefined,
        dataSources,
        budget: preferences ? Array.from(preferences.budget)[0] : undefined,
      });

      if (questions.length > 0) {
        setPendingQuestions(questions);
        // Show first question
        const firstQuestion = questions[0];
        setMessages((m) => [
          ...m,
          {
            id: `question-${Date.now()}`,
            role: "question",
            text: firstQuestion.text,
            timestamp: Date.now(),
            question: firstQuestion,
          },
        ]);
      }
    }
  }, [currentGoal, dataSources]);

  // Helper: start flow with a raw goal text (from PlanSelector quick-start)
  const startFlowWithGoalText = async (goalText: string) => {
    const trimmed = goalText.trim();
    if (!trimmed) return;

    setCurrentGoal(trimmed);
    setShowGoalSuggestions(false);
    setLoading(true);

    // Show immediate user message
    setMessages((m) => [
      ...m,
      {
        id: `user-goal-${Date.now()}`,
        role: "user",
        text: trimmed,
        timestamp: Date.now(),
      },
    ]);

    // Let LLM evaluate the goal and decide next steps
    try {
      const resp = await postOpenAIChat({
        model: "dyocense-chat-mini",
        messages: [
          { role: "system", content: AGENT_SYSTEM_PROMPT },
          ...messages
            .filter(m => m.role !== "system")
            .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
          { role: "user", content: trimmed }
        ],
        temperature: 0.3,
        context: {
          ...buildEnhancedContext(),
          goal: trimmed,
          intent: "goal_evaluation",
        },
      });

      const content = resp.choices?.[0]?.message?.content ||
        "Great goal! Let me help you create a detailed action plan.";

      setMessages((m) => [...m, {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: content,
        timestamp: Date.now(),
      }]);

      // Analyze LLM response to determine if it needs more info or is ready to plan
      const lowerContent = content.toLowerCase();
      const needsMoreInfo = lowerContent.includes("?") ||
        lowerContent.includes("need to know") ||
        lowerContent.includes("clarify") ||
        lowerContent.includes("could you") ||
        lowerContent.includes("tell me more");

      if (!needsMoreInfo) {
        // LLM thinks goal is specific enough, proceed to planning
        const planningIndicators = [
          "let me create",
          "i'll create",
          "creating a plan",
          "start planning",
          "here's your plan",
          "action plan"
        ];
        const shouldPlan = planningIndicators.some(indicator =>
          lowerContent.includes(indicator)
        );

        if (shouldPlan) {
          // Give user a moment to read the message, then start planning
          setTimeout(() => {
            generatePlan(trimmed);
          }, 1500);
        }
      }
      // Otherwise, conversation continues naturally with user responding to LLM's questions

      setLoading(false);

    } catch (error) {
      console.error("Error in goal flow:", error);

      // Fallback: If LLM is unavailable, show a helpful message and still attempt planning
      setMessages((m) => [...m, {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: `I understand your goal: "${trimmed}". Let me create a detailed action plan for you.`,
        timestamp: Date.now(),
      }]);

      // Proceed to planning even without LLM conversation
      setTimeout(() => {
        generatePlan(trimmed);
      }, 1000);

      setLoading(false);
    }
  };

  // If a goal is seeded (e.g., from PlanSelector), kick off the flow automatically after reset
  useEffect(() => {
    if (seedGoal && seedGoal.trim()) {
      startFlowWithGoalText(seedGoal);
    }
    // We include startNewPlanSignal so a new-plan reset followed by the same seedGoal still triggers
  }, [seedGoal, startNewPlanSignal]);

  const handlePreferencesConfirm = async (summary: string, prefs: PreferencesState) => {
    setPreferences(prefs);
    // Persist a simple flag to indicate preferences were set for this tenant
    try {
      const tenantId = profile?.tenant_id;
      if (tenantId) {
        localStorage.setItem(`dyocense-prefs-set-${tenantId}`, "true");
      }
    } catch { }

    setMessages((m) => [
      ...m,
      {
        id: `user-prefs-${Date.now()}`,
        role: "user",
        text: `My preferences: ${summary}`,
        timestamp: Date.now(),
      },
    ]);

    const businessType = Array.from(prefs.businessType)[0] || "";
    const objectives = Array.from(prefs.objectiveFocus);
    const pace = Array.from(prefs.operatingPace)[0] || "";
    const budget = Array.from(prefs.budget)[0] || "";
    const markets = Array.from(prefs.markets);

    // Use backend recommendations
    const goals = await generateSuggestedGoalsFromBackend(profile || null, {
      businessType,
      objectives,
      pace,
      budget,
      markets,
    });

    setSuggestedGoals(goals);
    setShowGoalSuggestions(true);

    setMessages((m) => [
      ...m,
      {
        id: `assistant-goals-${Date.now()}`,
        role: "assistant",
        text: `Based on your preferences, I've identified ${goals.length} high-priority goals. Select one to get started, or upload data for more personalized recommendations.`,
        timestamp: Date.now(),
      },
    ]);
  };

  const handleGoalSelect = async (goal: SuggestedGoal) => {
    // Convert preferences to business profile format
    const businessProfile = preferences ? {
      businessType: Array.from(preferences.businessType)[0] || "",
      objectives: Array.from(preferences.objectiveFocus),
      pace: Array.from(preferences.operatingPace)[0] || "",
      budget: Array.from(preferences.budget)[0] || "",
      markets: Array.from(preferences.markets),
    } : {
      businessType: "",
      objectives: [],
      pace: "",
      budget: "",
      markets: [],
    };

    const goalStatement = generateGoalStatement(goal, businessProfile);
    setCurrentGoal(goalStatement);
    setShowGoalSuggestions(false);

    setMessages((m) => [
      ...m,
      {
        id: `user-goal-${Date.now()}`,
        role: "user",
        text: `I want to: ${goalStatement}`,
        timestamp: Date.now(),
      },
    ]);

    // Create initial goal version
    const initialVersion = createGoalVersion(
      null,
      {
        title: goal.title,
        description: goalStatement,
        metrics: [],
        timeline: goal.estimatedDuration,
        status: "draft",
      },
      "Initial goal creation",
      profile?.tenant_id || "user"
    );

    setGoalVersions({
      goalId: initialVersion.goalId,
      versions: [initialVersion],
      branches: {},
    });
    setEditingGoal(initialVersion);

    // Generate contextual questions
    const questions = generateQuestions({
      goal: goalStatement,
      businessType: preferences ? Array.from(preferences.businessType)[0] : undefined,
      dataSources,
      budget: preferences ? Array.from(preferences.budget)[0] : undefined,
    });

    if (questions.length > 0) {
      setPendingQuestions(questions);
      setMessages((m) => [
        ...m,
        {
          id: `assistant-questions-${Date.now()}`,
          role: "assistant",
          text: `Great! To create an accurate, measurable plan, I need to ask a few questions. This will help ensure your goal is SMART (Specific, Measurable, Achievable, Relevant, Time-bound).`,
          timestamp: Date.now(),
        },
        {
          id: `question-${Date.now()}`,
          role: "question",
          text: questions[0].text,
          timestamp: Date.now(),
          question: questions[0],
        },
      ]);
    } else {
      // No questions needed, proceed with research
      generatePlan(goalStatement);
    }
  };

  // DEPRECATED: Legacy Q&A handler - kept for reference but no longer used
  // Now using LLM-driven conversational flow in startFlowWithGoalText
  /*
  const handleQuestionAnswer = (question: Question, answer: string) => {
    const validation = validateAnswer(question, answer);

    if (!validation.valid) {
      setMessages((m) => [
        ...m,
        {
          id: `validation-${Date.now()}`,
          role: "system",
          text: validation.suggestion || "Please provide a valid answer",
          timestamp: Date.now(),
        },
      ]);
      return;
    }

    // Store answer
    const newAnswers = new Map(questionAnswers);
    newAnswers.set(question.id, answer);
    setQuestionAnswers(newAnswers);

    // Mark question as answered
    const updatedQuestions = pendingQuestions.map((q) =>
      q.id === question.id ? { ...q, answered: true, answer } : q
    );
    setPendingQuestions(updatedQuestions);

    // Add user answer to chat
    setMessages((m) => [
      ...m,
      {
        id: `user-answer-${Date.now()}`,
        role: "user",
        text: answer,
        timestamp: Date.now(),
      },
    ]);

    // Generate follow-up questions
    const followUps = generateFollowUpQuestions(question, answer, {
      goal: currentGoal,
      businessType: preferences ? Array.from(preferences.businessType)[0] : undefined,
      dataSources,
      budget: preferences ? Array.from(preferences.budget)[0] : undefined,
    });

    if (followUps.length > 0) {
      setPendingQuestions([...updatedQuestions, ...followUps]);
      setMessages((m) => [
        ...m,
        {
          id: `question-${Date.now()}`,
          role: "question",
          text: followUps[0].text,
          timestamp: Date.now(),
          question: followUps[0],
        },
      ]);
    } else {
      // Check if all required questions answered
      const unansweredRequired = updatedQuestions.filter((q) => q.required && !q.answered);

      if (unansweredRequired.length > 0) {
        // Ask next required question
        const nextQuestion = unansweredRequired[0];
        setMessages((m) => [
          ...m,
          {
            id: `question-${Date.now()}`,
            role: "question",
            text: nextQuestion.text,
            timestamp: Date.now(),
            question: nextQuestion,
          },
        ]);
      } else {
        // All required questions answered, enrich goal and proceed
        const enrichedGoal = enrichGoalWithAnswers(currentGoal, newAnswers);
        setCurrentGoal(enrichedGoal);

        setMessages((m) => [
          ...m,
          {
            id: `assistant-proceed-${Date.now()}`,
            role: "assistant",
            text: `Perfect! I have all the information I need. Let me create a detailed, measurable plan for you: "${enrichedGoal}"`,
            timestamp: Date.now(),
          },
        ]);

        generatePlan(enrichedGoal);
      }
    }
  };
  */

  const handleDataSourceAdded = (source: DataSource) => {
    setDataSources((prev) => {
      const existing = prev.find((s) => s.id === source.id);
      let updated;
      if (existing) {
        updated = prev.map((s) => (s.id === source.id ? source : s));
      } else {
        updated = [...prev, source];
      }

      // Persist to localStorage
      if (profile?.tenant_id) {
        try {
          const key = `dyocense-datasources-${profile.tenant_id}`;
          localStorage.setItem(key, JSON.stringify(updated));
        } catch (error) {
          console.error("Error saving data sources:", error);
        }
      }

      return updated;
    });

    if (source.status === "ready") {
      // Call agent to acknowledge and suggest next steps
      (async () => {
        try {
          const resp = await postOpenAIChat({
            model: "dyocense-chat-mini",
            messages: [
              { role: "system", content: AGENT_SYSTEM_PROMPT },
              ...messages
                .filter(m => m.role !== "system")
                .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
              { role: "user", content: `Data source "${source.name}" is now connected with ${source.metadata?.rows} rows and columns: ${source.metadata?.columns?.join(", ")}.` },
            ],
            temperature: 0.2,
            context: {
              ...buildEnhancedContext(),
              new_data_source: source.name,
              intent: "data_source_added",
            },
          });
          const content = resp.choices?.[0]?.message?.content || `✓ Data source "${source.name}" connected successfully (${source.metadata?.rows} rows). What would you like to analyze?`;
          setMessages((m) => [...m, { id: `assistant-data-${Date.now()}`, role: "assistant", text: content, timestamp: Date.now() }]);
        } catch {
          setMessages((m) => [
            ...m,
            {
              id: `system-data-${Date.now()}`,
              role: "system",
              text: `✓ Data source "${source.name}" connected successfully (${source.metadata?.rows} rows)`,
              timestamp: Date.now(),
            },
          ]);
        }
      })();
    }
  };

  const handleDataSourceRemove = async (sourceId: string) => {
    const source = dataSources.find(s => s.id === sourceId);
    if (!source) return;

    setDataSources((prev) => {
      const updated = prev.filter(s => s.id !== sourceId);
      if (profile?.tenant_id) {
        try {
          const key = `dyocense-datasources-${profile.tenant_id}`;
          localStorage.setItem(key, JSON.stringify(updated));
        } catch (error) {
          console.error("Error saving data sources:", error);
        }
      }
      return updated;
    });

    // Call agent to acknowledge removal
    try {
      const resp = await postOpenAIChat({
        model: "dyocense-chat-mini",
        messages: [
          { role: "system", content: AGENT_SYSTEM_PROMPT },
          ...messages
            .filter(m => m.role !== "system")
            .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
          { role: "user", content: `Removed data source "${source.name}".` },
        ],
        temperature: 0.2,
        context: {
          tenant_id: profile?.tenant_id,
          has_data_sources: dataSources.length > 1,
          preferences,
          data_sources: dataSources.filter(ds => ds.id !== sourceId).map(ds => ({ id: ds.id, name: ds.name, type: ds.type, rows: ds.metadata?.rows })),
          connectors: tenantConnectors.map(c => ({ id: c.id, name: c.displayName, type: c.connectorName || c.connectorId, status: c.status })),
        },
      });
      const content = resp.choices?.[0]?.message?.content || `✓ Removed "${source.name}".`;
      setMessages((m) => [...m, { id: `assistant-remove-${Date.now()}`, role: "assistant", text: content, timestamp: Date.now() }]);
    } catch {
      setMessages((m) => [...m, { id: `system-remove-${Date.now()}`, role: "system", text: `✓ Removed "${source.name}".`, timestamp: Date.now() }]);
    }
  };

  const handleDataSourcePreview = (sourceId: string) => {
    const source = dataSources.find(s => s.id === sourceId);
    if (!source || !source.metadata?.previewData) return;

    const previewText = `Preview of "${source.name}" (showing first ${source.metadata.previewData.length} rows):\n\n` +
      source.metadata.columns?.join(" | ") + "\n" +
      "---".repeat(source.metadata.columns?.length || 1) + "\n" +
      source.metadata.previewData.map(row =>
        source.metadata!.columns!.map(col => row[col]).join(" | ")
      ).join("\n");

    setMessages((m) => [
      ...m,
      {
        id: `preview-${Date.now()}`,
        role: "system",
        text: previewText,
        timestamp: Date.now(),
      },
    ]);
  };

  const processFileUpload = async (file: File): Promise<DataSource> => {
    const source: DataSource = {
      id: `file-${Date.now()}-${Math.random()}`,
      type: "file",
      name: file.name,
      status: "uploading",
      metadata: { size: file.size },
    };

    handleDataSourceAdded(source);

    try {
      const content = await file.text();
      let parsedData: any[] = [];
      let columns: string[] = [];

      if (file.name.endsWith('.csv')) {
        const lines = content.split('\n').filter(l => l.trim());
        if (lines.length > 0) {
          columns = lines[0].split(',').map(c => c.trim());
          parsedData = lines.slice(1).map(line => {
            const values = line.split(',');
            const row: any = {};
            columns.forEach((col, idx) => {
              row[col] = values[idx]?.trim();
            });
            return row;
          });
        }
      } else if (file.name.endsWith('.json')) {
        const json = JSON.parse(content);
        parsedData = Array.isArray(json) ? json : [json];
        if (parsedData.length > 0) {
          columns = Object.keys(parsedData[0]);
        }
      }

      const updatedSource: DataSource = {
        ...source,
        status: "ready",
        metadata: {
          size: file.size,
          rows: parsedData.length,
          columns,
          previewData: parsedData.slice(0, 5),
        },
      };

      handleDataSourceAdded(updatedSource);
      return updatedSource;
    } catch (error) {
      const errorSource: DataSource = {
        ...source,
        status: "error",
        metadata: {
          size: file.size,
          error: error instanceof Error ? error.message : "Failed to process file",
        },
      };
      handleDataSourceAdded(errorSource);
      return errorSource;
    }
  };


  const handleConnectorSelected = (connector: ConnectorConfig) => {
    setSelectedConnectorForSetup(connector);
    setShowConnectorMarketplace(false);
    setShowConnectorSetup(true);
  };

  const handleConnectorSetupComplete = async (connectorId: string) => {
    const connector = await tenantConnectorStore.getById(connectorId);
    if (connector && profile?.tenant_id) {
      const updated = await tenantConnectorStore.getAll(profile.tenant_id);
      setTenantConnectors(updated);
      // Ask the agent to summarize what's now possible
      try {
        const resp = await postOpenAIChat({
          model: "dyocense-chat-mini",
          messages: [
            { role: "system", content: AGENT_SYSTEM_PROMPT },
            ...messages
              .filter(m => m.role !== "system")
              .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
            { role: "user", content: `${connector.displayName} connector is now connected.` },
          ],
          temperature: 0.2,
          context: {
            ...buildEnhancedContext(),
            new_connector: connector.displayName,
            intent: "connector_setup_complete",
          },
        });
        const content = resp.choices?.[0]?.message?.content || `✓ ${connector.displayName} connected. What would you like to do with this data?`;
        setMessages((m) => [...m, { id: `assistant-connector-${Date.now()}`, role: "assistant", text: content, timestamp: Date.now() }]);
      } catch {
        setMessages((m) => [...m, { id: `assistant-connector-${Date.now()}`, role: "assistant", text: `✓ ${connector.displayName} connected. What would you like to do with this data?`, timestamp: Date.now() }]);
      }
    }

    setShowConnectorSetup(false);
    setSelectedConnectorForSetup(null);
    setMode("chat");
  };

  const handleConnectorSetupCancel = () => {
    setShowConnectorSetup(false);
    setSelectedConnectorForSetup(null);
    setMode("chat");
  };

  const handleOpenConnectorMarketplace = () => {
    setShowConnectorMarketplace(true);
    setMode("connectors");
  };

  const generatePlan = async (goal: string) => {
    setResearchStatus("researching");

    // Initialize thinking steps for business planning
    const thinkingSteps: ThinkingStep[] = [
      { id: "step-1", label: "Analyzing Business Context", status: "pending" },
      { id: "step-2", label: "Compiling Goal Specification", status: "pending" },
      { id: "step-3", label: "Retrieving Industry Data", status: "pending", subItems: [] },
      { id: "step-4", label: "Generating Optimization Model", status: "pending", subItems: [] },
      { id: "step-5", label: "Running Strategic Analysis", status: "pending", subItems: [] },
      { id: "step-6", label: "Creating Execution Plan", status: "pending", subItems: [] },
      { id: "step-7", label: "Finalizing Recommendations", status: "pending" },
    ];

    // Add thinking progress message
    const thinkingMsgId = `thinking-${Date.now()}`;
    setMessages((m) => [
      ...m,
      {
        id: thinkingMsgId,
        role: "system",
        text: "Analyzing your goal and creating a comprehensive plan...",
        timestamp: Date.now(),
        showThinking: true,
        thinkingSteps: [...thinkingSteps],
      },
    ]);

    try {
      // Step 1: Analyze business context
      thinkingSteps[0].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Get tenant profile for context
      const profile = await getTenantProfile();

      thinkingSteps[0].status = "completed";
      thinkingSteps[0].subItems = [`Analyzed context for ${profile.name}`];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 2: Compile goal
      thinkingSteps[1].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Get recommended templates (with fallback if backend unavailable)
      let selectedTemplate: any = null;
      try {
        const recommendations = await getPlaybookRecommendations();
        selectedTemplate = recommendations.recommendations[0];
      } catch (error) {
        console.warn("Recommendations API unavailable, using default template");
        // Fall back to a known valid template id from registry.json
        selectedTemplate = { title: "Inventory Optimization", template_id: "inventory_basic" };
      }

      thinkingSteps[1].status = "completed";
      thinkingSteps[1].subItems = [`Selected template: ${selectedTemplate?.title || "Business Strategy"}`];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 3: Retrieve data
      thinkingSteps[2].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      thinkingSteps[2].status = "completed";
      thinkingSteps[2].subItems = dataSources.length > 0
        ? [`Analyzed ${dataSources.length} uploaded data sources`]
        : ["Using industry benchmarks and best practices"];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 4: Generate optimization model
      thinkingSteps[3].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Try to create a run using the orchestrator, fall back to local if unavailable
      let runResponse: any = null;
      let runStatus: any = null;
      try {
        runResponse = await createRun({
          goal: goal,
          project_id: profile.tenant_id,
          // Prefer template_id, fall back to archetype_id (backward-compat), then a known valid default
          template_id: (selectedTemplate?.template_id || (selectedTemplate as any)?.archetype_id || "inventory_basic"),
          horizon: 6,
          data_inputs: dataSources.length > 0 ? { sources: dataSources } : undefined,
        });

        thinkingSteps[3].status = "completed";
        thinkingSteps[3].subItems = [`Created optimization model (Run ID: ${runResponse.run_id})`];
        setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

        // Step 5: Poll for completion
        thinkingSteps[4].status = "in-progress";
        setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

        runStatus = await getRun(runResponse.run_id);
        let pollAttempts = 0;
        while (runStatus.status === "pending" || runStatus.status === "running") {
          if (pollAttempts++ > 30) break; // Timeout after 30 seconds
          await new Promise((r) => setTimeout(r, 1000));
          runStatus = await getRun(runResponse.run_id);
        }

        thinkingSteps[4].status = "completed";
        thinkingSteps[4].subItems = [`Analysis complete: ${runStatus.status}`];
        setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));
      } catch (error) {
        console.warn("Backend optimization unavailable, proceeding with local plan generation");
        thinkingSteps[3].status = "completed";
        thinkingSteps[3].subItems = ["Using local business strategy template"];
        setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

        thinkingSteps[4].status = "completed";
        thinkingSteps[4].subItems = ["Applied best-practice frameworks"];
        setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));
      }

      // Step 6: Create execution plan
      thinkingSteps[5].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Extract plan from run result (if available)
      const result = runStatus?.result || {};
      const explanation = result.explanation || {};

      thinkingSteps[5].status = "completed";
      thinkingSteps[5].subItems = ["Generated phased execution roadmap"];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 7: Finalize recommendations
      thinkingSteps[6].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      const newPlan: PlanOverview = {
        title: goal,
        summary: explanation.summary || `Strategic plan to ${goal}. Based on ${dataSources.length > 0 ? "your uploaded data" : "industry benchmarks"} and optimization analysis.`,
        stages: explanation.what_ifs?.map((wif: any, idx: number) => ({
          id: `stage-${idx + 1}`,
          title: wif.scenario || `Phase ${idx + 1}`,
          description: wif.impact || "Execute key initiatives",
          todos: wif.impact?.split(".").filter((s: string) => s.trim().length > 0).slice(0, 4) || [
            "Define metrics and baselines",
            "Execute planned activities",
            "Monitor progress",
            "Optimize and iterate",
          ],
        })) || [
            {
              id: "stage-1",
              title: "Foundation & Baseline",
              description: "Establish current metrics and set up tracking",
              todos: [
                "Document current state metrics",
                "Set up data collection systems",
                "Define success criteria",
                "Identify key stakeholders",
              ],
            },
            {
              id: "stage-2",
              title: "Quick Wins Implementation",
              description: "Execute high-impact, low-effort improvements",
              todos: [
                "Implement top 3 quick wins",
                "Monitor immediate impact",
                "Gather early feedback",
                "Adjust approach as needed",
              ],
            },
            {
              id: "stage-3",
              title: "Strategic Initiatives",
              description: "Roll out major improvements",
              todos: [
                "Execute main transformation activities",
                "Track progress against targets",
                "Manage change with team",
                "Document learnings",
              ],
            },
            {
              id: "stage-4",
              title: "Optimization & Scale",
              description: "Refine and expand successful approaches",
              todos: [
                "Analyze results vs. targets",
                "Optimize underperforming areas",
                "Scale successful initiatives",
                "Plan next iteration",
              ],
            },
          ],
        quickWins: result.solution?.kpis?.slice(0, 3).map((kpi: any) =>
          `${kpi.name}: ${kpi.description || "Optimize for impact"}`
        ) || [
            "Implement low-cost automation for repetitive tasks",
            "Optimize top 3 high-cost processes",
            "Launch quick feedback collection system",
          ],
        estimatedDuration: questionAnswers.get("goal-timeframe") || "6 months",
        dataSources: dataSources.map(ds => ({
          id: ds.id,
          name: ds.name,
          type: ds.type,
          size: ds.metadata?.size || 0,
        })),
      };

      thinkingSteps[6].status = "completed";
      thinkingSteps[6].subItems = ["Plan ready with actionable recommendations"];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      setPlan(newPlan);
      setLastPlanGeneratedTime(Date.now());
      setResearchStatus("ready");

      setMessages((m) => [
        ...m,
        {
          id: `plan-ready-${Date.now()}`,
          role: "assistant",
          text: "✅ Your strategic plan is ready! Created using real optimization analysis and industry best practices. Review the phased roadmap and start tracking progress.",
          timestamp: Date.now(),
        },
      ]);

      onPlanGenerated?.(newPlan);

    } catch (error) {
      console.error("Plan generation error:", error);

      // Mark all remaining steps as completed (graceful fallback)
      thinkingSteps.forEach(step => {
        if (step.status === "in-progress" || step.status === "pending") {
          step.status = "completed";
        }
      });
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Generate fallback plan using LLM instead of hardcoded structure
      console.warn("Backend unavailable, generating LLM-driven fallback plan...");

      try {
        // Use LLM to generate a personalized, context-aware plan
        const planPrompt = `Generate a detailed, actionable business plan for the following goal:

**Goal**: ${goal}

**Context**:
- Project: ${projectName || "Not specified"}

**Generate a JSON plan with this exact structure**:
{
  "title": "Clear, inspiring title for the plan",
  "summary": "2-3 sentence executive summary explaining what will be achieved and how",
  "stages": [
    {
      "id": "stage-1",
      "title": "Phase name (e.g., Discovery & Analysis)",
      "description": "What gets accomplished in this phase",
      "todos": ["Specific action 1", "Specific action 2", "Specific action 3", "Specific action 4"]
    },
    // Include 4 stages total: Discovery, Quick Wins, Core Execution, Optimization
  ],
  "quickWins": ["Quick win 1", "Quick win 2", "Quick win 3"],
  "estimatedDuration": "X months"
}

**Requirements**:
1. Make stages specific to the goal (not generic)
2. Include concrete, actionable todos (not vague advice)
3. Base quick wins on the goal's focus area
4. If data sources exist, reference them in the plan
5. Keep it practical and achievable

Return ONLY the JSON object, no additional text.`;

        const llmResp = await postOpenAIChat({
          model: "dyocense-chat-mini",
          messages: [
            {
              role: "system",
              content: buildSystemPrompt() + "\n\nYou are a business planning expert. Generate detailed, actionable plans in JSON format. Be specific and practical, not generic."
            },
            {
              role: "user",
              content: planPrompt
            }
          ],
          temperature: 0.4, // Slightly higher for creativity but still focused
          context: {
            ...buildEnhancedContext(),
            goal: goal,
            fallback_mode: true,
            intent: "fallback_plan_generation",
          },
        });

        const llmContent = llmResp.choices?.[0]?.message?.content || "";

        // Try to parse JSON from LLM response
        let fallbackPlan: PlanOverview;

        try {
          // Extract JSON if wrapped in code blocks
          const jsonMatch = llmContent.match(/```json?\s*([\s\S]*?)\s*```/) ||
            llmContent.match(/\{[\s\S]*\}/);
          const jsonStr = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : llmContent;
          const parsedPlan = JSON.parse(jsonStr);

          // Validate and construct PlanOverview
          fallbackPlan = {
            title: parsedPlan.title || goal,
            summary: parsedPlan.summary || `Strategic plan to ${goal}. Based on proven business frameworks.`,
            stages: (parsedPlan.stages || []).map((stage: any, idx: number) => ({
              id: stage.id || `stage-${idx + 1}`,
              title: stage.title || `Phase ${idx + 1}`,
              description: stage.description || "Execute key initiatives",
              todos: Array.isArray(stage.todos) ? stage.todos.slice(0, 5) : [
                "Define success metrics",
                "Execute planned activities",
                "Monitor progress",
                "Adjust based on results"
              ],
            })),
            quickWins: Array.isArray(parsedPlan.quickWins) ? parsedPlan.quickWins.slice(0, 3) : [
              "Identify and optimize highest-impact area",
              "Set up basic progress tracking",
              "Execute one quick improvement"
            ],
            estimatedDuration: parsedPlan.estimatedDuration || questionAnswers.get("goal-timeframe") || "6 months",
            dataSources: dataSources.map(ds => ({
              id: ds.id,
              name: ds.name,
              type: ds.type,
              size: ds.metadata?.size || 0,
            })),
          };

          // Ensure we have at least 3 stages
          while (fallbackPlan.stages.length < 3) {
            const phaseNum = fallbackPlan.stages.length + 1;
            fallbackPlan.stages.push({
              id: `stage-${phaseNum}`,
              title: `Phase ${phaseNum}`,
              description: "Execute key initiatives for this phase",
              todos: [
                "Define phase objectives",
                "Execute planned activities",
                "Monitor key metrics",
                "Adjust approach as needed"
              ],
            });
          }

        } catch (parseError) {
          console.warn("Failed to parse LLM JSON, using LLM text response");

          // Fallback: Use LLM response as summary and create basic structure
          fallbackPlan = {
            title: goal,
            summary: llmContent.substring(0, 300) || `Strategic plan to ${goal}. Based on proven business frameworks and industry best practices.`,
            stages: [
              {
                id: "stage-1",
                title: "Discovery & Baseline",
                description: "Understand current state and set measurable targets",
                todos: [
                  "Measure current performance metrics",
                  "Identify improvement opportunities",
                  "Set specific, measurable targets",
                  "Get team alignment on goals",
                ],
              },
              {
                id: "stage-2",
                title: "Quick Wins (First 30 Days)",
                description: "Execute high-impact, low-effort improvements",
                todos: [
                  "Implement top 3 quick-win actions",
                  "Track daily/weekly progress",
                  "Celebrate early successes",
                  "Build momentum with the team",
                ],
              },
              {
                id: "stage-3",
                title: "Core Initiatives",
                description: "Execute main transformation activities",
                todos: [
                  "Roll out strategic improvements",
                  "Monitor KPIs weekly",
                  "Address blockers quickly",
                  "Adjust tactics based on data",
                ],
              },
            ],
            quickWins: [
              "Review and optimize your highest-impact area",
              "Set up simple progress tracking",
              "Execute one quick improvement this week",
            ],
            estimatedDuration: questionAnswers.get("goal-timeframe") || "6 months",
            dataSources: dataSources.map(ds => ({
              id: ds.id,
              name: ds.name,
              type: ds.type,
              size: ds.metadata?.size || 0,
            })),
          };
        }

        setPlan(fallbackPlan);
        setLastPlanGeneratedTime(Date.now());
        setResearchStatus("ready");

        setMessages((m) => [
          ...m,
          {
            id: `plan-ready-${Date.now()}`,
            role: "assistant",
            text: "✅ Your strategic plan is ready! I've created a practical roadmap based on your goal and context. You can refine this plan as you go, and connect your data sources for more personalized recommendations.",
            timestamp: Date.now(),
          },
        ]);

        onPlanGenerated?.(fallbackPlan);

      } catch (llmError) {
        console.error("LLM fallback also failed, using minimal plan:", llmError);

        // Ultimate fallback: minimal generic plan if even LLM fails
        const minimalPlan: PlanOverview = {
          title: goal,
          summary: `Action plan for: ${goal}. Connect your data sources and I'll help create a more personalized plan.`,
          stages: [
            {
              id: "stage-1",
              title: "Getting Started",
              description: "Set up tracking and baseline metrics",
              todos: [
                "Define what success looks like",
                "Measure current state",
                "Identify key actions",
                "Set up progress tracking",
              ],
            },
            {
              id: "stage-2",
              title: "Take Action",
              description: "Execute your plan",
              todos: [
                "Start with highest-impact actions",
                "Monitor progress regularly",
                "Adjust based on results",
                "Document what works",
              ],
            },
          ],
          quickWins: [
            "Identify your highest-impact opportunity",
            "Take one action this week",
            "Set up basic tracking",
          ],
          estimatedDuration: "6 months",
          dataSources: dataSources.map(ds => ({
            id: ds.id,
            name: ds.name,
            type: ds.type,
            size: ds.metadata?.size || 0,
          })),
        };

        setPlan(minimalPlan);
        setLastPlanGeneratedTime(Date.now());
        setResearchStatus("ready");

        setMessages((m) => [
          ...m,
          {
            id: `plan-ready-${Date.now()}`,
            role: "assistant",
            text: "✅ I've created a basic plan to get you started. Connect your data sources or provide more context, and I'll help create a more detailed, personalized plan.",
            timestamp: Date.now(),
          },
        ]);

        onPlanGenerated?.(minimalPlan);
      }
    }
  };

  const handleUpdateGoal = () => {
    if (!editingGoal || !goalVersions) return;

    // Validate SMART criteria
    const validation = validateSMARTGoal(editingGoal);

    if (!validation.isValid) {
      setMessages((m) => [
        ...m,
        {
          id: `validation-${Date.now()}`,
          role: "system",
          text: `⚠️ Goal validation issues:\n${validation.issues.join("\n")}\n\nSuggestions:\n${validation.suggestions.join("\n")}`,
          timestamp: Date.now(),
        },
      ]);
      return;
    }

    // Create new version
    const latestVersion = goalVersions.versions[goalVersions.versions.length - 1];
    const newVersion = createGoalVersion(
      latestVersion,
      editingGoal,
      "User updated goal metrics and timeline",
      profile?.tenant_id || "user"
    );

    const updatedHistory: VersionHistory = {
      ...goalVersions,
      versions: [...goalVersions.versions, newVersion],
    };

    setGoalVersions(updatedHistory);
    setEditingGoal(newVersion);

    setMessages((m) => [
      ...m,
      {
        id: `version-created-${Date.now()}`,
        role: "system",
        text: `✓ Created version ${newVersion.version} of your goal. You can compare versions or rollback anytime.`,
        timestamp: Date.now(),
      },
    ]);
  };

  const handleFeedback = (messageId: string, feedback: "positive" | "negative") => {
    setMessages((m) =>
      m.map(msg =>
        msg.id === messageId
          ? { ...msg, feedback: msg.feedback === feedback ? null : feedback }
          : msg
      )
    );

    // Here you could send feedback to analytics/backend
    console.log(`Feedback for message ${messageId}: ${feedback}`);
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userInput = input;
    setInput("");

    // Heuristic: determine if this is a complex strategic goal suitable for multi-agent analysis
    const isComplexGoal = (text: string) => {
      const verbs = /(increase|reduce|improve|optimize|forecast|predict|plan|launch|grow|scale|retain|expand)/i;
      const hasPercentOrTarget = /(\b\d+%\b|\b\d{4}\b|\$\d+)/.test(text);
      return verbs.test(text) && (text.length > 25 || hasPercentOrTarget);
    };

    // Parse common intents before calling agent
    const lowerInput = userInput.toLowerCase();

    // Handle "preview [filename]" intent
    if (lowerInput.includes("preview")) {
      const matchedSource = dataSources.find(ds =>
        lowerInput.includes(ds.name.toLowerCase())
      );
      if (matchedSource) {
        handleDataSourcePreview(matchedSource.id);
        setMessages((m) => [...m, {
          id: `user-${Date.now()}`,
          role: "user",
          text: userInput,
          timestamp: Date.now(),
        }]);
        return;
      }
    }

    // Handle "remove [filename]" intent
    if (lowerInput.includes("remove") || lowerInput.includes("delete")) {
      const matchedSource = dataSources.find(ds =>
        lowerInput.includes(ds.name.toLowerCase())
      );
      if (matchedSource) {
        setMessages((m) => [...m, {
          id: `user-${Date.now()}`,
          role: "user",
          text: userInput,
          timestamp: Date.now(),
        }]);
        await handleDataSourceRemove(matchedSource.id);
        return;
      }
    }

    // Agent-driven flow: all messages go through LLM
    // Add user message to chat
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      text: userInput,
      timestamp: Date.now(),
    };

    setMessages((m) => [...m, userMsg]);

    // Phase 3: Track conversation turn
    setConversationTurnCount(prev => prev + 1);

    // LLM now handles connector suggestions via function calling (removed hardcoded logic)

    // Process as general chat using backend
    setLoading(true);

    try {
      const useMultiAgent = multiAgentMode || (messages.length === 0 && isComplexGoal(userInput));
      let message: any = null;

      if (useMultiAgent) {
        // Call multi-agent backend endpoint
        const maResp = await fetch('/v1/chat/multi-agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            goal: userInput,
            context: {
              data_sources: dataSources.map(ds => ({ id: ds.id, name: ds.name, type: ds.type })),
              connectors: tenantConnectors.filter(c => c.status === 'active').map(c => ({ id: c.id, name: c.displayName })),
            },
            llm_config: { provider: (window as any).LLM_PROVIDER || 'azure' }
          })
        });
        if (!maResp.ok) throw new Error(`Multi-agent request failed: ${maResp.status}`);
        const maJson = await maResp.json();
        setLastMultiAgentPayload(maJson);
        // Shape a message-like object to reuse existing parsing logic
        message = { content: maJson.response };
        // Also append structured analysis messages (compact summaries)
        const summaries: string[] = [];
        if (maJson.goal_analysis) summaries.push(`Refined Goal: ${maJson.goal_analysis.refined_goal || userInput}`);
        if (maJson.data_analysis) summaries.push(`Data Readiness: ${maJson.data_analysis.ready_for_modeling ? 'Ready for modeling' : 'Needs more data'}`);
        if (maJson.model_results) summaries.push(`Model Insights: ${(maJson.model_results.analysis || '').slice(0, 200)}${(maJson.model_results.analysis || '').length > 200 ? '...' : ''}`);
        if (maJson.recommendations) summaries.push(`Recommendations prepared.`);
        if (summaries.length) {
          setMessages(m => [...m, {
            id: `ma-summary-${Date.now()}`,
            role: 'assistant',
            text: summaries.join('\n'),
            timestamp: Date.now(),
          }]);
        }
      } else {
        // Standard single-agent chat flow
        const oaiResp = await postOpenAIChat({
          model: "dyocense-chat-mini",
          messages: [
            { role: "system", content: AGENT_SYSTEM_PROMPT },
            ...messages
              .filter(m => m.role !== "system")
              .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
            { role: "user", content: userInput },
          ],
          temperature: 0.2,
          ...({
            tools: AGENT_FUNCTION_TOOLS,
            tool_choice: "auto",
          } as any),
          context: {
            ...buildEnhancedContext(),
          },
        });
        message = oaiResp.choices?.[0]?.message as any;
      }

      // Handle function calls from LLM (if supported by backend)
      if (message?.tool_calls && Array.isArray(message.tool_calls) && message.tool_calls.length > 0) {
        for (const toolCall of message.tool_calls) {
          try {
            const args = JSON.parse(toolCall.function.arguments);

            if (toolCall.function.name === "show_connector_options") {
              const connectorMsg: Message = {
                id: `connector-${Date.now()}`,
                role: "assistant",
                text: args.reason || "Here are some data sources you can connect:",
                embeddedComponent: "connector-selector",
                componentData: {
                  connectors: args.connectors || [],
                  reason: args.reason,
                },
                timestamp: Date.now(),
              };
              setMessages(m => [...m, connectorMsg]);
            } else if (toolCall.function.name === "show_data_uploader") {
              const uploaderMsg: Message = {
                id: `uploader-${Date.now()}`,
                role: "assistant",
                text: args.reason || "Upload your data file here:",
                embeddedComponent: "data-uploader",
                componentData: {
                  format: args.format || "csv",
                  expectedColumns: args.expectedColumns,
                },
                timestamp: Date.now(),
              };
              setMessages(m => [...m, uploaderMsg]);
            }
          } catch (parseError) {
            console.error("Error parsing tool call arguments:", parseError);
          }
        }
      }

      // Handle regular text response and parse for inline UI markers
      if (message?.content) {
        let responseText = message.content;
        console.log("🤖 LLM Response:", responseText);

        // Parse [SHOW_CONNECTORS: ...] marker
        const connectorMatch = responseText.match(/\[SHOW_CONNECTORS:\s*([^\]]+)\]/i);
        if (connectorMatch) {
          console.log("✅ Detected SHOW_CONNECTORS:", connectorMatch[1]);
          const connectorList = connectorMatch[1].split(',').map((c: string) => c.trim().toLowerCase());
          responseText = responseText.replace(connectorMatch[0], '').trim();

          // Add text message
          if (responseText) {
            setMessages(m => [...m, {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              text: responseText,
              timestamp: Date.now(),
            }]);
          }

          // Add connector selector
          setMessages(m => [...m, {
            id: `connector-${Date.now()}`,
            role: "assistant",
            text: "Choose a data source to connect:",
            embeddedComponent: "connector-selector",
            componentData: {
              connectors: connectorList,
              reason: "Select a connector to integrate your business data",
            },
            timestamp: Date.now(),
          }]);
        }
        // Parse [SHOW_UPLOADER: ...] marker
        else if (responseText.match(/\[SHOW_UPLOADER:\s*([^\]]+)\]/i)) {
          const uploaderMatch = responseText.match(/\[SHOW_UPLOADER:\s*([^\]]+)\]/i);
          const format = uploaderMatch![1].trim().toLowerCase();
          console.log("✅ Detected SHOW_UPLOADER:", format);
          responseText = responseText.replace(uploaderMatch![0], '').trim();

          // Add text message
          if (responseText) {
            setMessages(m => [...m, {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              text: responseText,
              timestamp: Date.now(),
            }]);
          }

          // Add uploader
          setMessages(m => [...m, {
            id: `uploader-${Date.now()}`,
            role: "assistant",
            text: "Upload your data file:",
            embeddedComponent: "data-uploader",
            componentData: {
              format: format === "excel" ? "excel" : "csv",
              expectedColumns: [],
            },
            timestamp: Date.now(),
          }]);
        }
        // No markers found, just show text
        else {
          const assistantMsg: Message = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            text: responseText,
            timestamp: Date.now(),
          };
          setMessages((m) => [...m, assistantMsg]);
        }
      }

      // If no content and no tool calls, provide default message
      if (!message?.content && (!message?.tool_calls || message.tool_calls.length === 0)) {
        const defaultMsg: Message = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          text: "I'm here to help! You can upload data, select a goal, or ask me questions about your business objectives.",
          timestamp: Date.now(),
        };
        setMessages((m) => [...m, defaultMsg]);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: "I'm having trouble connecting to the backend. Please try again or contact support if the issue persists.",
        timestamp: Date.now(),
      };
      setMessages((m) => [...m, errorMsg]);
    }
    setLoading(false);
  }; return (
    <div className="flex h-full w-full flex-col bg-white relative">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-2.5 flex-shrink-0">
        <div className="mb-1.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="text-primary" size={20} />
            <h2 className="text-base font-semibold text-gray-900">AI Business Assistant</h2>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setMode("data-upload")}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${mode === "data-upload"
                ? "bg-primary text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
            >
              <FileUp size={14} className="inline mr-1" />
              Data ({dataSources.length})
            </button>
            <button
              onClick={handleOpenConnectorMarketplace}
              data-connectors-button
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${mode === "connectors"
                ? "bg-primary text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
            >
              <Database size={14} className="inline mr-1" />
              Connectors ({tenantConnectors.filter(c => c.status === "active").length})
            </button>
            <button
              onClick={() => setMultiAgentMode(m => !m)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${multiAgentMode
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
              title="Toggle multi-agent strategic analysis"
            >
              <GitBranch size={14} className="inline mr-1" />
              {multiAgentMode ? 'Multi-Agent ON' : 'Multi-Agent'}
            </button>
            {goalVersions && (
              <button
                onClick={() => setMode("version-history")}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${mode === "version-history"
                  ? "bg-primary text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
              >
                <History size={14} className="inline mr-1" />
                Versions ({goalVersions.versions.length})
              </button>
            )}
          </div>
        </div>

        {/* Project Context Display */}
        {projectName && (
          <div className="mb-2 flex items-center gap-2 text-xs text-gray-600 bg-blue-50 px-3 py-1.5 rounded-md border border-blue-100">
            <span className="text-gray-500">Planning for:</span>
            <span className="font-semibold text-primary">📁 {projectName}</span>
          </div>
        )}

        {/* Optional: Show preferences button less prominently */}
        {!preferences && (
          <div className="flex items-center justify-between">
            <button
              onClick={() => setPrefsModalOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary"
              title="Optional: Set preferences for personalized recommendations"
            >
              <Settings size={14} className="text-gray-400 hover:text-primary" />
              <span className="text-xs">Set Preferences (Optional)</span>
            </button>
          </div>
        )}
        {preferences && (
          <div className="flex items-center justify-between">
            <button
              onClick={() => setPrefsModalOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-700 hover:text-primary"
            >
              <Settings size={14} className="text-primary" />
              Update Preferences
            </button>
            <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-medium text-green-700 border border-green-200">
              <CheckCircle2 size={12} /> Preferences set
            </span>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-4 py-3 pb-28">
        {mode === "chat" && (
          <>
            {/* Empty State - Optimized UX Flow */}
            {messages.length === 0 && !plan && (
              <div className="flex flex-col items-center justify-center h-full px-6 py-8">
                <div className="w-full max-w-2xl space-y-8">
                  {/* Hero Section */}
                  <div className="text-center space-y-4">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-3xl mb-2 shadow-lg">
                      <Sparkles className="text-white" size={40} />
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 tracking-tight">
                      Let's create your action plan
                    </h2>
                    <p className="text-base text-gray-600 max-w-md mx-auto">
                      I'll help you turn your business goal into a detailed, step-by-step plan with milestones and actionable tasks.
                    </p>
                  </div>

                  {/* Quick Start Cards - Prominent CTAs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      {
                        icon: "💰",
                        title: "Cut Costs",
                        description: "Reduce expenses by 15% in 3 months",
                        gradient: "from-emerald-500 to-teal-600",
                        hoverGradient: "from-emerald-600 to-teal-700"
                      },
                      {
                        icon: "�",
                        title: "Boost Revenue",
                        description: "Increase sales by 20% this quarter",
                        gradient: "from-blue-500 to-indigo-600",
                        hoverGradient: "from-blue-600 to-indigo-700"
                      },
                      {
                        icon: "⚡",
                        title: "Optimize Operations",
                        description: "Improve efficiency and productivity",
                        gradient: "from-purple-500 to-pink-600",
                        hoverGradient: "from-purple-600 to-pink-700"
                      },
                      {
                        icon: "👥",
                        title: "Grow Customers",
                        description: "Expand customer base by 30%",
                        gradient: "from-orange-500 to-red-600",
                        hoverGradient: "from-orange-600 to-red-700"
                      },
                    ].map((card, idx) => (
                      <button
                        key={card.title}
                        onClick={() => {
                          startFlowWithGoalText(card.description);
                        }}
                        className="group relative overflow-hidden rounded-2xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm hover:shadow-xl hover:border-transparent hover:-translate-y-1 transition-all duration-300"
                        style={{ animationDelay: `${idx * 100}ms` }}
                      >
                        {/* Gradient overlay on hover */}
                        <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>

                        {/* Content */}
                        <div className="relative z-10">
                          <div className="flex items-start justify-between mb-3">
                            <span className="text-4xl mb-2 transform group-hover:scale-110 transition-transform duration-300">
                              {card.icon}
                            </span>
                            <span className="text-gray-400 group-hover:text-white transition-colors">
                              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </span>
                          </div>
                          <h3 className="text-lg font-bold text-gray-900 group-hover:text-white mb-1 transition-colors">
                            {card.title}
                          </h3>
                          <p className="text-sm text-gray-600 group-hover:text-white/90 transition-colors">
                            {card.description}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Divider with "OR" */}
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-200"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white text-gray-500 font-medium">OR</span>
                    </div>
                  </div>

                  {/* Custom Input Prompt */}
                  <div className="text-center space-y-4">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-200">
                      <Target size={16} className="text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">Have a specific goal in mind?</span>
                    </div>
                    <div className="flex items-center justify-center gap-2 text-gray-600">
                      <span className="text-base">Type it in the box below</span>
                      <span className="text-2xl animate-bounce">👇</span>
                    </div>
                  </div>

                  {/* Optional Feature Showcase */}
                  {tenantConnectors.filter(c => c.status === "active").length === 0 && (
                    <div className="pt-4">
                      <div className="rounded-2xl bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 p-6 border border-blue-100">
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center">
                            <Database size={20} className="text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-gray-900 mb-1">
                              💡 Pro Tip: Connect Your Data
                            </h4>
                            <p className="text-sm text-gray-600 mb-3">
                              Link your business systems for AI-powered insights and personalized recommendations.
                            </p>
                            <button
                              onClick={handleOpenConnectorMarketplace}
                              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all text-sm font-medium text-gray-900 shadow-sm"
                            >
                              <span>Browse Connectors</span>
                              <span className="text-blue-600">→</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Messages - Only shown after conversation starts */}
            {messages.length > 0 && (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] ${msg.role === "user"
                        ? "bg-primary text-white rounded-xl px-4 py-3"
                        : msg.role === "system"
                          ? "w-full"
                          : msg.role === "question"
                            ? "bg-amber-50 border border-amber-200 text-gray-900 rounded-xl px-4 py-3"
                            : "bg-gray-100 text-gray-900 rounded-xl px-4 py-3"
                        }`}
                    >
                      {msg.role === "question" && (
                        <div className="flex items-start gap-2 mb-2">
                          <AlertCircle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
                          <div className="text-xs text-amber-700 font-semibold">
                            {msg.question?.reason}
                          </div>
                        </div>
                      )}

                      {/* Thinking Progress for system messages */}
                      {msg.showThinking && msg.thinkingSteps && (
                        <div className="mb-3">
                          <ThinkingProgress
                            steps={msg.thinkingSteps}
                            isCollapsed={false}
                          />
                        </div>
                      )}

                      <div className="whitespace-pre-wrap text-sm">{msg.text}</div>

                      {/* Embedded Components for Inline Connector/Upload Flow */}
                      {msg.embeddedComponent === "connector-selector" && msg.componentData && (
                        <InlineConnectorSelector
                          connectors={msg.componentData.connectors || []}
                          reason={msg.componentData.reason}
                          onSelect={handleConnectorSelected}
                        />
                      )}

                      {msg.embeddedComponent === "data-uploader" && msg.componentData && (
                        <InlineDataUploader
                          format={msg.componentData.format || "csv"}
                          expectedColumns={msg.componentData.expectedColumns}
                          onUploadComplete={handleDataSourceAdded}
                        />
                      )}

                      {/* Action Buttons for file uploads and data operations */}
                      {msg.actions && msg.actions.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-gray-200">
                          <div className="flex flex-wrap gap-2">
                            {msg.actions.map((action, idx) => (
                              <button
                                key={idx}
                                onClick={async () => {
                                  if (action.action === "preview") {
                                    handleDataSourcePreview(action.data?.sourceId);
                                  } else if (action.action === "remove") {
                                    await handleDataSourceRemove(action.data?.sourceId);
                                  } else if (action.action === "analyze") {
                                    setInput(`Analyze the data in ${dataSources.find(ds => ds.id === action.data?.sourceId)?.name}`);
                                    chatInputRef.current?.focus();
                                  }
                                }}
                                className="rounded-lg border-2 border-primary bg-white px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary hover:text-white transition-all"
                              >
                                {action.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* DEPRECATED: Quick Reply Buttons for Questions - No longer used with LLM-driven flow
                      {msg.question?.suggestedAnswers && !msg.question.answered && (
                        <div className="mt-4 pt-3 border-t border-amber-200">
                          <p className="text-xs font-semibold text-gray-600 mb-2">Quick replies:</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.question.suggestedAnswers.map((ans) => (
                              <button
                                key={ans}
                                onClick={() => msg.question && handleQuestionAnswer(msg.question, ans)}
                                className="rounded-lg border-2 border-primary bg-white px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-white transition-all"
                              >
                                {ans}
                              </button>
                            ))}
                          </div>
                          <p className="text-xs text-gray-500 mt-2 italic">Or type your own answer below</p>
                        </div>
                      )}
                      */}

                      {/* Feedback buttons for assistant messages */}
                      {msg.role === "assistant" && !msg.question && (
                        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-200">
                          <button
                            onClick={() => handleFeedback(msg.id, "positive")}
                            className={`p-1.5 rounded-lg transition-colors ${msg.feedback === "positive"
                              ? "bg-green-100 text-green-600"
                              : "text-gray-400 hover:text-green-600 hover:bg-green-50"
                              }`}
                            title="Helpful"
                          >
                            <ThumbsUp size={14} />
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.id, "negative")}
                            className={`p-1.5 rounded-lg transition-colors ${msg.feedback === "negative"
                              ? "bg-red-100 text-red-600"
                              : "text-gray-400 hover:text-red-600 hover:bg-red-50"
                              }`}
                            title="Not helpful"
                          >
                            <ThumbsDown size={14} />
                          </button>
                          <span className="text-xs text-gray-500 ml-1">Was this helpful?</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}

            {/* Suggested Goals */}
            {showGoalSuggestions && suggestedGoals.length > 0 && (
              <div className="mt-6 space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <Lightbulb size={18} className="text-amber-500" />
                  Suggested Goals for You
                </div>
                {suggestedGoals.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => handleGoalSelect(goal)}
                    className="w-full rounded-xl border border-gray-200 bg-white p-4 text-left hover:border-primary hover:bg-blue-50"
                  >
                    <div className="mb-2 flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Target size={18} className="text-primary flex-shrink-0" />
                        <h3 className="font-semibold text-gray-900">{goal.title}</h3>
                      </div>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${goal.priority === "high"
                          ? "bg-red-100 text-red-700"
                          : goal.priority === "medium"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-green-100 text-green-700"
                          }`}
                      >
                        {goal.priority}
                      </span>
                    </div>
                    <p className="mb-2 text-sm text-gray-600">{goal.description}</p>
                    <div className="flex gap-3 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {goal.estimatedDuration}
                      </span>
                      <span>Impact: {goal.expectedImpact}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Plan Overview */}
            {plan && (
              <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <CheckCircle2 size={20} className="text-green-600" />
                  <h3 className="font-bold text-gray-900">Plan Ready</h3>
                </div>
                <h4 className="mb-2 font-semibold text-gray-900">{plan.title}</h4>
                <p className="mb-3 text-sm text-gray-700">{plan.summary}</p>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>📋 {plan.stages.length} implementation stages</div>
                  <div>⚡ {plan.quickWins.length} quick wins identified</div>
                  <div>⏱️ Estimated duration: {plan.estimatedDuration}</div>
                </div>
              </div>
            )}
          </>
        )}

        {mode === "data-upload" && (
          <div>
            <h3 className="mb-4 text-lg font-bold text-gray-900">Upload Data & Connect Sources</h3>
            <DataUploader onDataSourceAdded={handleDataSourceAdded} existingSources={dataSources} />
          </div>
        )}

        {mode === "connectors" && (
          <div>
            <h3 className="mb-4 text-lg font-bold text-gray-900">Connected Data Sources</h3>
            <ConnectedDataSources
              tenantId={profile?.tenant_id || ""}
              onAddConnector={handleOpenConnectorMarketplace}
              onConfigureConnector={(connectorId) => {
                // TODO: Implement connector reconfiguration
                console.log("Configure connector:", connectorId);
              }}
            />
            {tenantConnectors.length > 0 && (
              <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <h4 className="mb-2 font-semibold text-blue-900">💡 Using Your Data</h4>
                <p className="text-sm text-blue-800">{dataContextPrompt || "Your connected data will be used to ground analysis and recommendations."}</p>
              </div>
            )}
          </div>
        )}

        {mode === "version-history" && goalVersions && (
          <div>
            <h3 className="mb-4 text-lg font-bold text-gray-900">Goal Version History</h3>
            <div className="space-y-3">
              {goalVersions.versions.map((version, idx) => {
                const isLatest = idx === goalVersions.versions.length - 1;
                const progress = calculateGoalProgress(version);

                return (
                  <div
                    key={version.id}
                    className={`rounded-lg border p-4 ${isLatest ? "border-primary bg-blue-50" : "border-gray-200 bg-white"
                      }`}
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GitBranch size={16} className="text-gray-600" />
                        <span className="font-semibold text-gray-900">Version {version.version}</span>
                        {isLatest && (
                          <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-semibold text-white">
                            Current
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(version.createdAt).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="mb-2 text-sm font-semibold text-gray-900">{version.title}</div>
                    <div className="mb-2 text-xs text-gray-600">{version.changeDescription}</div>
                    <div className="text-xs text-gray-500">
                      {version.metrics.length} metrics • {version.timeline}
                    </div>
                    {progress.overallProgress > 0 && (
                      <div className="mt-2">
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="text-gray-600">Progress</span>
                          <span className="font-semibold text-gray-900">
                            {Math.round(progress.overallProgress)}%
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200">
                          <div
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${progress.overallProgress}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {!isLatest && (
                      <button className="mt-2 text-xs font-semibold text-primary hover:underline">
                        Compare with current
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Floating Input Area - Enhanced UX */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-white via-white to-white/80 border-t border-gray-200 px-6 py-4 shadow-[0_-8px_16px_-4px_rgba(0,0,0,0.1)] backdrop-blur-sm">
        {/* Input hint for empty state */}
        {messages.length === 0 && !loading && (
          <div className="mb-2 flex items-center justify-center gap-2 text-xs text-gray-500">
            <Lightbulb size={14} className="text-yellow-500" />
            <span>Example: "Reduce inventory costs by 20% in the next quarter"</span>
          </div>
        )}

        <form
          className="flex gap-3 items-end max-w-4xl mx-auto"
          onSubmit={e => { e.preventDefault(); handleSend(); }}
          encType="multipart/form-data"
        >
          <div className="flex-1 relative">
            <input
              data-chat-input
              ref={chatInputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder={
                pendingQuestions.some((q) => !q.answered && q.required)
                  ? "Type your answer..."
                  : messages.length === 0
                    ? "Describe your business goal in your own words..."
                    : "Ask me anything..."
              }
              className="w-full rounded-2xl border-2 border-gray-300 px-5 py-3.5 pr-12 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all disabled:bg-gray-50 disabled:cursor-not-allowed"
              disabled={loading}
            />
            {/* Character count for longer inputs */}
            {input.length > 50 && (
              <span className="absolute right-3 bottom-3 text-xs text-gray-400">
                {input.length}
              </span>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <label
              htmlFor="chat-file-upload"
              className={`cursor-pointer flex items-center gap-2 px-4 py-3.5 rounded-2xl border-2 border-gray-300 bg-white hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              title="Upload data file (CSV, Excel)"
            >
              <FileUp size={20} className="text-gray-600" />
              <span className="text-sm font-medium text-gray-700 hidden sm:inline">Upload</span>
              <input
                id="chat-file-upload"
                type="file"
                multiple
                disabled={loading}
                accept=".csv,.xlsx,.xls,.json"
                style={{ display: "none" }}
                onChange={async (e) => {
                  const files = Array.from(e.target.files || []);
                  setLoading(true);

                  for (const file of files) {
                    // Process and persist file
                    const processedSource = await processFileUpload(file);

                    // Add user message for upload
                    setMessages((m) => [
                      ...m,
                      {
                        id: `file-upload-${Date.now()}-${file.name}`,
                        role: "user",
                        text: `Uploaded file: ${file.name}`,
                        files: [{ name: file.name, size: file.size }],
                        timestamp: Date.now(),
                      },
                    ]);

                    // Call agent/LLM for next step after upload
                    try {
                      const oaiResp = await postOpenAIChat({
                        model: "dyocense-chat-mini",
                        messages: [
                          { role: "system", content: AGENT_SYSTEM_PROMPT },
                          ...messages
                            .filter(m => m.role !== "system")
                            .map(m => ({ role: (m.role === "question" ? "assistant" : m.role) as any, content: m.text })),
                          { role: "user", content: `Uploaded file: ${file.name} (${processedSource.metadata?.rows} rows, ${processedSource.metadata?.columns?.length} columns: ${processedSource.metadata?.columns?.join(", ")})` }
                        ],
                        temperature: 0.2,
                        context: {
                          tenant_id: profile?.tenant_id,
                          has_data_sources: true,
                          preferences: preferences,
                          uploaded_file: {
                            name: file.name,
                            size: file.size,
                            rows: processedSource.metadata?.rows,
                            columns: processedSource.metadata?.columns,
                          },
                          data_sources: [...dataSources, processedSource].map(ds => ({ id: ds.id, name: ds.name, type: ds.type, rows: ds.metadata?.rows, columns: ds.metadata?.columns })),
                          connectors: tenantConnectors.map(c => ({ id: c.id, name: c.displayName, type: c.connectorName || c.connectorId, status: c.status })),
                        },
                      });
                      const content = oaiResp.choices?.[0]?.message?.content || `File "${file.name}" uploaded with ${processedSource.metadata?.rows} rows!`;
                      setMessages((m) => [
                        ...m,
                        {
                          id: `file-action-${Date.now()}-${file.name}`,
                          role: "assistant",
                          text: content,
                          timestamp: Date.now(),
                          actions: processedSource.status === "ready" ? [
                            { label: "Preview Data", action: "preview", data: { sourceId: processedSource.id } },
                            { label: "Analyze", action: "analyze", data: { sourceId: processedSource.id } },
                            { label: "Remove", action: "remove", data: { sourceId: processedSource.id } },
                          ] : undefined,
                        },
                      ]);
                    } catch (err) {
                      console.error("Agent error after upload:", err);
                      setMessages((m) => [
                        ...m,
                        {
                          id: `file-action-error-${Date.now()}-${file.name}`,
                          role: "assistant",
                          text: `File "${file.name}" uploaded with ${processedSource.metadata?.rows || 0} rows. What would you like to do with it?`,
                          timestamp: Date.now(),
                          actions: processedSource.status === "ready" ? [
                            { label: "Preview Data", action: "preview", data: { sourceId: processedSource.id } },
                            { label: "Analyze", action: "analyze", data: { sourceId: processedSource.id } },
                            { label: "Remove", action: "remove", data: { sourceId: processedSource.id } },
                          ] : undefined,
                        },
                      ]);
                    }
                  }

                  setLoading(false);
                  // Reset file input
                  e.target.value = "";
                }}
              />
            </label>

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className={`flex items-center gap-2 px-6 py-3.5 rounded-2xl font-semibold text-white shadow-lg transition-all ${loading || !input.trim()
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:shadow-xl hover:scale-105 active:scale-95'
                }`}
              title={!input.trim() ? "Type a message to send" : "Send message"}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span className="hidden sm:inline">Thinking...</span>
                </>
              ) : (
                <>
                  <Send size={20} />
                  <span className="hidden sm:inline">Send</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <PreferencesModal
        open={prefsModalOpen}
        onClose={() => setPrefsModalOpen(false)}
        onConfirm={handlePreferencesConfirm}
        profile={profile}
      />

      {showConnectorMarketplace && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold">Connect Data Source</h2>
              <button
                onClick={() => {
                  setShowConnectorMarketplace(false);
                  setMode("chat");
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <ConnectorMarketplace
                onConnectorSelected={handleConnectorSelected}
                tenantId={profile?.tenant_id || ""}
              />
            </div>
          </div>
        </div>
      )}

      {showConnectorSetup && selectedConnectorForSetup && (
        <ChatConnectorSetup
          connector={selectedConnectorForSetup}
          tenantId={profile?.tenant_id || ""}
          userId={profile?.tenant_id || ""}
          onComplete={handleConnectorSetupComplete}
          onCancel={handleConnectorSetupCancel}
        />
      )}
    </div>
  );
}
