/**
 * OnboardingPage - Multi-step setup flow with browser navigation support
 * Handles: Industry Selection → Business Preferences → Getting Started
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { IndustrySelector, Industry } from "../components/IndustrySelector";
import { BusinessPreferences } from "../components/BusinessPreferences";
import { GettingStartedGuide } from "../components/GettingStartedGuide";
import { useAuth } from "../context/AuthContext";
import { ArrowLeft, Check } from "lucide-react";
import { tenantConnectorStore } from "../lib/tenantConnectors";

type OnboardingStep = "industry" | "preferences" | "getting-started";

export function OnboardingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Get step from URL or default to first step
  const currentStep = (searchParams.get("step") as OnboardingStep) || "industry";
  
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | undefined>(() => {
    if (!user?.id) return undefined;
    const stored = localStorage.getItem(`dyocense-industry-${user.id}`);
    return stored ? (stored as Industry) : undefined;
  });

  const [preferencesComplete, setPreferencesComplete] = useState(() => {
    if (!user?.id) return false;
    return localStorage.getItem(`dyocense-preferences-${user.id}`) === "complete";
  });

  const [hasConnectors, setHasConnectors] = useState(false);
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Load tenant ID from auth
  useEffect(() => {
    if (user?.id) {
      // Get tenant_id from user profile or default
      const tid = user.tenantId || user.id;
      setTenantId(tid);
    }
  }, [user]);

  // Check connectors
  useEffect(() => {
    if (tenantId) {
      (async () => {
        try {
          const connectors = await tenantConnectorStore.getAll(tenantId);
          setHasConnectors(connectors.filter((c) => c.status === "active").length > 0);
        } catch (err) {
          console.warn("Failed to load connectors", err);
        }
      })();
    }
  }, [tenantId]);

  // Redirect if onboarding already complete
  useEffect(() => {
    if (selectedIndustry && preferencesComplete && currentStep === "industry") {
      setSearchParams({ step: "getting-started" });
    }
  }, [selectedIndustry, preferencesComplete, currentStep]);

  const handleIndustrySelect = (industry: Industry) => {
    if (!user?.id) return;
    
    setSelectedIndustry(industry);
    localStorage.setItem(`dyocense-industry-${user.id}`, industry);
    
    // Move to preferences step
    setSearchParams({ step: "preferences" });
  };

  const handlePreferencesComplete = (data: any) => {
    if (!user?.id) return;
    
    localStorage.setItem(`dyocense-preferences-${user.id}`, "complete");
    localStorage.setItem(`dyocense-preferences-data-${user.id}`, JSON.stringify(data));
    setPreferencesComplete(true);
    
    // Move to getting started
    setSearchParams({ step: "getting-started" });
  };

  const handleSkipPreferences = () => {
    if (!user?.id) return;
    
    localStorage.setItem(`dyocense-preferences-${user.id}`, "complete");
    setPreferencesComplete(true);
    setSearchParams({ step: "getting-started" });
  };

  const finalizeOnboarding = () => {
    if (user?.id) {
      localStorage.setItem(`dyocense-onboarding-${user.id}`, "complete");
    }
  };

  const handleStartChat = () => {
    finalizeOnboarding();
    navigate("/home?mode=agent");
  };

  const handleConnectData = () => {
    finalizeOnboarding();
    navigate("/home?mode=connectors");
  };

  const handleBack = () => {
    if (currentStep === "preferences") {
      setSearchParams({ step: "industry" });
    } else if (currentStep === "getting-started") {
      setSearchParams({ step: "preferences" });
    }
  };

  const canGoBack = currentStep !== "industry";

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Progress Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              {canGoBack && (
                <button
                  onClick={handleBack}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <ArrowLeft size={20} />
                  <span className="text-sm font-medium">Back</span>
                </button>
              )}
              <h2 className="text-xl font-bold text-gray-900">
                {currentStep === "industry" && "What's your business?"}
                {currentStep === "preferences" && "Tell us more"}
                {currentStep === "getting-started" && "You're ready!"}
              </h2>
            </div>
            <button
              onClick={() => {
                  finalizeOnboarding();
                  navigate("/home");
                }}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              I'll do this later
            </button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-4">
            {/* Step 1: Industry */}
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                currentStep === "industry"
                  ? "bg-blue-600 text-white"
                  : selectedIndustry
                  ? "bg-green-500 text-white"
                  : "bg-gray-200 text-gray-600"
              }`}>
                {selectedIndustry ? <Check size={16} /> : "1"}
              </div>
              <span className={`text-sm font-medium ${
                currentStep === "industry" ? "text-gray-900" : "text-gray-600"
              }`}>
                Business Type
              </span>
            </div>

            <div className="flex-1 h-0.5 bg-gray-300">
              <div 
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ 
                  width: currentStep === "industry" 
                    ? "0%" 
                    : currentStep === "preferences" 
                    ? "50%" 
                    : "100%" 
                }}
              />
            </div>

            {/* Step 2: Preferences */}
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                currentStep === "preferences"
                  ? "bg-blue-600 text-white"
                  : preferencesComplete
                  ? "bg-green-500 text-white"
                  : "bg-gray-200 text-gray-600"
              }`}>
                {preferencesComplete ? <Check size={16} /> : "2"}
              </div>
              <span className={`text-sm font-medium ${
                currentStep === "preferences" ? "text-gray-900" : "text-gray-600"
              }`}>
                Preferences
              </span>
            </div>

            <div className="flex-1 h-0.5 bg-gray-300">
              <div 
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ 
                  width: currentStep === "getting-started" ? "100%" : "0%" 
                }}
              />
            </div>

            {/* Step 3: Getting Started */}
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                currentStep === "getting-started"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-600"
              }`}>
                3
              </div>
              <span className={`text-sm font-medium ${
                currentStep === "getting-started" ? "text-gray-900" : "text-gray-600"
              }`}>
                Get Started
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {currentStep === "industry" && (
          <div className="bg-white rounded-2xl border-2 border-blue-200 p-8 shadow-lg max-w-4xl mx-auto">
            <IndustrySelector
              selected={selectedIndustry}
              onSelect={handleIndustrySelect}
            />
          </div>
        )}

        {currentStep === "preferences" && (
          <div className="bg-white rounded-2xl border-2 border-blue-200 p-8 shadow-lg max-w-4xl mx-auto">
            <BusinessPreferences
              industry={selectedIndustry}
              onComplete={handlePreferencesComplete}
              onSkip={handleSkipPreferences}
            />
          </div>
        )}

        {currentStep === "getting-started" && (
          <GettingStartedGuide
            onConnectData={handleConnectData}
            onStartChat={handleStartChat}
            hasConnectors={hasConnectors}
            selectedIndustry={selectedIndustry}
          />
        )}
      </div>
    </div>
  );
}
