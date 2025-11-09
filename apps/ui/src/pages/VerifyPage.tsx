import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { BrandedFooter } from "../components/BrandedFooter";
import { BrandedHeader } from "../components/BrandedHeader";
import { useAuth } from "../context/AuthContext";
import { devVerify } from "../lib/api";

function useQuery() {
    return new URLSearchParams(useLocation().search);
}

export const VerifyPage = () => {
    const query = useQuery();
    const navigate = useNavigate();
    const { loginWithToken } = useAuth();

    const [token, setToken] = useState(query.get("token") || "");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (query.get("token")) {
            setToken(query.get("token") || "");
        }
    }, [query]);

    const handleVerify = async (e?: React.FormEvent) => {
        e?.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            const resp = await devVerify(token);
            if (!resp.jwt) {
                setError("Invalid or expired token.");
                setSubmitting(false);
                return;
            }

            // Use AuthContext helper to login with returned JWT (dev token)
            await loginWithToken({ apiToken: resp.jwt, tenantId: resp.tenant_id });

            // Redirect to home and include tenant/workspace as query params when present.
            // The React Router app currently serves the workspace UI at /home; including
            // tenant/workspace as query params preserves context without relying on a
            // Next.js-style dynamic route.
            const qp: string[] = [];
            if (resp.tenant_id) qp.push(`tenant=${encodeURIComponent(resp.tenant_id)}`);
            if (resp.workspace_id) qp.push(`workspace=${encodeURIComponent(resp.workspace_id)}`);
            const qs = qp.length ? `?${qp.join("&")}` : "";
            navigate(`/home${qs}`);
        } catch (err: any) {
            setError(err?.message || "Verification failed");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
            <BrandedHeader showNav={false} />

            <div className="flex-1 flex items-center justify-center px-4 py-8">
                <div className="max-w-md w-full bg-white border border-gray-100 rounded-2xl shadow-xl p-8 space-y-6">
                    <header className="text-center">
                        <h1 className="text-2xl font-semibold text-gray-900">Verify your account</h1>
                        <p className="text-sm text-gray-600">Paste the verification token you received (dev mode returns token directly).</p>
                    </header>

                    <form className="space-y-4" onSubmit={handleVerify}>
                        <label className="flex flex-col gap-2 text-sm text-gray-700">
                            Verification token
                            <input
                                className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                                placeholder="paste token here"
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                required
                            />
                        </label>

                        {error && <p className="text-sm text-red-500">{error}</p>}

                        <div className="flex flex-col gap-2">
                            <button
                                type="submit"
                                className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                                disabled={submitting}
                            >
                                {submitting ? "Verifying…" : "Verify account"}
                            </button>

                            <button
                                type="button"
                                className="text-xs text-primary font-semibold"
                                onClick={() => navigate("/login")}
                            >
                                Back to sign in
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <BrandedFooter />
        </div>
    );
};

export default VerifyPage;
