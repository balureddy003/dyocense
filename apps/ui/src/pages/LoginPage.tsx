import { LogIn, ShieldCheck, User } from "lucide-react";
import { useEffect, useState } from "react";
import { NavigateFunction, useLocation, useNavigate } from "react-router-dom";
import { BrandedFooter } from "../components/BrandedFooter";
import { BrandedHeader } from "../components/BrandedHeader";
import { SocialLoginButtons } from "../components/SocialLoginButtons";
import { useAuth } from "../context/AuthContext";
import { getUserTenants, TenantOption } from "../lib/api";

const resolveRedirect = (navigate: NavigateFunction, target: string) => {
  if (!target.startsWith("http")) {
    navigate(target, { replace: true });
    return;
  }
  window.location.href = target;
};

export const LoginPage = () => {
  const {
    ready,
    authenticated,
    login,
    loginWithCredentials,
    registerUserAccount,
    profile,
    supportsKeycloak,
    logout,
  } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const redirectTarget = params.get("redirect") || "/home";
  const [credentialTenant, setCredentialTenant] = useState("");
  const [credentialEmail, setCredentialEmail] = useState("");
  const [credentialPassword, setCredentialPassword] = useState("");
  const [credentialError, setCredentialError] = useState<string | null>(null);
  const [credentialSubmitting, setCredentialSubmitting] = useState(false);
  const [registerMode, setRegisterMode] = useState(false);
  const [registerAccessToken, setRegisterAccessToken] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [tenantFromUrl, setTenantFromUrl] = useState(false); // Track if tenant came from URL
  const [availableTenants, setAvailableTenants] = useState<TenantOption[]>([]);
  const [fetchingTenants, setFetchingTenants] = useState(false);
  const [showTenantSelector, setShowTenantSelector] = useState(false);

  useEffect(() => {
    if (!ready) return;

    // If authenticated, redirect to target page (profile is optional)
    if (authenticated) {
      resolveRedirect(navigate, redirectTarget);
    }
  }, [authenticated, ready, navigate, redirectTarget]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // First check URL params (takes precedence)
    const urlTenant = params.get("tenant");
    const urlEmail = params.get("email");
    const shouldRegister = params.get("register") === "true";

    if (urlTenant) {
      setCredentialTenant(urlTenant);
      setTenantFromUrl(true); // Mark that tenant came from URL
    }
    if (urlEmail) setCredentialEmail(urlEmail);
    if (shouldRegister) setRegisterMode(true); // Auto-switch to register mode from welcome email

    // Then check localStorage for remembered values (only if not in URL)
    const storedTenant = window.localStorage.getItem("dyocense-tenant-id");
    const storedEmail = window.localStorage.getItem("dyocense-user-email");

    if (!urlTenant && storedTenant) setCredentialTenant(storedTenant);
    if (!urlEmail && storedEmail) setCredentialEmail(storedEmail);
  }, [params]);

  // Fetch available tenants when email changes (only in login mode and if tenant not from URL)
  const handleEmailBlur = async () => {
    if (registerMode || tenantFromUrl || !credentialEmail.trim() || !credentialEmail.includes("@")) {
      return;
    }

    setFetchingTenants(true);
    setCredentialError(null);

    try {
      const tenants = await getUserTenants(credentialEmail.trim());
      setAvailableTenants(tenants);

      if (tenants.length === 0) {
        setCredentialError("No account found with this email address.");
        setShowTenantSelector(false);
        setCredentialTenant("");
      } else if (tenants.length === 1) {
        // Auto-select the only tenant
        setCredentialTenant(tenants[0].tenant_id);
        setShowTenantSelector(false);
      } else {
        // Multiple tenants - show selector
        setShowTenantSelector(true);
        if (!credentialTenant || !tenants.find(t => t.tenant_id === credentialTenant)) {
          setCredentialTenant(""); // Reset if current selection not in list
        }
      }
    } catch (error) {
      console.error("Failed to fetch tenants:", error);
      // Don't show error to user - they can still manually enter tenant ID
      setShowTenantSelector(false);
    } finally {
      setFetchingTenants(false);
    }
  };

  const handleCredentialLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCredentialError(null);
    if (!credentialTenant.trim()) {
      setCredentialError("Tenant ID is required.");
      return;
    }
    if (!credentialEmail.trim() || !credentialPassword.trim()) {
      setCredentialError("Email and password are required.");
      return;
    }
    setCredentialSubmitting(true);
    try {
      await loginWithCredentials(credentialTenant.trim(), credentialEmail.trim(), credentialPassword);
    } catch (err: any) {
      setCredentialError(err?.message || "Unable to sign in with credentials.");
    } finally {
      setCredentialSubmitting(false);
    }
  };

  const handleRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCredentialError(null);
    if (!credentialTenant.trim()) {
      setCredentialError("Tenant ID is required.");
      return;
    }
    if (!credentialEmail.trim() || !registerPassword.trim() || !registerName.trim()) {
      setCredentialError("Name, email, and password are required to register.");
      return;
    }
    setCredentialSubmitting(true);
    try {
      await registerUserAccount(
        credentialTenant.trim(),
        credentialEmail.trim(),
        registerName.trim(),
        registerPassword,
        registerAccessToken.trim()
      );

      // Account created successfully - now automatically log in
      setCredentialError("Account created! Signing you in...");

      // Longer delay to ensure database write is committed (MongoDB may need time)
      await new Promise(resolve => setTimeout(resolve, 1500));

      try {
        await loginWithCredentials(credentialTenant.trim(), credentialEmail.trim(), registerPassword);
        // Login successful - user will be redirected by the useEffect above
        // Keep the form in submitting state while redirect happens
        return;
      } catch (loginErr: any) {
        console.error("Auto-login failed:", loginErr);
        // If auto-login fails, switch to login mode so they can try manually
        setRegisterMode(false);
        setCredentialPassword(registerPassword);
        setCredentialError("Account created successfully! Please click 'Sign in' below.");
        setRegisterPassword("");
        setRegisterAccessToken("");
        setRegisterName("");
      }
    } catch (err: any) {
      setCredentialError(err?.message || "Unable to register account.");
    } finally {
      setCredentialSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <BrandedHeader showNav={false} />

      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full bg-white border border-gray-100 rounded-2xl shadow-xl p-8 space-y-6">
          {/* Show profile setup prompt if authenticated but no profile */}
          {authenticated && !profile ? (
            <div className="text-center space-y-4">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mx-auto">
                <User size={32} className="text-primary" />
              </div>
              <h1 className="text-2xl font-semibold text-gray-900">
                Complete Your Profile
              </h1>
              <p className="text-gray-600">
                You're logged in! Let's set up your business profile to get started.
              </p>
              <button
                onClick={() => navigate("/profile")}
                className="w-full px-6 py-3 rounded-lg bg-primary text-white font-semibold shadow-md hover:shadow-lg transition"
              >
                Continue to Profile Setup
              </button>
              <button
                onClick={() => {
                  logout();
                  window.location.reload();
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign in with different account
              </button>
            </div>
          ) : (
            <>
              <header className="space-y-2 text-center">
                <h1 className="text-2xl font-semibold text-gray-900">
                  {registerMode ? "Get Started with Dyocense" : "Welcome Back"}
                </h1>
                <p className="text-sm text-gray-600">
                  {registerMode
                    ? "Join businesses making smarter inventory and planning decisions"
                    : "Sign in to your business dashboard"}
                </p>
              </header>

              <div className="space-y-8">
                <section className="space-y-3">
                  {params.get("tenant") && registerMode && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                      👋 Welcome! Complete the form below to create your account.
                    </div>
                  )}
                  {params.get("tenant") && !registerMode && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                      👋 Welcome! Sign in with your credentials below.
                    </div>
                  )}
                  <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">
                    {registerMode ? "Create your account" : "Sign in to your account"}
                  </p>

                  {/* Social Login Options for SMBs */}
                  {!registerMode && (
                    <>
                      <SocialLoginButtons
                        tenantId={credentialTenant || undefined}
                        onError={(error) => setCredentialError(error)}
                      />

                      <div className="relative flex items-center gap-3 py-2">
                        <div className="flex-1 border-t border-gray-200"></div>
                        <span className="text-xs text-gray-400 uppercase tracking-wide">or continue with email</span>
                        <div className="flex-1 border-t border-gray-200"></div>
                      </div>
                    </>
                  )}

                  <form className="space-y-3" onSubmit={registerMode ? handleRegister : handleCredentialLogin}>
                    {!registerMode && showTenantSelector && availableTenants.length > 1 && (
                      <label className="flex flex-col gap-2 text-sm text-gray-700">
                        Which company?
                        <select
                          className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                          value={credentialTenant}
                          onChange={(event) => setCredentialTenant(event.target.value)}
                          required
                        >
                          <option value="">-- Choose your company --</option>
                          {availableTenants.map(tenant => (
                            <option key={tenant.tenant_id} value={tenant.tenant_id}>
                              {tenant.name}
                            </option>
                          ))}
                        </select>
                        <span className="text-xs text-gray-500">You have access to multiple companies</span>
                      </label>
                    )}
                    {(registerMode && !tenantFromUrl) && (
                      <label className="flex flex-col gap-2 text-sm text-gray-700">
                        Company ID
                        <input
                          className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                          placeholder="e.g. acme-supplies"
                          value={credentialTenant}
                          onChange={(event) => setCredentialTenant(event.target.value)}
                          required
                        />
                        <span className="text-xs text-gray-500">This was provided in your invitation email</span>
                      </label>
                    )}
                    <label className="flex flex-col gap-2 text-sm text-gray-700">
                      Your work email
                      <input
                        type="email"
                        className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                        placeholder="you@yourcompany.com"
                        value={credentialEmail}
                        onChange={(event) => setCredentialEmail(event.target.value)}
                        onBlur={handleEmailBlur}
                        required
                      />
                      {fetchingTenants && (
                        <span className="text-xs text-gray-500">Checking your account...</span>
                      )}
                    </label>
                    {registerMode && (
                      <label className="flex flex-col gap-2 text-sm text-gray-700">
                        Full name
                        <input
                          className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                          placeholder="Your name"
                          value={registerName}
                          onChange={(event) => setRegisterName(event.target.value)}
                          required
                        />
                      </label>
                    )}
                    <label className="flex flex-col gap-2 text-sm text-gray-700">
                      {registerMode ? "Create password" : "Password"}
                      <input
                        type="password"
                        className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                        placeholder="••••••••"
                        value={registerMode ? registerPassword : credentialPassword}
                        onChange={(event) =>
                          registerMode ? setRegisterPassword(event.target.value) : setCredentialPassword(event.target.value)
                        }
                        required
                      />
                    </label>
                    {credentialError && (
                      <p
                        className={`text-sm ${credentialError.toLowerCase().includes("signing you in") ? "text-blue-600" :
                            credentialError.toLowerCase().includes("successfully") ? "text-emerald-600" : "text-red-500"
                          }`}
                      >
                        {credentialError}
                      </p>
                    )}
                    <div className="flex flex-col gap-2">
                      <button
                        type="submit"
                        className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                        disabled={credentialSubmitting}
                      >
                        <LogIn size={18} />
                        {credentialSubmitting ? (registerMode ? "Creating account…" : "Signing in…") : (registerMode ? "Create account" : "Sign in")}
                      </button>
                      <button
                        type="button"
                        className="text-xs text-primary font-semibold"
                        onClick={() => {
                          setCredentialError(null);
                          setRegisterMode((prev) => !prev);
                        }}
                      >
                        {registerMode ? "Have an account? Sign in" : "Need an account? Register"}
                      </button>
                    </div>
                  </form>
                </section>

                <div className="space-y-5">
                  {supportsKeycloak ? (
                    <div className="space-y-3 text-sm text-gray-700">
                      <p className="flex items-center gap-2">
                        <ShieldCheck size={16} className="text-primary" />
                        Secure single sign-on (SSO) with your company account
                      </p>
                      <p className="flex items-center gap-2">
                        <ShieldCheck size={16} className="text-primary" />
                        Automatic login with your existing credentials
                      </p>
                      <p className="flex items-center gap-2">
                        <ShieldCheck size={16} className="text-primary" />
                        Safe and encrypted access to your business data
                      </p>
                      <button
                        className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                        onClick={() => void login(`${window.location.origin}${redirectTarget}`)}
                        disabled={!ready}
                      >
                        <LogIn size={18} />
                        Sign in with SSO
                      </button>
                      <p className="text-xs text-gray-400 text-center">
                        Need access?{" "}
                        <button className="text-primary font-semibold" onClick={() => navigate("/buy")}>
                          Contact us
                        </button>
                      </p>
                    </div>
                  ) : null}

                  {/* Demo/sample data login removed to ensure only real authentication flows are used. */}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <BrandedFooter />
    </div>
  );
};
