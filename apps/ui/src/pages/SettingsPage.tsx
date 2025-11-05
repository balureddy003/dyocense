import { useState, useEffect } from "react";
import { Key, Copy, RefreshCw, Check, CreditCard, ArrowUpCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

interface TenantProfile {
  tenant_id: string;
  name: string;
  owner_email: string;
  plan_tier: string;
  created_at: string;
  trial_ends_at?: string;
}

export function SettingsPage() {
  const { profile, user } = useAuth();
  const navigate = useNavigate();
  const [tenantProfile, setTenantProfile] = useState<TenantProfile | null>(null);
  const [apiToken, setApiToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [rotating, setRotating] = useState(false);

  useEffect(() => {
    loadTenantProfile();
  }, []);

  const loadTenantProfile = async () => {
    try {
      const response = await fetch("http://localhost:8001/v1/tenants/me", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("dyocense-api-token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setTenantProfile(data);
      }
    } catch (err) {
      console.warn("Failed to load tenant profile", err);
    }
  };

  const loadApiToken = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8001/v1/tenants/me/api-token", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("dyocense-api-token")}`,
        },
      });
      if (!response.ok) {
        throw new Error("Failed to load API token");
      }
      const data = await response.json();
      setApiToken(data.api_token);
    } catch (err: any) {
      setError(err.message || "Failed to load API token");
    } finally {
      setLoading(false);
    }
  };

  const rotateApiToken = async () => {
    if (!confirm("Are you sure you want to rotate your API token? This will invalidate the current token immediately.")) {
      return;
    }

    setRotating(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8001/v1/tenants/me/api-token/rotate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("dyocense-api-token")}`,
        },
      });
      if (!response.ok) {
        throw new Error("Failed to rotate API token");
      }
      const data = await response.json();
      setApiToken(data.api_token);
    } catch (err: any) {
      setError(err.message || "Failed to rotate API token");
    } finally {
      setRotating(false);
    }
  };

  const copyToClipboard = () => {
    if (apiToken) {
      navigator.clipboard.writeText(apiToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getPlanDisplayName = (tier: string) => {
    const names: Record<string, string> = {
      free: "Free",
      silver: "Silver",
      gold: "Gold",
      platinum: "Platinum",
    };
    return names[tier] || tier;
  };

  const isTrialActive = () => {
    if (!tenantProfile?.trial_ends_at) return false;
    return new Date(tenantProfile.trial_ends_at) > new Date();
  };

  const getTrialDaysLeft = () => {
    if (!tenantProfile?.trial_ends_at) return 0;
    const now = new Date();
    const trialEnd = new Date(tenantProfile.trial_ends_at);
    const diff = trialEnd.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-600 mt-2">Manage your account and API access</p>
        </div>

        {/* Profile Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile</h2>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-600">Business Name</label>
              <p className="text-base text-gray-900">{profile?.companyName || tenantProfile?.name || "Not set"}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Tenant ID</label>
              <p className="text-base text-gray-900 font-mono">{tenantProfile?.tenant_id || "N/A"}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Email</label>
              <p className="text-base text-gray-900">{user?.email || tenantProfile?.owner_email || "N/A"}</p>
            </div>
          </div>
        </div>

        {/* Subscription Section */}
        {tenantProfile && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <CreditCard size={20} />
                  Subscription
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Manage your plan and billing
                </p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Plan</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {getPlanDisplayName(tenantProfile.plan_tier)}
                  </p>
                  {isTrialActive() && tenantProfile.plan_tier === "silver" && (
                    <p className="text-sm text-blue-600 mt-1">
                      🎉 Trial active • {getTrialDaysLeft()} days remaining
                    </p>
                  )}
                  {!isTrialActive() && tenantProfile.plan_tier === "free" && (
                    <p className="text-sm text-gray-600 mt-1">
                      Upgrade to unlock more features
                    </p>
                  )}
                </div>
                {(tenantProfile.plan_tier === "free" || (tenantProfile.plan_tier === "silver" && isTrialActive())) && (
                  <button
                    onClick={() => navigate("/buy")}
                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition flex items-center gap-2 font-semibold"
                  >
                    <ArrowUpCircle size={18} />
                    Upgrade Plan
                  </button>
                )}
              </div>

              {isTrialActive() && tenantProfile.plan_tier === "silver" && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>Trial ending soon!</strong> Your trial ends in {getTrialDaysLeft()} days.
                    Upgrade now to continue with full access, or you'll be moved to the Free plan.
                  </p>
                  <button
                    onClick={() => navigate("/buy")}
                    className="mt-3 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition text-sm font-semibold"
                  >
                    Upgrade to Silver - $149/month
                  </button>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Member Since</p>
                  <p className="text-sm font-medium text-gray-900">
                    {new Date(tenantProfile.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Status</p>
                  <p className="text-sm font-medium text-green-600">Active</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* API Token Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Key size={20} />
                API Token
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Use this token for programmatic access to the Dyocense API
              </p>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {!apiToken ? (
            <button
              onClick={loadApiToken}
              disabled={loading}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition disabled:opacity-50 flex items-center gap-2"
            >
              <Key size={16} />
              {loading ? "Loading..." : "Show API Token"}
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-600 mb-2 block">Your API Token</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={apiToken}
                    readOnly
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                  />
                  <button
                    onClick={copyToClipboard}
                    className="px-3 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition flex items-center gap-2"
                    title="Copy to clipboard"
                  >
                    {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
                  </button>
                  <button
                    onClick={rotateApiToken}
                    disabled={rotating}
                    className="px-3 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition disabled:opacity-50 flex items-center gap-2"
                    title="Rotate token"
                  >
                    <RefreshCw size={16} className={rotating ? "animate-spin" : ""} />
                    Rotate
                  </button>
                </div>
              </div>

              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>⚠️ Keep this secure:</strong> Anyone with this token can access your Dyocense account via API.
                  Do not share it publicly or commit it to version control.
                </p>
              </div>

              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                  How to use this token
                </summary>
                <div className="mt-3 p-4 bg-gray-50 rounded-lg space-y-2">
                  <p className="text-gray-700">Include it in your API requests as a Bearer token:</p>
                  <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto">
{`curl -H "Authorization: Bearer ${apiToken}" \\
  http://localhost:8001/v1/tenants/me`}
                  </pre>
                  <p className="text-gray-600 text-xs mt-2">
                    Or use it during login flow (for API token authentication without credentials).
                  </p>
                </div>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
