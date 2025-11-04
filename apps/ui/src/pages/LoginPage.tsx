import { useEffect, useState } from "react";
import { useLocation, useNavigate, NavigateFunction } from "react-router-dom";
import { LogIn, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

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
    loginDemo,
    loginWithToken,
    loginWithCredentials,
    registerUserAccount,
    profile,
    supportsKeycloak,
  } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const redirectTarget = params.get("redirect") || "/home";
  const [businessName, setBusinessName] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [apiToken, setApiToken] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [remember, setRemember] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [credentialTenant, setCredentialTenant] = useState("");
  const [credentialEmail, setCredentialEmail] = useState("");
  const [credentialPassword, setCredentialPassword] = useState("");
  const [credentialError, setCredentialError] = useState<string | null>(null);
  const [credentialSubmitting, setCredentialSubmitting] = useState(false);
  const [registerMode, setRegisterMode] = useState(false);
  const [registerAccessToken, setRegisterAccessToken] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");

  useEffect(() => {
    if (!ready) return;
    if (authenticated) {
      const next = profile ? redirectTarget : "/profile";
      resolveRedirect(navigate, next);
    }
  }, [authenticated, profile, ready, navigate, redirectTarget]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedTenant = window.localStorage.getItem("dyocense-tenant-id");
    const storedName = window.localStorage.getItem("dyocense-user-name");
    const storedEmail = window.localStorage.getItem("dyocense-user-email");
    const storedToken = window.localStorage.getItem("dyocense-api-token");
    if (storedTenant) setTenantId(storedTenant);
    if (storedName) setBusinessName(storedName);
    if (storedEmail) setContactEmail(storedEmail);
    if (storedTenant) setCredentialTenant(storedTenant);
    if (storedEmail) setCredentialEmail(storedEmail);
    if (storedToken) setApiToken(storedToken);
  }, []);

  const handleTokenLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTokenError(null);
    if (!apiToken.trim()) {
      setTokenError("API token is required.");
      return;
    }
    setSubmitting(true);
    try {
      await loginWithToken({
        apiToken,
        tenantId,
        displayName: businessName,
        email: contactEmail,
        remember,
      });
    } catch (err: any) {
      setTokenError(err?.message || "Unable to sign in with API token.");
    } finally {
      setSubmitting(false);
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
    if (!credentialTenant.trim() || !registerAccessToken.trim()) {
      setCredentialError("Tenant ID and access token are required.");
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
      setRegisterMode(false);
      setCredentialError("Account created! You can sign in now.");
      setCredentialPassword(registerPassword);
      setRegisterPassword("");
      setRegisterAccessToken("");
      setRegisterName("");
    } catch (err: any) {
      setCredentialError(err?.message || "Unable to register account.");
    } finally {
      setCredentialSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100 px-4">
      <div className="max-w-md w-full bg-white border border-gray-100 rounded-2xl shadow-xl p-8 space-y-6">
        <header className="space-y-2 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white font-semibold text-lg">
            D
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Welcome back to Dyocense</h1>
          {supportsKeycloak ? (
            <p className="text-sm text-gray-600">
              Use your Dyocense tenant API token to sign in instantly, or connect with enterprise SSO if your
              organization has enabled Keycloak.
            </p>
          ) : (
            <p className="text-sm text-gray-600">
              Small teams can access Dyocense with the tenant ID and API token we shared during onboarding. No SSO
              setup required.
            </p>
          )}
        </header>
        <div className="space-y-8">
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">User account login</p>
            <form className="space-y-3" onSubmit={registerMode ? handleRegister : handleCredentialLogin}>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Tenant ID
                <input
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="tenant-123"
                  value={credentialTenant}
                  onChange={(event) => setCredentialTenant(event.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Email
                <input
                  type="email"
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="ops@yourcompany.com"
                  value={credentialEmail}
                  onChange={(event) => setCredentialEmail(event.target.value)}
                  required
                />
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
              {registerMode && (
                <label className="flex flex-col gap-2 text-sm text-gray-700">
                  Access token (from subscription email)
                  <input
                    className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                    placeholder="key-xxxx"
                    value={registerAccessToken}
                    onChange={(event) => setRegisterAccessToken(event.target.value)}
                    required
                  />
                </label>
              )}
              {credentialError && (
                <p
                  className={`text-sm ${
                    credentialError.toLowerCase().includes("created") ? "text-emerald-600" : "text-red-500"
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
                  {registerMode ? "Have an account? Sign in" : "Need an account? Register with your access token"}
                </button>
              </div>
            </form>
          </section>

          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Small business API token</p>
            <form className="space-y-3" onSubmit={handleTokenLogin}>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Business name
                <input
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="e.g. Riverfront Supply Co."
                  value={businessName}
                  onChange={(event) => setBusinessName(event.target.value)}
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Tenant ID (optional)
                <input
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="tenant-123"
                  value={tenantId}
                  onChange={(event) => setTenantId(event.target.value)}
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                API token
                <input
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="key-xxxx"
                  value={apiToken}
                  onChange={(event) => setApiToken(event.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Contact email (optional)
                <input
                  type="email"
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="ops@yourcompany.com"
                  value={contactEmail}
                  onChange={(event) => setContactEmail(event.target.value)}
                />
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-500">
                <input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
                Remember this device
              </label>
              {tokenError && <p className="text-sm text-red-500">{tokenError}</p>}
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                disabled={submitting}
              >
                <LogIn size={18} />
                {submitting ? "Signing in…" : "Sign in with API token"}
              </button>
            </form>
          </section>

          <div className="space-y-5">
            {supportsKeycloak ? (
              <div className="space-y-3 text-sm text-gray-700">
                <p className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-primary" />
                  Single sign-on with Keycloak (OAuth 2.0 / OpenID Connect)
                </p>
                <p className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-primary" />
                  PKCE-enabled flow with auto token refresh
                </p>
                <p className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-primary" />
                  Secure access to Dyocense APIs and copilots
                </p>
                <button
                  className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                  onClick={() => void login(`${window.location.origin}${redirectTarget}`)}
                  disabled={!ready}
                >
                  <LogIn size={18} />
                  Sign in with Keycloak
                </button>
                <p className="text-xs text-gray-400 text-center">
                  Need access?{" "}
                  <button className="text-primary font-semibold" onClick={() => navigate("/buy")}>
                    Talk to us
                  </button>
                </p>
              </div>
            ) : null}

            <div
              className={`space-y-3 text-sm text-gray-700 ${
                supportsKeycloak ? "border-t border-dashed border-gray-200 pt-4" : ""
              }`}
            >
              <p className="flex items-center gap-2 font-semibold text-gray-900">
                <Sparkles size={16} className="text-primary" />
                Explore the Dyocense demo workspace
              </p>
              <p className="text-xs text-gray-500">
                Launch a guided sandbox with sample data to experience playbooks and copilots before connecting your own
                systems.
              </p>
              <button
                className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full border border-primary text-primary font-semibold bg-white shadow hover:bg-blue-50 transition"
                onClick={() => void loginDemo()}
              >
                <Sparkles size={18} />
                Preview with demo data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
