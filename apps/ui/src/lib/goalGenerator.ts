import { TenantProfile, getPlaybookRecommendations, PlaybookRecommendation } from "../lib/api";

type BusinessProfile = {
  businessType: string;
  objectives: string[];
  pace: string;
  budget: string;
  markets: string[];
};

export type SuggestedGoal = {
  id: string;
  title: string;
  description: string;
  rationale: string;
  icon: string;
  priority: "high" | "medium" | "low";
  estimatedDuration: string;
  expectedImpact: string;
  template_id?: string;
};

// Goal templates based on business type and objectives
const GOAL_TEMPLATES: Record<string, Record<string, SuggestedGoal[]>> = {
  Restaurant: {
    "Reduce Cost": [
      {
        id: "rest-cost-1",
        title: "Optimize Inventory Management",
        description: "Reduce food waste and holding costs by 40% through better forecasting and ordering",
        rationale: "Restaurants typically waste 4-10% of food inventory. Smart ordering can save $2-5k/month.",
        icon: "📦",
        priority: "high",
        estimatedDuration: "4-6 weeks",
        expectedImpact: "15-20% cost reduction",
      },
      {
        id: "rest-cost-2",
        title: "Reduce Energy Consumption",
        description: "Lower utility bills by 25% with equipment upgrades and usage optimization",
        rationale: "Energy costs are 3-5% of revenue. Simple changes can yield immediate savings.",
        icon: "⚡",
        priority: "medium",
        estimatedDuration: "6-8 weeks",
        expectedImpact: "10-15% energy cost reduction",
      },
    ],
    "Improve Service": [
      {
        id: "rest-service-1",
        title: "Streamline Kitchen Operations",
        description: "Reduce wait times by 30% with optimized workflows and prep schedules",
        rationale: "Faster service increases table turns and customer satisfaction.",
        icon: "⏱️",
        priority: "high",
        estimatedDuration: "3-4 weeks",
        expectedImpact: "25-30% faster service",
      },
    ],
    "Increase Revenue": [
      {
        id: "rest-revenue-1",
        title: "Implement Online Ordering System",
        description: "Add 15-20% revenue stream through delivery and takeout optimization",
        rationale: "60% of customers prefer online ordering. Capture this untapped market.",
        icon: "📱",
        priority: "high",
        estimatedDuration: "4-6 weeks",
        expectedImpact: "15-25% revenue increase",
      },
    ],
  },
  Retail: {
    "Reduce Cost": [
      {
        id: "retail-cost-1",
        title: "Optimize Stock Levels",
        description: "Keep the right stock without over-investing capital in slow-moving items",
        rationale: "Excess inventory ties up 20-30% of working capital unnecessarily.",
        icon: "📊",
        priority: "high",
        estimatedDuration: "4-6 weeks",
        expectedImpact: "20-30% inventory reduction",
      },
    ],
    "Increase Revenue": [
      {
        id: "retail-revenue-1",
        title: "Launch Omnichannel Strategy",
        description: "Integrate online and in-store experience to capture 40% more customers",
        rationale: "73% of shoppers use multiple channels. Unified experience drives sales.",
        icon: "🛒",
        priority: "high",
        estimatedDuration: "8-12 weeks",
        expectedImpact: "30-40% revenue growth",
      },
    ],
  },
  eCommerce: {
    "Scale Operations": [
      {
        id: "ecom-scale-1",
        title: "Automate Order Fulfillment",
        description: "Process 3x more orders with same team through automation and optimization",
        rationale: "Manual fulfillment becomes bottleneck at scale. Automation enables growth.",
        icon: "🤖",
        priority: "high",
        estimatedDuration: "6-8 weeks",
        expectedImpact: "3x capacity increase",
      },
    ],
    "Increase Revenue": [
      {
        id: "ecom-revenue-1",
        title: "Implement Personalization Engine",
        description: "Boost conversion rate by 25% with AI-powered product recommendations",
        rationale: "Personalized experiences drive 2-3x higher engagement and sales.",
        icon: "🎯",
        priority: "high",
        estimatedDuration: "6-10 weeks",
        expectedImpact: "20-30% conversion lift",
      },
    ],
  },
  Technology: {
    "Scale Operations": [
      {
        id: "tech-scale-1",
        title: "Build Self-Service Onboarding",
        description: "Reduce onboarding time from 2 weeks to 2 hours with automation",
        rationale: "Manual onboarding limits growth. Self-service scales infinitely.",
        icon: "🚀",
        priority: "high",
        estimatedDuration: "8-12 weeks",
        expectedImpact: "10x onboarding capacity",
      },
    ],
    "Reduce Cost": [
      {
        id: "tech-cost-1",
        title: "Optimize Cloud Infrastructure",
        description: "Cut cloud costs by 40% through rightsizing and reserved instances",
        rationale: "Most companies overpay 35-50% on cloud. Quick wins available.",
        icon: "☁️",
        priority: "high",
        estimatedDuration: "3-4 weeks",
        expectedImpact: "30-40% cost savings",
      },
    ],
  },
  Manufacturing: {
    "Reduce Cost": [
      {
        id: "mfg-cost-1",
        title: "Implement Predictive Maintenance",
        description: "Reduce downtime by 50% and maintenance costs by 30% with IoT sensors",
        rationale: "Unplanned downtime costs $50k-$1M per hour. Prevention is cheaper.",
        icon: "🔧",
        priority: "high",
        estimatedDuration: "10-12 weeks",
        expectedImpact: "40-50% downtime reduction",
      },
    ],
    "Reduce Carbon": [
      {
        id: "mfg-carbon-1",
        title: "Energy Efficiency Program",
        description: "Reduce carbon footprint by 35% through process optimization and renewables",
        rationale: "Energy is 10-30% of manufacturing costs. Efficiency helps planet and profit.",
        icon: "🌱",
        priority: "medium",
        estimatedDuration: "12-16 weeks",
        expectedImpact: "30-40% emissions reduction",
      },
    ],
  },
  Services: {
    "Improve Service": [
      {
        id: "svc-service-1",
        title: "Implement Client Portal",
        description: "Increase client satisfaction by 40% with self-service tracking and communication",
        rationale: "Clients want visibility. Portals reduce support load by 50%.",
        icon: "💬",
        priority: "high",
        estimatedDuration: "6-8 weeks",
        expectedImpact: "40% satisfaction increase",
      },
    ],
    "Scale Operations": [
      {
        id: "svc-scale-1",
        title: "Standardize Service Delivery",
        description: "Create repeatable processes to serve 5x more clients with same quality",
        rationale: "Custom work doesn't scale. Standardization enables growth.",
        icon: "📋",
        priority: "high",
        estimatedDuration: "8-10 weeks",
        expectedImpact: "5x scalability",
      },
    ],
  },
};

// Fallback generic goals if no specific match
const GENERIC_GOALS: SuggestedGoal[] = [
  {
    id: "generic-1",
    title: "Improve Operational Efficiency",
    description: "Identify and eliminate bottlenecks in your core business processes",
    rationale: "Most businesses have 20-40% efficiency gaps that can be closed.",
    icon: "⚙️",
    priority: "high",
    estimatedDuration: "6-8 weeks",
    expectedImpact: "20-30% efficiency gain",
  },
  {
    id: "generic-2",
    title: "Enhance Customer Experience",
    description: "Create better touchpoints throughout the customer journey",
    rationale: "Happy customers spend 67% more and refer others.",
    icon: "😊",
    priority: "high",
    estimatedDuration: "4-6 weeks",
    expectedImpact: "30% satisfaction boost",
  },
  {
    id: "generic-3",
    title: "Data-Driven Decision Making",
    description: "Build dashboards and analytics to make informed business decisions",
    rationale: "Data-driven companies are 5-6% more productive.",
    icon: "📈",
    priority: "medium",
    estimatedDuration: "6-10 weeks",
    expectedImpact: "Better strategic decisions",
  },
];

/**
 * Generate goal suggestions using backend AI recommendations
 * Falls back to templates if backend is unavailable
 */
export async function generateSuggestedGoalsFromBackend(
  profile: TenantProfile | null,
  businessProfile: BusinessProfile
): Promise<SuggestedGoal[]> {
  try {
    // Try to get real recommendations from backend
    const response = await getPlaybookRecommendations();
    
    if (response.recommendations && response.recommendations.length > 0) {
      // Convert PlaybookRecommendation to SuggestedGoal format
      return response.recommendations.map((rec: PlaybookRecommendation) => ({
        id: rec.id,
        title: rec.title,
        description: rec.description,
        rationale: `Recommended based on your industry profile. ${rec.tags.join(", ")}.`,
        icon: rec.icon,
        priority: "high" as const,
        estimatedDuration: rec.estimated_time,
        expectedImpact: "Strategic business improvement",
        template_id: rec.template_id,
      }));
    }
  } catch (error) {
    console.warn("Failed to fetch backend recommendations, using fallback templates:", error);
  }
  
  // Fallback to template-based generation
  return generateSuggestedGoals(profile, businessProfile);
}

export function generateSuggestedGoals(
  profile: TenantProfile | null,
  businessProfile: BusinessProfile
): SuggestedGoal[] {
  const { businessType, objectives, pace, budget } = businessProfile;
  
  const suggestions: SuggestedGoal[] = [];
  const businessTemplates = GOAL_TEMPLATES[businessType] || {};

  // Get goals for each objective
  objectives.forEach((objective) => {
    const objectiveGoals = businessTemplates[objective] || [];
    suggestions.push(...objectiveGoals);
  });

  // If no specific goals found, add generic ones
  if (suggestions.length === 0) {
    suggestions.push(...GENERIC_GOALS.slice(0, 3));
  }

  // Adjust based on pace and budget
  return suggestions
    .map((goal) => {
      let adjustedGoal = { ...goal };
      
      // Adjust priority based on pace
      if (pace === "Ambitious" && goal.priority === "medium") {
        adjustedGoal.priority = "high";
      } else if (pace === "Conservative" && goal.priority === "high") {
        adjustedGoal.priority = "medium";
      }

      // Add budget consideration to rationale
      if (budget === "Lean") {
        adjustedGoal.rationale += " Low initial investment required.";
      } else if (budget === "Premium") {
        adjustedGoal.rationale += " We can leverage premium tools for faster results.";
      }

      return adjustedGoal;
    })
    .sort((a, b) => {
      // Sort by priority
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    })
    .slice(0, 5); // Return top 5 suggestions
}

// Generate a complete goal statement based on selected suggested goal
export function generateGoalStatement(goal: SuggestedGoal, businessProfile: BusinessProfile): string {
  const { businessType, markets } = businessProfile;
  const marketStr = markets.length > 0 ? ` across ${markets.join(", ")} markets` : "";
  
  return `${goal.title}: ${goal.description}${marketStr}. Expected outcome: ${goal.expectedImpact} in ${goal.estimatedDuration}.`;
}
