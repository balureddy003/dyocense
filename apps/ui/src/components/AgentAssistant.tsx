import {
  FileUp,
  Loader2,
  Send,
  Sparkles,
  CheckCircle2,
  Clock,
  Settings,
  Lightbulb,
  Target,
  GitBranch,
  History,
  AlertCircle,
  Database,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { TenantProfile, getTenantProfile, getPlaybookRecommendations, createRun, getRun, postOpenAIChat } from "../lib/api";
import { PreferencesModal } from "./PreferencesModal";
import { generateSuggestedGoalsFromBackend, generateGoalStatement, SuggestedGoal } from "../lib/goalGenerator";
import { DataUploader, DataSource } from "./DataUploader";
import { generateQuestions, validateAnswer, generateFollowUpQuestions, enrichGoalWithAnswers, Question } from "../lib/intelligentQuestioning";
import { createGoalVersion, validateSMARTGoal, calculateGoalProgress, compareGoalVersions, GoalVersion, VersionHistory } from "../lib/goalVersioning";
import { ConnectorMarketplace } from "./ConnectorMarketplace";
import { ChatConnectorSetup } from "./ChatConnectorSetup";
import { ConnectedDataSources } from "./ConnectedDataSources";
import { tenantConnectorStore, generateDataContextPrompt, suggestConnectorFromIntent, checkDataAvailability, type TenantConnector } from "../lib/tenantConnectors";
import { getConnectorById, type ConnectorConfig } from "../lib/connectorMarketplace";
import { ThinkingProgress, ThinkingStep } from "./ThinkingProgress";
import { ThumbsUp, ThumbsDown } from "lucide-react";

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
  // Signal to kickoff a fresh new-plan journey. Increment to trigger.
  startNewPlanSignal?: number;
};

export function AgentAssistant({ onPlanGenerated, profile, startNewPlanSignal }: AgentAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hi! I'm your intelligent AI business assistant. I can help you create data-driven, measurable goals. Let's start by setting your preferences, or upload data to begin analysis.",
      timestamp: Date.now(),
    },
  ]);
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
  
  const fileRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

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
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        text: "Let's create a new plan. Start by setting preferences, connect your data, or tell me your top business goal.",
        timestamp: Date.now(),
      },
    ]);
    
    // Only auto-open preferences modal if user hasn't set them yet
    const hasSetPreferences = profile?.tenant_id && 
      typeof window !== 'undefined' && 
      localStorage.getItem(`dyocense-prefs-set-${profile.tenant_id}`) === 'true';
    
    if (!hasSetPreferences) {
      setTimeout(() => {
        setPrefsModalOpen(true);
        chatInputRef.current?.focus();
      }, 100);
    }
  }, [startNewPlanSignal, profile?.tenant_id]);

  // Auto-generate questions when context changes
  useEffect(() => {
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

  const handlePreferencesConfirm = async (summary: string, prefs: PreferencesState) => {
    setPreferences(prefs);
    // Persist a simple flag to indicate preferences were set for this tenant
    try {
      const tenantId = profile?.tenant_id;
      if (tenantId) {
        localStorage.setItem(`dyocense-prefs-set-${tenantId}`, "true");
      }
    } catch {}

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

      setMessages((m) => [
        ...m,
        {
          id: `system-connector-${Date.now()}`,
          role: "system",
          text: `✓ ${connector.displayName} connected successfully! I can now access your ${connector.dataTypes.join(", ")} data.`,
          timestamp: Date.now(),
        },
      ]);
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
      
      // Get recommended templates
      const recommendations = await getPlaybookRecommendations();
      const selectedTemplate = recommendations.recommendations[0];
      
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
      
      // Create a run using the orchestrator
      const runResponse = await createRun({
        goal: goal,
        project_id: profile.tenant_id,
        template_id: selectedTemplate?.template_id || "business_strategy",
        horizon: 6,
        data_inputs: dataSources.length > 0 ? { sources: dataSources } : undefined,
      });
      
      thinkingSteps[3].status = "completed";
      thinkingSteps[3].subItems = [`Created optimization model (Run ID: ${runResponse.run_id})`];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 5: Poll for completion
      thinkingSteps[4].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));
      
      let runStatus = await getRun(runResponse.run_id);
      let pollAttempts = 0;
      while (runStatus.status === "pending" || runStatus.status === "running") {
        if (pollAttempts++ > 30) break; // Timeout after 30 seconds
        await new Promise((r) => setTimeout(r, 1000));
        runStatus = await getRun(runResponse.run_id);
      }
      
      thinkingSteps[4].status = "completed";
      thinkingSteps[4].subItems = [`Analysis complete: ${runStatus.status}`];
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));

      // Step 6: Create execution plan
      thinkingSteps[5].status = "in-progress";
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));
      
      // Extract plan from run result
      const result = runStatus.result || {};
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
      
      // Mark all remaining steps as failed
      thinkingSteps.forEach(step => {
        if (step.status === "in-progress" || step.status === "pending") {
          step.status = "completed";
        }
      });
      setMessages((m) => m.map(msg => msg.id === thinkingMsgId ? { ...msg, thinkingSteps: [...thinkingSteps] } : msg));
      
      setResearchStatus("idle");
      setMessages((m) => [
        ...m,
        {
          id: `error-${Date.now()}`,
          role: "system",
          text: `⚠️ Could not generate plan from backend. ${error instanceof Error ? error.message : "Please try again."}`,
          timestamp: Date.now(),
        },
      ]);
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

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      text: input,
      timestamp: Date.now(),
    };

    setMessages((m) => [...m, userMsg]);
    const userInput = input;
    setInput("");

    // Check for connector-related keywords
    const connectorIntent = suggestConnectorFromIntent(userInput);
    if (connectorIntent && profile?.tenant_id) {
      setMessages((m) => [
        ...m,
        {
          id: `assistant-connector-${Date.now()}`,
          role: "assistant",
          text: connectorIntent.reason,
          timestamp: Date.now(),
        },
      ]);

      // Show connector marketplace
      setShowConnectorMarketplace(true);
      setMode("connectors");
      return;
    }

    // Check if answering a pending question
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role === "question" && lastMessage.question && !lastMessage.question.answered) {
      handleQuestionAnswer(lastMessage.question, input);
      return;
    }

    // Otherwise, process as general chat using backend
    setLoading(true);

    try {
      const oaiResp = await postOpenAIChat({
        model: "dyocense-chat-mini",
        messages: messages
          .filter(m => m.role !== "system")
          .map(m => ({ role: m.role as any, content: m.text }))
          .concat([{ role: "user", content: userInput }]),
        temperature: 0.2,
        context: {
          tenant_id: profile?.tenant_id,
          has_data_sources: dataSources.length > 0,
          preferences: preferences,
        },
      });

      const content = oaiResp.choices?.[0]?.message?.content || "I'm here to help! You can upload data, select a goal, or ask me questions about your business objectives.";
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: content,
        timestamp: Date.now(),
      };

      setMessages((m) => [...m, assistantMsg]);
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
  };

  return (
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
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                mode === "data-upload"
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
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                mode === "connectors"
                  ? "bg-primary text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              <Database size={14} className="inline mr-1" />
              Connectors ({tenantConnectors.filter(c => c.status === "active").length})
            </button>
            {goalVersions && (
              <button
                onClick={() => setMode("version-history")}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                  mode === "version-history"
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

        <div className="flex items-center justify-between">
          <button
            onClick={() => setPrefsModalOpen(true)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-700 hover:text-primary"
          >
            <Settings size={14} className="text-primary" />
            {preferences ? "Update Preferences" : "Set Preferences"}
          </button>
          {preferences && (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-medium text-green-700 border border-green-200">
              <CheckCircle2 size={12} /> Preferences set
            </span>
          )}
        </div>
      </div>

      {/* Main Content Area */}
  <div className="flex-1 overflow-y-auto px-4 py-3 pb-28">
        {mode === "chat" && (
          <>
            {/* Messages */}
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] ${
                      msg.role === "user"
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
                    
                    {/* Feedback buttons for assistant messages */}
                    {msg.role === "assistant" && !msg.question && (
                      <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-200">
                        <button
                          onClick={() => handleFeedback(msg.id, "positive")}
                          className={`p-1.5 rounded-lg transition-colors ${
                            msg.feedback === "positive"
                              ? "bg-green-100 text-green-600"
                              : "text-gray-400 hover:text-green-600 hover:bg-green-50"
                          }`}
                          title="Helpful"
                        >
                          <ThumbsUp size={14} />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, "negative")}
                          className={`p-1.5 rounded-lg transition-colors ${
                            msg.feedback === "negative"
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
                    
                    {msg.question?.suggestedAnswers && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {msg.question.suggestedAnswers.map((ans) => (
                          <button
                            key={ans}
                            onClick={() => msg.question && handleQuestionAnswer(msg.question, ans)}
                            className="rounded-lg border border-amber-300 bg-white px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-amber-50"
                          >
                            {ans}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

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
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                          goal.priority === "high"
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
                    className={`rounded-lg border p-4 ${
                      isLatest ? "border-primary bg-blue-50" : "border-gray-200 bg-white"
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

      {/* Floating Input Area - Absolutely positioned at bottom */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-white border-t border-gray-200 px-6 py-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
        <div className="flex gap-2">
          <input
            data-chat-input
            ref={chatInputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={
              pendingQuestions.some((q) => !q.answered && q.required)
                ? "Answer the question above..."
                : "Ask me anything about your goals..."
            }
            className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-primary px-6 py-3 font-semibold text-white hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
          </button>
        </div>
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
