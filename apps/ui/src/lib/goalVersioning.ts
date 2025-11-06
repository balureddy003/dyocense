export type GoalVersion = {
  id: string;
  goalId: string;
  version: number;
  title: string;
  description: string;
  metrics: GoalMetric[];
  timeline: string;
  createdAt: Date;
  createdBy: string;
  changeDescription: string;
  status: "draft" | "active" | "archived";
  parentVersion?: number; // For branching
};

export type GoalMetric = {
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

export type GoalComparison = {
  field: string;
  oldValue: any;
  newValue: any;
  changeType: "added" | "removed" | "modified";
  impact: "major" | "minor" | "none";
};

export type VersionHistory = {
  goalId: string;
  versions: GoalVersion[];
  branches: { [key: string]: number[] }; // branch name -> version numbers
};

/**
 * Creates a new version of a goal
 */
export function createGoalVersion(
  existingVersion: GoalVersion | null,
  updates: Partial<Omit<GoalVersion, "id" | "version" | "goalId" | "createdAt">>,
  changeDescription: string,
  userId: string
): GoalVersion {
  const newVersion: GoalVersion = {
    id: `goal-v${Date.now()}`,
    goalId: existingVersion?.goalId || `goal-${Date.now()}`,
    version: existingVersion ? existingVersion.version + 1 : 1,
    title: updates.title || existingVersion?.title || "Untitled Goal",
    description: updates.description || existingVersion?.description || "",
    metrics: updates.metrics || existingVersion?.metrics || [],
    timeline: updates.timeline || existingVersion?.timeline || "",
    createdAt: new Date(),
    createdBy: userId,
    changeDescription,
    status: updates.status || "draft",
    parentVersion: existingVersion?.version,
  };

  return newVersion;
}

/**
 * Compares two goal versions and returns differences
 */
export function compareGoalVersions(oldVersion: GoalVersion, newVersion: GoalVersion): GoalComparison[] {
  const comparisons: GoalComparison[] = [];

  // Compare title
  if (oldVersion.title !== newVersion.title) {
    comparisons.push({
      field: "Title",
      oldValue: oldVersion.title,
      newValue: newVersion.title,
      changeType: "modified",
      impact: "major",
    });
  }

  // Compare description
  if (oldVersion.description !== newVersion.description) {
    comparisons.push({
      field: "Description",
      oldValue: oldVersion.description,
      newValue: newVersion.description,
      changeType: "modified",
      impact: "minor",
    });
  }

  // Compare timeline
  if (oldVersion.timeline !== newVersion.timeline) {
    comparisons.push({
      field: "Timeline",
      oldValue: oldVersion.timeline,
      newValue: newVersion.timeline,
      changeType: "modified",
      impact: "major",
    });
  }

  // Compare metrics
  const oldMetricMap = new Map(oldVersion.metrics.map((m) => [m.name, m]));
  const newMetricMap = new Map(newVersion.metrics.map((m) => [m.name, m]));

  // Check for modified and removed metrics
  oldVersion.metrics.forEach((oldMetric) => {
    const newMetric = newMetricMap.get(oldMetric.name);
    if (!newMetric) {
      comparisons.push({
        field: `Metric: ${oldMetric.name}`,
        oldValue: formatMetric(oldMetric),
        newValue: null,
        changeType: "removed",
        impact: "major",
      });
    } else if (JSON.stringify(oldMetric) !== JSON.stringify(newMetric)) {
      comparisons.push({
        field: `Metric: ${oldMetric.name}`,
        oldValue: formatMetric(oldMetric),
        newValue: formatMetric(newMetric),
        changeType: "modified",
        impact: oldMetric.target !== newMetric.target ? "major" : "minor",
      });
    }
  });

  // Check for added metrics
  newVersion.metrics.forEach((newMetric) => {
    if (!oldMetricMap.has(newMetric.name)) {
      comparisons.push({
        field: `Metric: ${newMetric.name}`,
        oldValue: null,
        newValue: formatMetric(newMetric),
        changeType: "added",
        impact: "major",
      });
    }
  });

  return comparisons;
}

/**
 * Formats a metric for display in comparisons
 */
function formatMetric(metric: GoalMetric): string {
  return `${metric.baseline} → ${metric.target} ${metric.unit}`;
}

/**
 * Validates if a goal meets SMART criteria
 */
export function validateSMARTGoal(goal: GoalVersion): {
  isValid: boolean;
  issues: string[];
  suggestions: string[];
} {
  const issues: string[] = [];
  const suggestions: string[] = [];

  // Specific: Does it have a clear, detailed description?
  if (!goal.description || goal.description.length < 20) {
    issues.push("Goal description is too vague");
    suggestions.push("Add more details about what you want to achieve and why");
  }

  // Measurable: Does it have metrics with baselines and targets?
  if (goal.metrics.length === 0) {
    issues.push("No metrics defined");
    suggestions.push("Add at least one measurable metric with baseline and target values");
  } else {
    goal.metrics.forEach((metric) => {
      if (!metric.baseline || !metric.target) {
        issues.push(`Metric "${metric.name}" is missing baseline or target`);
        suggestions.push(`Provide both baseline and target for ${metric.name}`);
      }
      if (!metric.measurable) {
        issues.push(`Metric "${metric.name}" is not measurable`);
        suggestions.push(`Ensure ${metric.name} can be tracked with specific numbers`);
      }
    });
  }

  // Achievable: Are the targets realistic?
  goal.metrics.forEach((metric) => {
    if (metric.achievable === false) {
      issues.push(`Target for "${metric.name}" may not be achievable`);
      suggestions.push(`Review if the target for ${metric.name} is realistic given your resources and constraints`);
    }
  });

  // Relevant: Are metrics relevant to the goal?
  goal.metrics.forEach((metric) => {
    if (metric.relevant === false) {
      issues.push(`Metric "${metric.name}" may not be relevant to your goal`);
      suggestions.push(`Ensure ${metric.name} directly supports your overall objective`);
    }
  });

  // Time-bound: Does it have a clear timeline?
  if (!goal.timeline || goal.timeline.length === 0) {
    issues.push("No timeline specified");
    suggestions.push("Add a specific deadline or timeframe (e.g., '6 months', 'By Q2 2025')");
  } else if (!goal.metrics.every((m) => m.timebound)) {
    issues.push("Some metrics lack time constraints");
    suggestions.push("Ensure each metric has a specific date or deadline");
  }

  return {
    isValid: issues.length === 0,
    issues,
    suggestions,
  };
}

/**
 * Calculates progress toward goal metrics
 */
export function calculateGoalProgress(goal: GoalVersion): {
  overallProgress: number;
  metricProgress: { name: string; progress: number; onTrack: boolean }[];
} {
  const metricProgress = goal.metrics.map((metric) => {
    let progress = 0;
    let onTrack = true;

    if (metric.current !== undefined && metric.baseline !== undefined && metric.target !== undefined) {
      const baseline = typeof metric.baseline === "number" ? metric.baseline : parseFloat(String(metric.baseline));
      const target = typeof metric.target === "number" ? metric.target : parseFloat(String(metric.target));
      const current = typeof metric.current === "number" ? metric.current : parseFloat(String(metric.current));

      if (!isNaN(baseline) && !isNaN(target) && !isNaN(current)) {
        const totalChange = target - baseline;
        const currentChange = current - baseline;
        progress = totalChange !== 0 ? (currentChange / totalChange) * 100 : 0;
        progress = Math.max(0, Math.min(100, progress));

        // Check if on track (at least 80% of expected progress based on time)
        onTrack = progress >= 60; // Simplified check
      }
    }

    return { name: metric.name, progress, onTrack };
  });

  const overallProgress =
    metricProgress.length > 0 ? metricProgress.reduce((sum, m) => sum + m.progress, 0) / metricProgress.length : 0;

  return { overallProgress, metricProgress };
}

/**
 * Rolls back to a previous version
 */
export function rollbackToVersion(
  history: VersionHistory,
  targetVersion: number,
  userId: string
): GoalVersion | null {
  const version = history.versions.find((v) => v.version === targetVersion);
  if (!version) return null;

  // Create a new version based on the target version
  const rollbackVersion = createGoalVersion(
    history.versions[history.versions.length - 1],
    {
      title: version.title,
      description: version.description,
      metrics: version.metrics,
      timeline: version.timeline,
      status: "draft",
    },
    `Rolled back to version ${targetVersion}`,
    userId
  );

  return rollbackVersion;
}

/**
 * Creates a branch from a specific version for what-if scenarios
 */
export function createBranch(
  history: VersionHistory,
  sourceVersion: number,
  branchName: string,
  userId: string
): { history: VersionHistory; branchVersion: GoalVersion } | null {
  const version = history.versions.find((v) => v.version === sourceVersion);
  if (!version) return null;

  const branchVersion = createGoalVersion(
    version,
    {
      title: `${version.title} (${branchName})`,
      status: "draft",
    },
    `Branched from version ${sourceVersion}: ${branchName}`,
    userId
  );

  const updatedHistory = {
    ...history,
    branches: {
      ...history.branches,
      [branchName]: [branchVersion.version],
    },
  };

  return { history: updatedHistory, branchVersion };
}

/**
 * Suggests improvements based on goal analysis
 */
export function suggestGoalImprovements(goal: GoalVersion): string[] {
  const suggestions: string[] = [];

  // Check metric granularity
  if (goal.metrics.length < 2) {
    suggestions.push("Consider adding 2-3 complementary metrics to track different aspects of success");
  }

  // Check for leading vs. lagging indicators
  const hasLeadingIndicators = goal.metrics.some(
    (m) => m.name.toLowerCase().includes("activity") || m.name.toLowerCase().includes("rate")
  );
  if (!hasLeadingIndicators) {
    suggestions.push(
      "Add leading indicators (activities that drive results) in addition to lagging indicators (final outcomes)"
    );
  }

  // Check timeline
  if (goal.timeline) {
    const months = extractMonths(goal.timeline);
    if (months > 12) {
      suggestions.push("Consider breaking this into shorter milestones (3-6 month increments) for better tracking");
    } else if (months < 1) {
      suggestions.push("This timeline may be too aggressive. Consider allowing more time for sustainable results");
    }
  }

  // Check target ambition
  goal.metrics.forEach((metric) => {
    if (
      typeof metric.baseline === "number" &&
      typeof metric.target === "number" &&
      Math.abs((metric.target - metric.baseline) / metric.baseline) < 0.05
    ) {
      suggestions.push(`Target for "${metric.name}" is only a 5% improvement - consider a more ambitious goal`);
    }
  });

  return suggestions;
}

/**
 * Extracts number of months from timeline string
 */
function extractMonths(timeline: string): number {
  const match = timeline.match(/(\d+)\s*(month|months|quarter|quarters|year|years)/i);
  if (!match) return 6; // default

  const num = parseInt(match[1]);
  const unit = match[2].toLowerCase();

  if (unit.startsWith("year")) return num * 12;
  if (unit.startsWith("quarter")) return num * 3;
  return num;
}
