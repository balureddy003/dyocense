import { useEffect } from "react";
import { useLocation, useNavigate, NavigateFunction } from "react-router-dom";
import { LogIn, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const resolveRedirect = (navigate: NavigateFunction, target: string) => {
  if (!target.startsWith("http")) {
    navigate(target, { replace: true });
    return;
  }
  window.location.href = target;
};

export const LoginPage = () => {
  const { ready, authenticated, login, profile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const redirectTarget = params.get("redirect") || "/home";

  useEffect(() => {
    if (!ready) return;
    if (authenticated) {
      const next = profile ? redirectTarget : "/profile";
      resolveRedirect(navigate, next);
    }
  }, [authenticated, profile, ready, navigate, redirectTarget]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100 px-4">
      <div className="max-w-md w-full bg-white border border-gray-100 rounded-2xl shadow-xl p-8 space-y-6">
        <header className="space-y-2 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white font-semibold text-lg">
            D
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Welcome back to Dyocense</h1>
          <p className="text-sm text-gray-600">
            Sign in securely with your enterprise identity. We use Keycloak to keep your data protected and compliant.
          </p>
        </header>
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
        </div>
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
    </div>
  );
};
