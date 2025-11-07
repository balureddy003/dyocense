import { useEffect, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../lib/config";

export const OAuthCallbackPage = () => {
  const { provider } = useParams<{ provider: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const errorParam = searchParams.get("error");

        if (errorParam) {
          throw new Error(`OAuth error: ${errorParam}`);
        }

        if (!code || !state) {
          throw new Error("Missing OAuth parameters");
        }

        // Verify state matches
        const storedState = sessionStorage.getItem(`oauth_state_${provider}`);
        if (storedState && storedState !== state) {
          throw new Error("Invalid state parameter - possible CSRF attack");
        }

        // Call backend OAuth callback
        const response = await fetch(
          `${API_BASE_URL}/api/accounts/v1/auth/${provider}/callback`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ code, state }),
          }
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "OAuth authentication failed");
        }

        const data = await response.json();

        // Clear stored state
        sessionStorage.removeItem(`oauth_state_${provider}`);

        // Login with received token
        await loginWithToken({
          apiToken: data.token,
          tenantId: data.tenant_id,
          remember: true,
        });

        // Redirect to home or intended destination
        const redirect = sessionStorage.getItem("oauth_redirect") || "/home";
        sessionStorage.removeItem("oauth_redirect");
        navigate(redirect, { replace: true });
      } catch (err: any) {
        console.error("OAuth callback error:", err);
        setError(err.message || "Authentication failed");
        setProcessing(false);
      }
    };

    handleCallback();
  }, [provider, searchParams, navigate, loginWithToken]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Authentication Failed</h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate("/login")}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="inline-block relative">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 bg-primary rounded-full opacity-20"></div>
          </div>
        </div>
        <h2 className="mt-6 text-xl font-semibold text-gray-900">Completing sign in...</h2>
        <p className="mt-2 text-sm text-gray-600">
          {provider && `Authenticating with ${provider.charAt(0).toUpperCase() + provider.slice(1)}`}
        </p>
      </div>
    </div>
  );
};
