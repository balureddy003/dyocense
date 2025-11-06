# Intelligent AI Agent - Complete Implementation Guide

## Overview

This document describes the complete implementation of an intelligent AI agent assistant for Dyocense, featuring GitHub Copilot-level intelligence with:

- **Data Upload & Connectors** - Upload files (CSV, JSON) and connect to external data sources (APIs, databases, spreadsheets)
- **Intelligent Questioning** - Context-aware questions to identify missing data and ensure SMART goals
- **Goal Versioning** - Git-like version control for goals with comparison and rollback capabilities
- **Measurable Tracking** - Baseline vs. target metrics with lowest-level progress monitoring
- **Interactive Refinement** - Edit goals with real-time SMART validation and suggestions

---

## Architecture

### Component Structure

```
apps/ui/src/
├── components/
│   ├── AgentAssistantEnhanced.tsx    # Main intelligent agent UI (800+ lines)
│   ├── DataUploader.tsx               # File upload & connector manager (350+ lines)
│   ├── PreferencesModal.tsx           # 5-step preference wizard (545 lines)
│   ├── ExecutionPanel.tsx             # Stage-by-stage execution tracking
│   └── MetricsPanel.tsx               # KPI visualization with progress
├── lib/
│   ├── intelligentQuestioning.ts      # Context-aware question generation (250+ lines)
│   ├── goalVersioning.ts              # Goal version control system (350+ lines)
│   ├── goalGenerator.ts               # Goal template library (376 lines)
│   └── api.ts                         # API client for backend services
```

### Data Flow

```
User Sets Preferences
  ↓
System Suggests Goals (60+ templates)
  ↓
User Selects Goal
  ↓
System Generates Contextual Questions
  ↓
User Answers Questions (with validation)
  ↓
System Enriches Goal with SMART Criteria
  ↓
System Creates Initial Goal Version (v1)
  ↓
System Generates Execution Plan
  ↓
User Tracks Progress & Updates Goals
  ↓
System Creates New Versions (v2, v3, ...)
  ↓
User Can Compare Versions & Rollback
```

---

## Feature 1: Data Upload & Connectors

### Components

**`DataUploader.tsx`** - Unified data ingestion component

### Capabilities

#### File Upload
- **Drag & Drop** - Drop files directly into the drop zone
- **File Browser** - Click to select files from file system
- **Supported Formats**:
  - CSV (parsed with column detection)
  - JSON (arrays and objects)
  - Excel (.xlsx, .xls) - *planned*
- **Automatic Parsing** - Extracts columns, row count, preview data
- **Error Handling** - Validates file format and shows helpful error messages

#### External Connectors

**REST API Connector**
```typescript
{
  url: "https://api.example.com/data",
  method: "GET",
  headers: { "Authorization": "Bearer token" }
}
```

**Google Sheets Connector**
```typescript
{
  sheetUrl: "https://docs.google.com/spreadsheets/d/...",
  range: "Sheet1!A1:Z100"
}
```

**PostgreSQL Database Connector**
```typescript
{
  host: "localhost",
  port: 5432,
  database: "mydb",
  username: "user",
  password: "password",
  query: "SELECT * FROM sales ORDER BY date DESC LIMIT 1000"
}
```

### Data Source Model

```typescript
type DataSource = {
  id: string;
  type: "file" | "api" | "database" | "spreadsheet";
  name: string;
  status: "uploading" | "processing" | "ready" | "error";
  metadata?: {
    size?: number;
    rows?: number;
    columns?: string[];
    previewData?: any[];
    error?: string;
  };
};
```

### Usage Example

```tsx
<DataUploader
  onDataSourceAdded={(source) => {
    if (source.status === "ready") {
      console.log(`Connected: ${source.name}`);
      console.log(`Rows: ${source.metadata?.rows}`);
      console.log(`Columns: ${source.metadata?.columns}`);
    }
  }}
  existingSources={dataSources}
/>
```

---

## Feature 2: Intelligent Questioning

### Purpose

Automatically identify gaps in goal definition and ask contextual questions to ensure goals are SMART (Specific, Measurable, Achievable, Relevant, Time-bound).

### Components

**`intelligentQuestioning.ts`** - Question generation and validation logic

### Question Generation

```typescript
const questions = generateQuestions({
  goal: "Reduce operational costs",
  businessType: "restaurant",
  dataSources: [], // Empty = ask about data availability
  budget: "<$10K",
});

// Returns questions like:
// 1. "What specific number or percentage improvement do you want to achieve?"
// 2. "What is your target timeframe for achieving this goal?"
// 3. "What is your current monthly/annual cost for this area?"
// 4. "Do you have historical data about your operations?"
```

### Question Categories

| Category | Purpose | Example |
|----------|---------|---------|
| `goal` | Clarify goal specifics | "What specific improvement do you want?" |
| `data` | Identify missing data | "Do you have historical sales data?" |
| `metrics` | Establish baselines | "What is your current monthly cost?" |
| `timeline` | Define deadlines | "When do you want to achieve this?" |
| `constraints` | Understand limitations | "What budget do you have available?" |

### Question Flow

1. **Initial Questions** - Generated based on goal text and context
2. **Validation** - Checks if answer is sufficient (e.g., contains numbers for metrics)
3. **Follow-up Questions** - Generated based on previous answers
4. **Goal Enrichment** - Incorporates answers into goal statement

### Question Model

```typescript
type Question = {
  id: string;
  text: string;
  category: "goal" | "data" | "metrics" | "timeline" | "constraints";
  reason: string; // Why this question matters
  suggestedAnswers?: string[]; // Quick reply options
  required: boolean;
  answered?: boolean;
  answer?: string;
};
```

### Context-Aware Analysis

The system automatically detects:

- **Missing Metrics** - Goal lacks quantifiable targets → Ask for specific numbers
- **No Timeframe** - Goal doesn't specify when → Ask for deadline
- **Data Gaps** - Goal mentions costs but no financial data uploaded → Ask for data
- **Ambiguous Scope** - Goal is too vague → Ask clarifying questions
- **Resource Constraints** - No budget specified → Ask about available resources

### Example Flow

```
User Goal: "Improve customer satisfaction"

Question 1: "What is your current customer satisfaction score (e.g., NPS, CSAT)?"
Reason: "Baseline satisfaction helps measure improvement and set realistic targets"

User Answer: "NPS is 30"

Question 2: "What specific improvement do you want to achieve?"
Reason: "A measurable target helps track progress and determine success"

User Answer: "15% increase"

Enriched Goal: "Improve customer satisfaction by 15% (current NPS: 30) within 6 months"
```

---

## Feature 3: Goal Versioning

### Purpose

Provide Git-like version control for business goals, enabling:
- Tracking changes over time
- Comparing different versions
- Rolling back to previous versions
- Creating what-if branches

### Components

**`goalVersioning.ts`** - Version control and comparison logic

### Goal Version Model

```typescript
type GoalVersion = {
  id: string;
  goalId: string; // Consistent across versions
  version: number; // 1, 2, 3, ...
  title: string;
  description: string;
  metrics: GoalMetric[];
  timeline: string;
  createdAt: Date;
  createdBy: string;
  changeDescription: string; // What changed
  status: "draft" | "active" | "archived";
  parentVersion?: number; // For branching
};

type GoalMetric = {
  name: string;
  baseline: number | string;
  target: number | string;
  unit: string;
  current?: number | string;
  achievable: boolean;
  measurable: boolean;
  relevant: boolean;
  timebound: boolean;
};
```

### Version History

```typescript
type VersionHistory = {
  goalId: string;
  versions: GoalVersion[];
  branches: { [key: string]: number[] }; // For what-if scenarios
};
```

### Creating Versions

```typescript
// Initial version
const v1 = createGoalVersion(
  null,
  {
    title: "Reduce Food Waste",
    description: "Implement inventory tracking to reduce spoilage",
    metrics: [
      {
        name: "Food Cost Percentage",
        baseline: 32,
        target: 28,
        unit: "%",
        achievable: true,
        measurable: true,
        relevant: true,
        timebound: true,
      }
    ],
    timeline: "6 months",
    status: "draft",
  },
  "Initial goal creation",
  "user123"
);

// Updated version
const v2 = createGoalVersion(
  v1,
  {
    title: "Reduce Food Waste",
    description: "Implement inventory tracking to reduce spoilage",
    metrics: [
      {
        name: "Food Cost Percentage",
        baseline: 32,
        target: 26, // More ambitious
        unit: "%",
        achievable: true,
        measurable: true,
        relevant: true,
        timebound: true,
      }
    ],
    timeline: "6 months",
    status: "active",
  },
  "Increased target based on industry benchmarks",
  "user123"
);
```

### Comparing Versions

```typescript
const comparisons = compareGoalVersions(v1, v2);

// Returns:
[
  {
    field: "Metric: Food Cost Percentage",
    oldValue: "32 → 28 %",
    newValue: "32 → 26 %",
    changeType: "modified",
    impact: "major"
  }
]
```

### SMART Validation

```typescript
const validation = validateSMARTGoal(goalVersion);

// Returns:
{
  isValid: false,
  issues: [
    "No timeline specified",
    "Metric 'Revenue' is missing baseline or target"
  ],
  suggestions: [
    "Add a specific deadline or timeframe (e.g., '6 months', 'By Q2 2025')",
    "Provide both baseline and target for Revenue"
  ]
}
```

### Progress Tracking

```typescript
const progress = calculateGoalProgress(goalVersion);

// Returns:
{
  overallProgress: 65, // 65% complete
  metricProgress: [
    {
      name: "Food Cost Percentage",
      progress: 75, // 75% toward target
      onTrack: true
    },
    {
      name: "Waste Reduction",
      progress: 55,
      onTrack: false // Behind schedule
    }
  ]
}
```

### Rollback

```typescript
const rolledBackVersion = rollbackToVersion(history, 3, "user123");

// Creates new version based on version 3
// Change description: "Rolled back to version 3"
```

### Branching (What-If Scenarios)

```typescript
const result = createBranch(history, 2, "aggressive-targets", "user123");

// Creates a new branch to explore more ambitious targets
// without affecting the main version history
```

---

## Feature 4: Measurable Tracking

### Baseline vs. Target

Every metric tracks three values:
- **Baseline** - Current state before starting
- **Target** - Desired end state
- **Current** - Actual progress during execution

### Example Metric Tracking

```typescript
const metric: GoalMetric = {
  name: "Monthly Operating Cost",
  baseline: 50000, // $50K/month currently
  target: 42500, // Goal: $42.5K/month (15% reduction)
  unit: "$",
  current: 46000, // Current: $46K/month (53% progress)
  achievable: true,
  measurable: true,
  relevant: true,
  timebound: true,
};
```

### Progress Calculation

```typescript
// Calculate progress percentage
const baseline = 50000;
const target = 42500;
const current = 46000;

const totalChange = target - baseline; // -7500
const currentChange = current - baseline; // -4000
const progress = (currentChange / totalChange) * 100; // 53%
```

### On-Track Detection

System automatically flags metrics that are behind schedule:

```typescript
{
  name: "Customer Satisfaction",
  progress: 35, // Only 35% toward target
  onTrack: false // Expected to be at 60% by now
}
```

### Lowest-Level Tracking

Progress tracked at multiple levels:

1. **Overall Goal** - Aggregate of all metrics
2. **Individual Metrics** - Each KPI separately
3. **Execution Stages** - Each implementation phase
4. **Todos within Stages** - Each specific task

### Example Progress Dashboard

```
Goal: Reduce Operating Costs by 15%
Overall Progress: 65% ●●●●●●○○○○

Metrics:
├─ Monthly Costs: 53% (✓ On Track)
│  Baseline: $50K → Target: $42.5K → Current: $46K
├─ Energy Usage: 78% (✓ On Track)
│  Baseline: 5000 kWh → Target: 4000 kWh → Current: 4200 kWh
└─ Labor Efficiency: 65% (⚠ Behind)
   Baseline: 40h/week → Target: 32h/week → Current: 36h/week

Stages:
├─ Foundation & Baseline: 100% (Completed)
├─ Quick Wins: 80% (In Progress)
├─ Strategic Initiatives: 30% (In Progress)
└─ Optimization: 0% (Not Started)
```

---

## Feature 5: Interactive Goal Refinement

### SMART Goal Editing

Users can edit any aspect of a goal:
- Title and description
- Baseline and target values
- Timelines and deadlines
- Add/remove metrics

### Real-Time Validation

As users edit, the system provides instant feedback:

```
⚠ Target change: 20% → 30% improvement
   This is ambitious! Consider:
   - Current progress is 15% in 3 months
   - New target requires 2x current pace
   - Suggest: Increase timeline or adjust target
```

### Suggested Improvements

System analyzes goals and suggests enhancements:

```typescript
const suggestions = suggestGoalImprovements(goal);

// Returns:
[
  "Consider adding 2-3 complementary metrics to track different aspects",
  "Add leading indicators (activities) in addition to lagging indicators (outcomes)",
  "Consider breaking this into shorter milestones (3-6 month increments)"
]
```

### Inline Editing UI

```tsx
// Goal editing interface
<div className="goal-editor">
  <input
    value={goal.title}
    onChange={(e) => updateGoal({ title: e.target.value })}
    className="font-bold text-xl"
  />
  
  {/* Metrics editor */}
  {goal.metrics.map((metric) => (
    <div key={metric.name} className="metric-row">
      <input value={metric.name} />
      <input value={metric.baseline} type="number" />
      <span>→</span>
      <input value={metric.target} type="number" />
      <input value={metric.unit} />
      
      {/* SMART validation */}
      <div className="validation-badges">
        <Badge color={metric.measurable ? "green" : "red"}>
          Measurable
        </Badge>
        <Badge color={metric.achievable ? "green" : "yellow"}>
          Achievable
        </Badge>
      </div>
    </div>
  ))}
  
  <button onClick={saveNewVersion}>
    Save as Version {currentVersion + 1}
  </button>
</div>
```

---

## Integration with Existing Components

### AgentAssistant → ExecutionPanel

```tsx
const plan = {
  title: "Reduce Operating Costs by 15%",
  stages: [
    {
      id: "stage-1",
      title: "Foundation & Baseline",
      description: "Establish current metrics",
      todos: [
        "Document current costs",
        "Set up tracking systems",
        "Define success criteria"
      ]
    }
  ]
};

onPlanGenerated(plan);
// ExecutionPanel receives plan and displays stages with progress tracking
```

### AgentAssistant → MetricsPanel

```tsx
const metrics = [
  {
    name: "Monthly Operating Cost",
    before: "$50,000",
    after: "$46,000",
    improvement: "-8%",
    target: "$42,500",
    progress: 53
  }
];

// MetricsPanel displays KPIs with before/after comparison
```

---

## Backend Integration Requirements

### API Endpoints Needed

#### Data Sources

```
POST /v1/data/upload
Body: FormData with file
Response: { id, name, status, metadata }

POST /v1/data/connectors
Body: { type, name, config }
Response: { id, status, metadata }

GET /v1/data/sources
Response: [{ id, type, name, status, metadata }]
```

#### Goal Versioning

```
POST /v1/goals
Body: { title, description, metrics, timeline }
Response: GoalVersion

GET /v1/goals/:id/versions
Response: VersionHistory

POST /v1/goals/:id/versions
Body: { updates, changeDescription }
Response: GoalVersion

GET /v1/goals/:id/versions/:v1/compare/:v2
Response: GoalComparison[]

POST /v1/goals/:id/rollback/:version
Response: GoalVersion
```

#### Intelligent Questioning

```
POST /v1/questions/generate
Body: { goal, businessType, dataSources, budget }
Response: Question[]

POST /v1/questions/:id/answer
Body: { answer }
Response: { valid, followUpQuestions?: Question[] }

POST /v1/goals/enrich
Body: { goal, answers: Map<string, string> }
Response: { enrichedGoal: string }
```

### Database Schema

#### Data Sources Table

```sql
CREATE TABLE data_sources (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  type VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  config JSONB,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Goal Versions Table

```sql
CREATE TABLE goal_versions (
  id UUID PRIMARY KEY,
  goal_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  version INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  metrics JSONB NOT NULL,
  timeline VARCHAR(100),
  change_description TEXT,
  status VARCHAR(50) NOT NULL,
  parent_version INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID NOT NULL
);

CREATE INDEX idx_goal_versions_goal_id ON goal_versions(goal_id);
CREATE INDEX idx_goal_versions_tenant_id ON goal_versions(tenant_id);
```

#### Question Answers Table

```sql
CREATE TABLE question_answers (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  goal_id UUID NOT NULL,
  question_id VARCHAR(100) NOT NULL,
  question_text TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Testing Strategy

### Unit Tests

```typescript
describe("intelligentQuestioning", () => {
  it("generates questions for goals without metrics", () => {
    const questions = generateQuestions({
      goal: "Reduce costs",
      businessType: "restaurant",
      dataSources: [],
    });
    
    expect(questions).toContainEqual(
      expect.objectContaining({
        id: "goal-metric",
        category: "goal"
      })
    );
  });

  it("validates metric answers contain numbers", () => {
    const question: Question = {
      id: "baseline-cost",
      category: "metrics",
      text: "What is your current cost?",
      reason: "Need baseline",
      required: true
    };
    
    const result = validateAnswer(question, "5000");
    expect(result.valid).toBe(true);
    
    const invalid = validateAnswer(question, "a lot");
    expect(invalid.valid).toBe(false);
  });
});

describe("goalVersioning", () => {
  it("creates new version with incremented version number", () => {
    const v1 = createGoalVersion(null, { title: "Goal" }, "Initial", "user");
    const v2 = createGoalVersion(v1, { title: "Goal Updated" }, "Updated title", "user");
    
    expect(v2.version).toBe(2);
    expect(v2.parentVersion).toBe(1);
  });

  it("compares two versions and identifies changes", () => {
    const comparisons = compareGoalVersions(v1, v2);
    
    expect(comparisons).toContainEqual({
      field: "Title",
      oldValue: "Goal",
      newValue: "Goal Updated",
      changeType: "modified",
      impact: "major"
    });
  });

  it("validates SMART criteria", () => {
    const invalidGoal = {
      ...baseGoal,
      metrics: [], // No metrics
      timeline: "" // No timeline
    };
    
    const validation = validateSMARTGoal(invalidGoal);
    expect(validation.isValid).toBe(false);
    expect(validation.issues).toHaveLength(2);
  });
});
```

### Integration Tests

```typescript
describe("AgentAssistant E2E", () => {
  it("guides user from preferences to executable plan", async () => {
    const { getByText, getByRole } = render(<AgentAssistant />);
    
    // Set preferences
    fireEvent.click(getByText("Set Preferences"));
    // ... fill preferences modal
    fireEvent.click(getByText("Confirm"));
    
    // Select suggested goal
    await waitFor(() => expect(getByText(/Suggested Goals/)).toBeInTheDocument());
    fireEvent.click(getByText("Reduce Energy Costs"));
    
    // Answer questions
    await waitFor(() => expect(getByText(/What is your current/)).toBeInTheDocument());
    fireEvent.change(getByRole("textbox"), { target: { value: "5000" } });
    fireEvent.click(getByText("Send"));
    
    // Verify plan generated
    await waitFor(() => expect(getByText(/Plan Ready/)).toBeInTheDocument());
  });
});
```

---

## User Guide

### Getting Started

1. **Set Preferences** - Click "Set Preferences" and complete the 5-step wizard
2. **Review Goals** - System suggests 5 personalized goals
3. **Upload Data** (Optional) - Upload CSV/JSON files or connect to external sources
4. **Select Goal** - Click a suggested goal or type your own
5. **Answer Questions** - System asks 3-5 questions to ensure goal is SMART
6. **Review Plan** - System generates executable plan with stages and milestones
7. **Track Progress** - Update metrics as you execute
8. **Refine Goals** - Edit targets, add metrics, create new versions

### Best Practices

- **Upload Data Early** - More data = better questions and recommendations
- **Be Specific** - Answer questions with specific numbers and dates
- **Update Regularly** - Mark todos complete and update metrics weekly
- **Compare Versions** - Review version history to see how goals evolved
- **Use Branches** - Create what-if scenarios without affecting main goal

---

## Future Enhancements

### Phase 1 (Completed ✓)
- ✓ Data upload with file parsing
- ✓ External connectors (REST API, Google Sheets, PostgreSQL)
- ✓ Intelligent questioning with validation
- ✓ Goal versioning with comparison
- ✓ SMART validation
- ✓ Progress tracking

### Phase 2 (Next)
- [ ] Real-time collaboration (multiple users editing same goal)
- [ ] AI-powered recommendations (suggest targets based on industry benchmarks)
- [ ] Automated data refresh (re-fetch from connectors on schedule)
- [ ] Advanced analytics (trend analysis, forecasting)
- [ ] Export reports (PDF, PowerPoint)

### Phase 3 (Future)
- [ ] Mobile app for progress updates
- [ ] Slack/Teams integration for notifications
- [ ] Webhook support for external triggers
- [ ] Machine learning for achievability prediction
- [ ] Natural language plan generation from uploaded documents

---

## Conclusion

The intelligent AI agent system provides a comprehensive, data-driven approach to business goal management. By combining automated data ingestion, contextual questioning, version control, and measurable tracking, it ensures goals are always SMART and progress is transparent.

**Key Differentiators:**
- **GitHub Copilot-level Intelligence** - Contextual, proactive assistance
- **Data-Driven** - Uses actual business data, not generic templates
- **Version Control** - Track every change, compare versions, rollback
- **Measurable** - Every goal has quantified baselines and targets
- **End-to-End** - From preference setting to plan execution to progress tracking

This system transforms vague business objectives into executable, measurable plans with continuous tracking and refinement capabilities.
