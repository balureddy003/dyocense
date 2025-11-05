import { AlertCircle, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface TrialBannerProps {
  status: string;
  planTier: string;
  trialEndsAt?: string | null;
}

export const TrialBanner = ({ status, planTier, trialEndsAt }: TrialBannerProps) => {
  const navigate = useNavigate();
  
  // Only show banner for silver trial plans
  if (planTier !== "silver" || status !== "trial" || !trialEndsAt) {
    return null;
  }

  const now = new Date();
  const endsAt = new Date(trialEndsAt);
  const daysRemaining = Math.ceil((endsAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  // Don't show if trial hasn't started or is far in the future
  if (daysRemaining > 7 || daysRemaining < 0) {
    return null;
  }

  const isUrgent = daysRemaining <= 2;
  const isExpired = daysRemaining < 0;

  return (
    <div
      className={`rounded-xl border px-5 py-4 flex items-start gap-4 ${
        isExpired
          ? "bg-red-50 border-red-200"
          : isUrgent
          ? "bg-orange-50 border-orange-200"
          : "bg-blue-50 border-blue-200"
      }`}
    >
      <div className="flex-shrink-0 mt-0.5">
        {isExpired ? (
          <AlertCircle size={20} className="text-red-600" />
        ) : isUrgent ? (
          <AlertCircle size={20} className="text-orange-600" />
        ) : (
          <Sparkles size={20} className="text-blue-600" />
        )}
      </div>
      <div className="flex-1 space-y-2">
        <div>
          <h3
            className={`text-sm font-semibold ${
              isExpired
                ? "text-red-900"
                : isUrgent
                ? "text-orange-900"
                : "text-blue-900"
            }`}
          >
            {isExpired
              ? "Your trial has ended"
              : daysRemaining === 0
              ? "Your trial ends today"
              : daysRemaining === 1
              ? "Your trial ends tomorrow"
              : `Your trial ends in ${daysRemaining} days`}
          </h3>
          <p
            className={`text-xs mt-1 ${
              isExpired
                ? "text-red-700"
                : isUrgent
                ? "text-orange-700"
                : "text-blue-700"
            }`}
          >
            {isExpired
              ? "You've been moved to the Free plan. Upgrade to restore full access to your projects and playbooks."
              : `Trial expires on ${endsAt.toLocaleDateString()}. Upgrade now to continue with full Silver plan features ($149/month) or switch to the Free plan.`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/settings")}
            className={`text-xs font-semibold px-4 py-2 rounded-lg transition ${
              isExpired || isUrgent
                ? "bg-primary text-white hover:bg-blue-700 shadow-sm"
                : "bg-white text-primary border border-blue-300 hover:bg-blue-50"
            }`}
          >
            {isExpired ? "Upgrade Now" : "View Upgrade Options"}
          </button>
          {!isExpired && (
            <button
              onClick={() => navigate("/settings")}
              className="text-xs font-medium text-gray-600 hover:text-gray-900 underline"
            >
              Learn about the Free plan
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
