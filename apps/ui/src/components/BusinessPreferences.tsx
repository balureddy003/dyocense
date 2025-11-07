/**
 * BusinessPreferences - Step 2 of onboarding
 * Multi-step preferences collection (Business Type, Team Size, Goals, etc.)
 */

import { useState, useEffect } from "react";
import { Industry } from "./IndustrySelector";
import { 
  Coffee, ShoppingBag, Briefcase, Package, Wrench, Store,
  Users, Target, TrendingUp, DollarSign, Clock, CheckCircle2
} from "lucide-react";

// Added "other" so we can map Industry "other" directly without forcing a different choice.
type BusinessType = 
  | "restaurant" | "retail" | "ecommerce" | "services" 
  | "manufacturing" | "healthcare" | "technology" | "hospitality" | "other";

type TeamSize = "1" | "2-5" | "6-10" | "11-20" | "21-50" | "51+";

type PrimaryGoal = 
  | "reduce-costs" | "increase-revenue" | "improve-cashflow" 
  | "optimize-inventory" | "expand-business" | "automate-processes";

type PreferenceData = {
  businessType?: BusinessType;
  teamSize?: TeamSize;
  primaryGoal?: PrimaryGoal;
  monthlyRevenue?: string;
  topChallenges?: string[];
};

type BusinessPreferencesProps = {
  industry?: Industry;
  onComplete: (data: PreferenceData) => void;
  onSkip: () => void;
};

export function BusinessPreferences({ industry, onComplete, onSkip }: BusinessPreferencesProps) {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<PreferenceData>({});

  const businessTypes: Array<{ id: BusinessType; label: string; icon: React.ReactNode }> = [
    { id: "restaurant", label: "Restaurant", icon: <Coffee size={24} /> },
    { id: "retail", label: "Retail", icon: <ShoppingBag size={24} /> },
    { id: "ecommerce", label: "eCommerce", icon: <Package size={24} /> },
    { id: "services", label: "Services", icon: <Briefcase size={24} /> },
    { id: "manufacturing", label: "Manufacturing", icon: <Package size={24} /> },
    { id: "healthcare", label: "Healthcare", icon: <Store size={24} /> },
    { id: "technology", label: "Technology", icon: <Store size={24} /> },
    { id: "hospitality", label: "Hospitality", icon: <Store size={24} /> },
    { id: "other", label: "Other", icon: <Store size={24} /> },
  ];

  // If an industry was selected in the previous step, auto-map it to a businessType and skip step 1.
  useEffect(() => {
    if (industry && !data.businessType) {
      const map: Record<string, BusinessType> = {
        restaurant: "restaurant",
        retail: "retail",
        services: "services",
        cpg: "manufacturing",
        logistics: "logistics" as BusinessType, // logistics not directly in union, treat via manufacturing or other if needed
        other: "other",
      };
      const mapped = map[industry];
      if (mapped) {
        setData(d => ({ ...d, businessType: mapped }));
        // Advance to next step so user isn't asked again
        setStep(2);
      }
    }
  }, [industry, data.businessType]);

  const teamSizes: Array<{ id: TeamSize; label: string }> = [
    { id: "1", label: "Just me" },
    { id: "2-5", label: "2-5 people" },
    { id: "6-10", label: "6-10 people" },
    { id: "11-20", label: "11-20 people" },
    { id: "21-50", label: "21-50 people" },
    { id: "51+", label: "51+ people" },
  ];

  const goals: Array<{ id: PrimaryGoal; label: string; icon: React.ReactNode }> = [
    { id: "reduce-costs", label: "Reduce costs", icon: <DollarSign size={20} /> },
    { id: "increase-revenue", label: "Increase revenue", icon: <TrendingUp size={20} /> },
    { id: "improve-cashflow", label: "Improve cash flow", icon: <Clock size={20} /> },
    { id: "optimize-inventory", label: "Optimize inventory", icon: <Package size={20} /> },
    { id: "expand-business", label: "Expand business", icon: <Target size={20} /> },
    { id: "automate-processes", label: "Automate processes", icon: <CheckCircle2 size={20} /> },
  ];

  const handleBusinessTypeSelect = (type: BusinessType) => {
    setData({ ...data, businessType: type });
  };

  const handleTeamSizeSelect = (size: TeamSize) => {
    setData({ ...data, teamSize: size });
  };

  const handleGoalSelect = (goal: PrimaryGoal) => {
    setData({ ...data, primaryGoal: goal });
  };

  const handleNext = () => {
    if (step < 5) {
      setStep(step + 1);
    } else {
      onComplete(data);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1: return !!data.businessType;
      case 2: return !!data.teamSize;
      case 3: return !!data.primaryGoal;
      case 4: return true; // Revenue is optional
      case 5: return true; // Challenges are optional
      default: return false;
    }
  };

  // When industry is provided, we effectively have 4 visible steps (team size, goal, revenue, challenges)
  const effectiveTotal = industry ? 4 : 5;
  const effectiveStep = industry ? Math.max(step - 1, 1) : step;
  const progressPercent = Math.round((effectiveStep / effectiveTotal) * 100);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4">
          <Target className="text-white" size={32} />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {(!industry && step === 1) && "What type of business?"}
          {(industry && step === 1) && "How big is your team?"}
          {(!industry && step === 2) && "How big is your team?"}
          {(!industry && step === 3) && "What's your main goal?"}
          {(!industry && step === 4) && "About your revenue"}
          {(!industry && step === 5) && "What keeps you up at night?"}
          {(industry && step === 2) && "What's your main goal?"}
          {(industry && step === 3) && "About your revenue"}
          {(industry && step === 4) && "What keeps you up at night?"}
        </h1>
        <p className="text-gray-600">
          {(!industry && step === 1) && "This helps us give you better recommendations"}
          {(industry && step === 1) && "Just to understand your scale"}
          {(!industry && step === 2) && "Just to understand your scale"}
          {(!industry && step === 3) && "What do you want to achieve first?"}
          {(!industry && step === 4) && "Optional - helps us personalize your plan"}
          {(!industry && step === 5) && "Select your biggest challenges (optional)"}
          {(industry && step === 2) && "What do you want to achieve first?"}
          {(industry && step === 3) && "Optional - helps us personalize your plan"}
          {(industry && step === 4) && "Select your biggest challenges (optional)"}
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center justify-center gap-2 mb-8">
        <span className="text-sm font-medium text-gray-600">Step {effectiveStep} of {effectiveTotal}</span>
        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <span className="text-sm font-medium text-gray-600">{progressPercent}%</span>
      </div>

      {/* Step Content */}
      <div className="min-h-[400px]">
        {/* Step 1: Business Type */}
        {/* Step 1 only shown when industry not pre-selected */}
        {step === 1 && !industry && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 mb-6">
              <Store className="text-blue-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">What type of business do you operate?</h3>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {businessTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => handleBusinessTypeSelect(type.id)}
                  className={`p-4 rounded-xl border-2 text-center transition-all hover:shadow-md ${
                    data.businessType === type.id
                      ? "border-blue-500 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-2 mx-auto ${
                    data.businessType === type.id ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"
                  }`}>
                    {type.icon}
                  </div>
                  <div className="font-semibold text-sm text-gray-900">{type.label}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Team Size */}
        {((!industry && step === 2) || (industry && step === 1)) && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 mb-6">
              <Users className="text-blue-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">How many people work at your business?</h3>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
              {teamSizes.map((size) => (
                <button
                  key={size.id}
                  onClick={() => handleTeamSizeSelect(size.id)}
                  className={`p-4 rounded-xl border-2 text-center transition-all hover:shadow-md ${
                    data.teamSize === size.id
                      ? "border-blue-500 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                >
                  <div className="font-semibold text-gray-900">{size.label}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Primary Goal */}
        {((!industry && step === 3) || (industry && step === 2)) && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 mb-6">
              <Target className="text-blue-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">What's your top priority right now?</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {goals.map((goal) => (
                <button
                  key={goal.id}
                  onClick={() => handleGoalSelect(goal.id)}
                  className={`p-4 rounded-xl border-2 flex items-center gap-3 transition-all hover:shadow-md ${
                    data.primaryGoal === goal.id
                      ? "border-blue-500 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    data.primaryGoal === goal.id ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"
                  }`}>
                    {goal.icon}
                  </div>
                  <div className="font-semibold text-gray-900">{goal.label}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Monthly Revenue (Optional) */}
        {((!industry && step === 4) || (industry && step === 3)) && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 mb-6">
              <DollarSign className="text-blue-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">What's your approximate monthly revenue?</h3>
            </div>
            
            <div className="max-w-md mx-auto space-y-3">
              {[
                { value: "0-10k", label: "$0 - $10,000" },
                { value: "10k-50k", label: "$10,000 - $50,000" },
                { value: "50k-100k", label: "$50,000 - $100,000" },
                { value: "100k-500k", label: "$100,000 - $500,000" },
                { value: "500k+", label: "$500,000+" },
                { value: "prefer-not", label: "Prefer not to say" },
              ].map((range) => (
                <button
                  key={range.value}
                  onClick={() => {
                    setData({ ...data, monthlyRevenue: range.value });
                  }}
                  className={`w-full p-4 rounded-xl border-2 text-left transition-all hover:shadow-md ${
                    data.monthlyRevenue === range.value
                      ? "border-blue-500 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                >
                  <div className="font-semibold text-gray-900">{range.label}</div>
                </button>
              ))}
            </div>
            
            <p className="text-sm text-gray-500 text-center mt-4">This helps us provide better recommendations</p>
          </div>
        )}

        {/* Step 5: Top Challenges (Optional) */}
        {((!industry && step === 5) || (industry && step === 4)) && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 mb-6">
              <CheckCircle2 className="text-blue-600" size={24} />
              <h3 className="text-lg font-bold text-gray-900">What challenges are you facing?</h3>
            </div>
            
            <p className="text-center text-gray-600 mb-4">Select all that apply</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {[
                "Managing cash flow",
                "Reducing costs",
                "Inventory management",
                "Hiring & staffing",
                "Customer acquisition",
                "Operational efficiency",
                "Competition",
                "Pricing strategy",
              ].map((challenge) => {
                const isSelected = data.topChallenges?.includes(challenge) || false;
                return (
                  <button
                    key={challenge}
                    onClick={() => {
                      const current = data.topChallenges || [];
                      const updated = isSelected
                        ? current.filter((c) => c !== challenge)
                        : [...current, challenge];
                      setData({ ...data, topChallenges: updated });
                    }}
                    className={`p-4 rounded-xl border-2 text-left transition-all hover:shadow-md ${
                      isSelected
                        ? "border-blue-500 bg-blue-50 shadow-lg"
                        : "border-gray-200 bg-white hover:border-blue-300"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                        isSelected ? "bg-blue-600 border-blue-600" : "border-gray-300"
                      }`}>
                        {isSelected && <CheckCircle2 className="text-white" size={14} />}
                      </div>
                      <div className="font-medium text-gray-900">{challenge}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onSkip}
          className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
        >
          I'll do this later
        </button>

        <div className="flex items-center gap-3">
          {((!industry && step > 1) || (industry && step > 2)) && (
            <button
              onClick={handleBack}
              className="px-6 py-2 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition-colors"
            >
              Back
            </button>
          )}
          
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              canProceed()
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            {((!industry && step === 5) || (industry && step === 4)) ? "Let's Go! 🚀" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
