import { X, Sparkles, Building2, Target, Zap, DollarSign, Globe } from "lucide-react";
import { useState, useEffect } from "react";
import { TenantProfile } from "../lib/api";

type PreferencesState = {
  businessType: Set<string>;
  objectiveFocus: Set<string>;
  operatingPace: Set<string>;
  budget: Set<string>;
  markets: Set<string>;
  otherNeeds: string;
};

export type PreferencesModalProps = {
  open: boolean;
  onClose: () => void;
  onConfirm: (summary: string, prefs: PreferencesState) => void;
  profile?: TenantProfile | null;
};

const BUSINESS_TYPES = [
  { id: "Restaurant", icon: "🍽️", label: "Restaurant" },
  { id: "Retail", icon: "🛍️", label: "Retail" },
  { id: "eCommerce", icon: "📦", label: "eCommerce" },
  { id: "Services", icon: "🔧", label: "Services" },
  { id: "Manufacturing", icon: "🏭", label: "Manufacturing" },
  { id: "Healthcare", icon: "🏥", label: "Healthcare" },
  { id: "Technology", icon: "💻", label: "Technology" },
  { id: "Hospitality", icon: "🏨", label: "Hospitality" },
];

const OBJECTIVE_FOCUS = [
  { id: "Reduce Cost", icon: "💰", label: "Reduce Cost", description: "Lower operational expenses" },
  { id: "Increase Revenue", icon: "📈", label: "Increase Revenue", description: "Grow sales and profits" },
  { id: "Improve Service", icon: "⭐", label: "Improve Service", description: "Enhance customer experience" },
  { id: "Reduce Carbon", icon: "🌱", label: "Reduce Carbon", description: "Sustainability initiatives" },
  { id: "Scale Operations", icon: "🚀", label: "Scale Operations", description: "Expand capacity" },
  { id: "Digital Transform", icon: "🔄", label: "Digital Transform", description: "Modernize processes" },
];

const OPERATING_PACE = [
  { id: "Ambitious", icon: "⚡", label: "Ambitious", description: "Fast-paced, aggressive timelines" },
  { id: "Conservative", icon: "🛡️", label: "Conservative", description: "Steady, risk-averse approach" },
  { id: "Pilot-first", icon: "🧪", label: "Pilot-first", description: "Test before scaling" },
];

const BUDGET = [
  { id: "Lean", icon: "💵", label: "Lean", description: "Minimal investment" },
  { id: "Standard", icon: "💳", label: "Standard", description: "Moderate budget" },
  { id: "Premium", icon: "💎", label: "Premium", description: "Significant investment" },
];

const MARKETS = [
  { id: "Local", label: "Local" },
  { id: "Multi-city", label: "Multi-city" },
  { id: "Online", label: "Online" },
  { id: "US", label: "US" },
  { id: "EU", label: "EU" },
  { id: "APAC", label: "APAC" },
  { id: "Global", label: "Global" },
];

// Auto-detect business type from profile
function detectBusinessType(profile?: TenantProfile | null): Set<string> {
  if (!profile?.name) return new Set();
  
  const name = profile.name.toLowerCase();
  const metadata = (profile as any).metadata || {};
  
  // Check metadata first
  if (metadata.business_type) {
    return new Set([metadata.business_type]);
  }
  
  // Heuristic detection from company name
  if (name.includes("restaurant") || name.includes("cafe") || name.includes("food")) {
    return new Set(["Restaurant"]);
  }
  if (name.includes("shop") || name.includes("store") || name.includes("retail")) {
    return new Set(["Retail"]);
  }
  if (name.includes("tech") || name.includes("software") || name.includes("saas")) {
    return new Set(["Technology"]);
  }
  if (name.includes("hotel") || name.includes("resort")) {
    return new Set(["Hospitality"]);
  }
  if (name.includes("hospital") || name.includes("clinic") || name.includes("medical")) {
    return new Set(["Healthcare"]);
  }
  
  return new Set();
}

// Generate suggested objectives based on business type and profile
function generateSuggestedObjectives(profile?: TenantProfile | null, businessType?: Set<string>): Set<string> {
  const suggestions = new Set<string>();
  
  const metadata = (profile as any)?.metadata || {};
  if (metadata.primary_goal) {
    suggestions.add(metadata.primary_goal);
  }
  
  // Add common objectives based on business type
  const type = Array.from(businessType || [])[0];
  if (type === "Restaurant" || type === "Retail") {
    suggestions.add("Reduce Cost");
    suggestions.add("Improve Service");
  } else if (type === "Technology" || type === "eCommerce") {
    suggestions.add("Scale Operations");
    suggestions.add("Increase Revenue");
  } else if (type === "Manufacturing") {
    suggestions.add("Reduce Cost");
    suggestions.add("Reduce Carbon");
  }
  
  return suggestions;
}

export function PreferencesModal({ open, onClose, onConfirm, profile }: PreferencesModalProps) {
  const [step, setStep] = useState(1);
  const [prefs, setPrefs] = useState<PreferencesState>({
    businessType: new Set(),
    objectiveFocus: new Set(),
    operatingPace: new Set(),
    budget: new Set(),
    markets: new Set(),
    otherNeeds: "",
  });

  // Auto-populate preferences from profile on mount
  useEffect(() => {
    if (open && profile) {
      const detectedType = detectBusinessType(profile);
      const suggestedObjectives = generateSuggestedObjectives(profile, detectedType);
      
      setPrefs((prev) => ({
        ...prev,
        businessType: detectedType,
        objectiveFocus: suggestedObjectives,
        // Smart defaults based on plan tier
        budget: new Set([profile.plan.tier === "free" ? "Lean" : profile.plan.tier === "platinum" ? "Premium" : "Standard"]),
        markets: new Set(["Local"]), // Default to local unless specified
      }));
    }
  }, [open, profile]);

  function toggleSet<K extends keyof PreferencesState>(key: K, value: string) {
    setPrefs((prev) => {
      const next = new Set(prev[key] as Set<string>);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  }

  const handleConfirm = () => {
    const parts: string[] = [];
    if (prefs.businessType.size) parts.push(`Business: ${Array.from(prefs.businessType).join(", ")}`);
    if (prefs.objectiveFocus.size) parts.push(`Focus: ${Array.from(prefs.objectiveFocus).join(", ")}`);
    if (prefs.operatingPace.size) parts.push(`Pace: ${Array.from(prefs.operatingPace).join(", ")}`);
    if (prefs.budget.size) parts.push(`Budget: ${Array.from(prefs.budget).join(", ")}`);
    if (prefs.markets.size) parts.push(`Markets: ${Array.from(prefs.markets).join(", ")}`);
    if (prefs.otherNeeds.trim()) parts.push(`Notes: ${prefs.otherNeeds.trim()}`);

    const summary = parts.length ? parts.join(" • ") : "No preferences set";
    onConfirm(summary, prefs);
    onClose();
  };

  const handleClear = () => {
    setPrefs({
      businessType: new Set(),
      objectiveFocus: new Set(),
      operatingPace: new Set(),
      budget: new Set(),
      markets: new Set(),
      otherNeeds: "",
    });
    setStep(1);
  };

  if (!open) return null;

  const totalSteps = 5;
  const progress = (step / totalSteps) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl rounded-2xl bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="border-b bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <Sparkles size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Set Your Preferences</h2>
                <p className="text-sm text-gray-600">Help us personalize your business plan</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-gray-100"
            >
              <X size={20} className="text-gray-500" />
            </button>
          </div>
          
          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex justify-between text-xs font-medium text-gray-600 mb-2">
              <span>Step {step} of {totalSteps}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-200">
              <div
                className="h-full bg-gradient-to-r from-primary to-purple-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto px-6 py-6">
          {/* Step 1: Business Type */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                <Building2 size={16} />
                Business Type
              </div>
              <p className="text-sm text-gray-600">What type of business do you operate?</p>
              <div className="grid grid-cols-2 gap-3">
                {BUSINESS_TYPES.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => {
                      // Single selection for business type
                      setPrefs((p) => ({ ...p, businessType: new Set([opt.id]) }));
                    }}
                    className={`flex items-center gap-3 rounded-xl border-2 p-4 text-left transition-all ${
                      prefs.businessType.has(opt.id)
                        ? "border-primary bg-blue-50 shadow-md"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-2xl">{opt.icon}</span>
                    <span className="font-medium text-gray-900">{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Objective Focus */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                <Target size={16} />
                What's Your Main Goal?
              </div>
              <p className="text-sm text-gray-600">Choose one or more objectives (we pre-selected recommendations)</p>
              <div className="space-y-3">
                {OBJECTIVE_FOCUS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => toggleSet("objectiveFocus", opt.id)}
                    className={`flex w-full items-start gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                      prefs.objectiveFocus.has(opt.id)
                        ? "border-primary bg-blue-50 shadow-md"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-2xl">{opt.icon}</span>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{opt.label}</div>
                      <div className="text-sm text-gray-600">{opt.description}</div>
                    </div>
                    {prefs.objectiveFocus.has(opt.id) && (
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white">
                        <span className="text-xs">✓</span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Operating Pace */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                <Zap size={16} />
                Implementation Pace
              </div>
              <p className="text-sm text-gray-600">How fast do you want to move?</p>
              <div className="space-y-3">
                {OPERATING_PACE.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setPrefs((p) => ({ ...p, operatingPace: new Set([opt.id]) }))}
                    className={`flex w-full items-start gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                      prefs.operatingPace.has(opt.id)
                        ? "border-primary bg-blue-50 shadow-md"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-2xl">{opt.icon}</span>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{opt.label}</div>
                      <div className="text-sm text-gray-600">{opt.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: Budget */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                <DollarSign size={16} />
                Budget Range
              </div>
              <p className="text-sm text-gray-600">What's your investment capacity?</p>
              <div className="space-y-3">
                {BUDGET.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setPrefs((p) => ({ ...p, budget: new Set([opt.id]) }))}
                    className={`flex w-full items-start gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                      prefs.budget.has(opt.id)
                        ? "border-primary bg-blue-50 shadow-md"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-2xl">{opt.icon}</span>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{opt.label}</div>
                      <div className="text-sm text-gray-600">{opt.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 5: Markets & Other Needs */}
          {step === 5 && (
            <div className="space-y-6">
              <div>
                <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                  <Globe size={16} />
                  Markets You Serve
                </div>
                <div className="flex flex-wrap gap-2">
                  {MARKETS.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => toggleSet("markets", opt.id)}
                      className={`rounded-full border-2 px-4 py-2 text-sm font-medium transition-all ${
                        prefs.markets.has(opt.id)
                          ? "border-primary bg-blue-50 text-primary"
                          : "border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-2 text-sm font-semibold text-gray-900">Any Other Needs or Constraints?</div>
                <textarea
                  className="w-full rounded-xl border-2 border-gray-200 p-4 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  rows={4}
                  maxLength={1000}
                  placeholder="E.g., limited staff, seasonal business, supply chain issues..."
                  value={prefs.otherNeeds}
                  onChange={(e) => setPrefs((p) => ({ ...p, otherNeeds: e.target.value }))}
                />
                <div className="text-right text-xs text-gray-400">{prefs.otherNeeds.length}/1000</div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t bg-gray-50 px-6 py-4">
          <div className="flex gap-2">
            {step > 1 && (
              <button
                onClick={() => setStep((s) => Math.max(1, s - 1))}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                Back
              </button>
            )}
            <button
              onClick={handleClear}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              Clear All
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              Cancel
            </button>
            {step < totalSteps ? (
              <button
                onClick={() => setStep((s) => Math.min(totalSteps, s + 1))}
                className="rounded-lg bg-primary px-6 py-2 text-sm font-semibold text-white shadow-lg hover:bg-primary/90"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleConfirm}
                className="rounded-lg bg-gradient-to-r from-primary to-purple-600 px-6 py-2 text-sm font-semibold text-white shadow-lg hover:from-primary/90 hover:to-purple-600/90"
              >
                Generate Plan
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
