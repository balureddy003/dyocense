import { useEffect, useState } from "react";
import { CheckCircle2, Headset, Mail, Shield, Copy, Check } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  listPlans,
  registerTenant,
  getOnboardingDetails,
  SubscriptionPlan,
  TenantRegistrationPayload,
  OnboardingDetails,
} from "../lib/api";
import { setAuthToken } from "../lib/config";

const FALLBACK_PLANS: SubscriptionPlan[] = [
  {
    tier: "free",
    name: "Free",
    price_per_month: 0,
    description: "Get started with sample data.",
    limits: { max_projects: 1, max_playbooks: 3, max_members: 2, support_level: "Community" },
    features: ["1 active project", "3 playbooks", "Community support"],
  },
  {
    tier: "silver",
    name: "Silver Trial",
    price_per_month: 149,
    description: "7-day free trial with full access.",
    limits: { max_projects: 5, max_playbooks: 25, max_members: 15, support_level: "Business-hours" },
    features: ["5 projects", "25 playbooks", "Business-hours support", "Export features", "7-day free trial"],
  },
];

type Step = "plans" | "details" | "success";

export const PurchasePage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState<Step>("plans");
  const [plans, setPlans] = useState<SubscriptionPlan[]>(FALLBACK_PLANS);
  const [selectedTier, setSelectedTier] = useState<string>("free");
  const [formData, setFormData] = useState({ org_name: "", email: user?.email || "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingDetails | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Check for plan parameter in URL (trial or free)
    const planParam = searchParams.get("plan");
    if (planParam === "trial") {
      setSelectedTier("silver");
      setStep("details");
    } else if (planParam === "free") {
      setSelectedTier("free");
      setStep("details");
    }
    
    listPlans(FALLBACK_PLANS)
      .then((data) => {
        if (data.length) setPlans(data);
      })
      .catch((err) => {
        console.warn("Failed to load plans", err);
      });
  }, [searchParams]);

  const selectedPlan = plans.find((p) => p.tier === selectedTier);

  const handleSelectPlan = (tier: string) => {
    setSelectedTier(tier);
    setStep("details");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlan || !formData.org_name || !formData.email) {
      setError("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload: TenantRegistrationPayload = {
        name: formData.org_name.trim(),
        owner_email: formData.email.trim(),
        plan_tier: selectedPlan.tier,
        metadata: {},
      };

      const registrationResponse = await registerTenant(payload);
      
      // Store the API token so subsequent calls are authenticated
      setAuthToken(registrationResponse.api_token);

      // Fetch onboarding details (now authenticated with the token)
      const details = await getOnboardingDetails();
      setOnboarding(details);
      setStep("success");
    } catch (err: any) {
      console.error("Registration failed:", err);
      setError(err?.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Start Building Smarter</h1>
          <p className="text-lg text-gray-600">Choose your plan and get instant access to AI-powered decision making.</p>
        </div>

        {step === "plans" && (
          <div className="grid gap-6 md:grid-cols-2 mb-12">
            {plans.map((plan) => (
              <button
                key={plan.tier}
                onClick={() => handleSelectPlan(plan.tier)}
                className="p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-blue-500 hover:shadow-lg transition text-left"
              >
                <h3 className="text-2xl font-bold text-gray-900 mb-1">{plan.name}</h3>
                <p className="text-3xl font-bold text-blue-600 mb-4">
                  ${plan.price_per_month}
                  <span className="text-sm text-gray-600">/month</span>
                </p>
                <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-gray-700">
                      <CheckCircle2 size={16} className="text-green-600" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button className="w-full py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition">
                  Get Started
                </button>
              </button>
            ))}
          </div>
        )}

        {step === "details" && (
          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Complete Your Registration</h2>

            {error && <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Organization Name *</label>
                <input
                  type="text"
                  required
                  value={formData.org_name}
                  onChange={(e) => setFormData({ ...formData, org_name: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  placeholder="Your company name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                  placeholder="your@email.com"
                />
              </div>

              <div className="pt-4 space-x-3 flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep("plans")}
                  className="flex-1 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition disabled:bg-gray-400"
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </div>
            </form>
          </div>
        )}

        {step === "success" && onboarding && (
          <div className="bg-white rounded-2xl border border-green-200 p-8 space-y-6">
            <div className="text-center mb-6">
              <div className="inline-block p-3 bg-green-100 rounded-full mb-4">
                <CheckCircle2 size={32} className="text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome to Dyocense!</h2>
              <p className="text-gray-600 mt-2">Your account is ready. Here's what you need to know:</p>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm font-semibold text-gray-700 mb-2">Tenant ID</p>
                <div className="flex items-center justify-between">
                  <code className="text-sm text-gray-900 break-all">{onboarding.tenant_id}</code>
                  <button
                    onClick={() => copyToClipboard(onboarding.tenant_id)}
                    className="ml-2 p-2 hover:bg-blue-100 rounded"
                  >
                    {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} className="text-gray-600" />}
                  </button>
                </div>
              </div>

              {onboarding.temporary_password && (
                <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Temporary Password</p>
                  <div className="flex items-center justify-between">
                    <code className="text-sm text-gray-900">{onboarding.temporary_password}</code>
                    <button
                      onClick={() => copyToClipboard(onboarding.temporary_password || "")}
                      className="ml-2 p-2 hover:bg-amber-100 rounded"
                    >
                      {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} className="text-gray-600" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">Use this to login. You'll be asked to set a new password.</p>
                </div>
              )}

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm font-semibold text-gray-700 mb-2">Next Steps</p>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Check your email for onboarding details</li>
                  <li>Login with your temporary password</li>
                  <li>Set a permanent password</li>
                  <li>Start creating your first playbook</li>
                </ol>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                onClick={() => navigate(`/login?tenant=${encodeURIComponent(onboarding.tenant_id)}&email=${encodeURIComponent(onboarding.email)}`)}
                className="flex-1 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
              >
                Go to Login
              </button>
              <button
                onClick={() => navigate("/")}
                className="flex-1 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition"
              >
                Back to Home
              </button>
            </div>
          </div>
        )}

        {/* Support Section */}
        <div className="mt-12 grid gap-6 md:grid-cols-3 text-center">
          <div className="p-4">
            <Mail size={24} className="mx-auto text-blue-600 mb-2" />
            <p className="font-semibold text-gray-900">Email Support</p>
            <p className="text-sm text-gray-600">hello@dyocense.ai</p>
          </div>
          <div className="p-4">
            <Headset size={24} className="mx-auto text-blue-600 mb-2" />
            <p className="font-semibold text-gray-900">Live Support</p>
            <p className="text-sm text-gray-600">For Silver+ plans</p>
          </div>
          <div className="p-4">
            <Shield size={24} className="mx-auto text-blue-600 mb-2" />
            <p className="font-semibold text-gray-900">Secure & Compliant</p>
            <p className="text-sm text-gray-600">SOC2 & GDPR Ready</p>
          </div>
        </div>
      </div>
    </div>
  );
};
