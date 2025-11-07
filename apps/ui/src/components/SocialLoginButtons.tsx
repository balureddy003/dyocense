import { useState, useEffect } from "react";
import { API_BASE_URL } from "../lib/config";

interface SocialProvider {
  name: string;
  description: string;
  icon: string;
  color: string;
}

interface SocialLoginButtonsProps {
  tenantId?: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const SocialLoginButtons = ({ tenantId, onSuccess, onError }: SocialLoginButtonsProps) => {
  const [providers, setProviders] = useState<Record<string, SocialProvider>>({});
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState<string | null>(null);

  useEffect(() => {
    // Fetch enabled OAuth providers
    fetch(`${API_BASE_URL}/api/accounts/v1/auth/providers`)
      .then((res) => res.json())
      .then((data) => {
        setProviders(data.providers || {});
        setLoading(false);
      })
      .catch((error) => {
        console.error("Failed to load OAuth providers:", error);
        setLoading(false);
      });
  }, []);

  const handleSocialLogin = async (provider: string) => {
    setAuthLoading(provider);
    
    try {
      // Get authorization URL
      const url = new URL(`${API_BASE_URL}/api/accounts/v1/auth/${provider}/authorize`);
      if (tenantId) {
        url.searchParams.set("tenant_id", tenantId);
      }

      const response = await fetch(url.toString());
      const data = await response.json();

      if (data.authorization_url) {
        // Store state for verification after callback
        if (data.state) {
          sessionStorage.setItem(`oauth_state_${provider}`, data.state);
        }
        
        // Redirect to OAuth provider
        window.location.href = data.authorization_url;
      } else {
        throw new Error("No authorization URL returned");
      }
    } catch (error) {
      console.error(`${provider} login failed:`, error);
      setAuthLoading(null);
      onError?.(`Failed to initiate ${provider} login`);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-11 bg-gray-100 rounded-lg animate-pulse"></div>
        <div className="h-11 bg-gray-100 rounded-lg animate-pulse"></div>
        <div className="h-11 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  const enabledProviders = Object.keys(providers);

  if (enabledProviders.length === 0) {
    return null;
  }

  const getProviderIcon = (provider: string) => {
    const icons: Record<string, JSX.Element> = {
      google: (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <path
            fill="currentColor"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="currentColor"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="currentColor"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="currentColor"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
      ),
      microsoft: (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#F25022" d="M1 1h10v10H1z" />
          <path fill="#00A4EF" d="M13 1h10v10H13z" />
          <path fill="#7FBA00" d="M1 13h10v10H1z" />
          <path fill="#FFB900" d="M13 13h10v10H13z" />
        </svg>
      ),
      apple: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
        </svg>
      ),
    };
    return icons[provider] || null;
  };

  return (
    <div className="space-y-3">
      {enabledProviders.map((provider) => {
        const info = providers[provider];
        const isLoading = authLoading === provider;

        return (
          <button
            key={provider}
            onClick={() => handleSocialLogin(provider)}
            disabled={isLoading || authLoading !== null}
            className={`
              w-full flex items-center justify-center gap-3 px-4 py-2.5 
              border border-gray-300 rounded-lg font-medium text-sm
              transition-all duration-200
              ${
                isLoading
                  ? "bg-gray-100 cursor-wait"
                  : "bg-white hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100"
              }
              ${authLoading && authLoading !== provider ? "opacity-50 cursor-not-allowed" : ""}
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary
            `}
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
            ) : (
              getProviderIcon(provider)
            )}
            <span className="text-gray-700">
              {isLoading ? `Connecting to ${info.name}...` : `Continue with ${info.name}`}
            </span>
          </button>
        );
      })}
    </div>
  );
};
