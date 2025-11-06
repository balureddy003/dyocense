import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, MessageSquare, ArrowRight } from "lucide-react";
import { BusinessProfile, useAuth } from "../context/AuthContext";

const defaultProfile: BusinessProfile = {
  companyName: "",
  industry: "",
  teamSize: "",
  primaryGoal: "",
  timezone: "",
};

export const ProfileSetupPage = () => {
  const { profile, updateProfile, user, authenticated, ready } = useAuth();
  const navigate = useNavigate();

  const [businessDescription, setBusinessDescription] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (!authenticated) {
      navigate("/login", { replace: true });
      return;
    }
    if (profile) {
      navigate("/home", { replace: true });
    }
  }, [authenticated, profile, ready, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(true);
    
    if (!businessDescription.trim()) {
      return;
    }

    setIsProcessing(true);

    try {
      // Extract business information from the description using simple parsing
      // In a real implementation, you could call an LLM API here
      const profile: BusinessProfile = {
        companyName: extractBusinessName(businessDescription),
        industry: "small-business", // Generic category
        teamSize: extractTeamInfo(businessDescription),
        primaryGoal: businessDescription, // Keep the full description as the goal
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, // Auto-detect
      };

      await updateProfile(profile);
      navigate("/home", { replace: true });
    } catch (error) {
      console.error("Failed to save profile:", error);
      setIsProcessing(false);
    }
  };

  // Simple extraction - could be replaced with LLM call
  const extractBusinessName = (text: string): string => {
    // Look for common patterns like "I run/own/manage [business name]"
    const patterns = [
      /(?:i run|i own|i manage|i have)\s+(?:a\s+)?([^.,!?]+)/i,
      /(?:my|our)\s+([^.,!?]+\s+(?:restaurant|salon|shop|store|school|center|academy|parlour|business))/i,
      /^([^.,!?]+)(?:\s+is|\s+provides|\s+offers)/i,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    // Fallback: Use first few words or ask user's tenant name
    const words = text.trim().split(/\s+/);
    return words.slice(0, Math.min(3, words.length)).join(" ");
  };

  const extractTeamInfo = (text: string): string => {
    // Look for team size mentions
    const teamMatch = text.match(/(\d+)\s+(?:people|employees|staff|team members)/i);
    if (teamMatch) {
      return `${teamMatch[1]} people`;
    }
    
    // Look for team roles
    const roleMatch = text.match(/(?:with|including|for)\s+([^.,!?]*(?:sales|inventory|operations|kitchen|front desk|management)[^.,!?]*)/i);
    if (roleMatch) {
      return roleMatch[1].trim();
    }

    return "";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100 px-4 py-8">
      <div className="max-w-3xl w-full bg-white border border-gray-100 rounded-3xl shadow-xl p-8 md:p-12 space-y-8">
        <header className="space-y-4 text-center">
          <div className="flex items-center justify-center gap-2 text-primary">
            <Sparkles size={24} />
            <MessageSquare size={24} />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
            Tell us about your business
          </h1>
          <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto">
            In your own words, describe what you do. Our AI will understand and customize everything for you.
          </p>
        </header>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Describe your business in 1-2 sentences
            </label>
            <textarea
              className="w-full px-4 py-4 min-h-[180px] rounded-2xl border-2 border-gray-200 focus:border-primary focus:ring-4 focus:ring-primary/10 text-base transition-all resize-none"
              placeholder="For example:&#10;&#10;• I run a small Italian restaurant with 12 staff. We need help managing our food inventory and reducing waste.&#10;&#10;• We're a driving school with 5 instructors. We want to optimize our scheduling and track vehicle maintenance.&#10;&#10;• I own a nail salon with 3 technicians. I need better appointment booking and supply ordering."
              value={businessDescription}
              onChange={(e) => setBusinessDescription(e.target.value)}
              disabled={isProcessing}
            />
            {submitted && !businessDescription.trim() && (
              <span className="text-sm text-red-500">Please tell us a bit about your business</span>
            )}
            <p className="text-sm text-gray-500 flex items-start gap-2">
              <Sparkles size={14} className="mt-0.5 flex-shrink-0 text-primary" />
              <span>
                Don't worry about being formal! Just tell us what you do, how many people work with you, and what you're trying to improve. Our AI will figure out the rest.
              </span>
            </p>
          </div>

          {/* Suggested prompts */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">
              Need inspiration? Click to try:
            </p>
            <div className="grid gap-2 md:grid-cols-2">
              {[
                "I run a coffee shop with 8 baristas. We struggle with over-ordering milk and pastries.",
                "We're a tutoring center with 15 teachers. Need help scheduling classes and tracking student progress.",
                "Small retail boutique, 3 employees. Want to know which items to restock and when.",
                "Family-owned bakery. 6 staff. Need to predict daily demand for fresh bread and cakes.",
              ].map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="text-left px-4 py-3 rounded-xl border border-gray-200 text-sm text-gray-700 hover:border-primary hover:bg-blue-50 transition"
                  onClick={() => setBusinessDescription(example)}
                  disabled={isProcessing}
                >
                  <span className="line-clamp-2">{example}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center pt-6 border-t border-gray-100 gap-4">
            <div className="text-center sm:text-left">
              <p className="font-medium text-gray-800">{user?.fullName}</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
            <button
              type="submit"
              className="w-full sm:w-auto px-8 py-4 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Sparkles size={20} className="animate-spin" />
                  Setting up your workspace...
                </>
              ) : (
                <>
                  Continue to Dashboard
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </div>
        </form>

        <div className="pt-6 border-t border-gray-100">
          <div className="bg-blue-50 rounded-2xl p-6 space-y-3">
            <p className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles size={16} className="text-primary" />
              Why we ask this
            </p>
            <ul className="text-sm text-gray-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">✓</span>
                <span>We'll suggest the best planning templates for YOUR specific business</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">✓</span>
                <span>AI will use industry-specific language you understand (no jargon!)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">✓</span>
                <span>Recommendations will match your actual challenges and team size</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
