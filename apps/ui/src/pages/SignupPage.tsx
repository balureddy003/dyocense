import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BrandedFooter } from "../components/BrandedFooter";
import { BrandedHeader } from "../components/BrandedHeader";
import { devSignup } from "../lib/api";

export const SignupPage = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [company, setCompany] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [devToken, setDevToken] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            const resp = await devSignup({ email, name, company });
            // For dev flow we get the verification token back. Show it and navigate to verify.
            setDevToken(resp.verification_token);
            // Navigate to verify page with token in query so user can continue.
            navigate(`/verify?token=${encodeURIComponent(resp.verification_token)}`);
        } catch (err: any) {
            setError(err?.message || "Signup failed");
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
                        <h1 className="text-2xl font-semibold text-gray-900">Start your free trial</h1>
                        <p className="text-sm text-gray-600">Create a development trial account (dev: token returned directly).</p>
                    </header>

                    <form className="space-y-4" onSubmit={handleSubmit}>
                        <label className="flex flex-col gap-2 text-sm text-gray-700">
                            Work email
                            <input
                                type="email"
                                className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                                placeholder="you@yourcompany.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </label>

                        <label className="flex flex-col gap-2 text-sm text-gray-700">
                            Full name (optional)
                            <input
                                className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                                placeholder="Your name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </label>

                        <label className="flex flex-col gap-2 text-sm text-gray-700">
                            Company (optional)
                            <input
                                className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                                placeholder="ACME Supplies"
                                value={company}
                                onChange={(e) => setCompany(e.target.value)}
                            />
                        </label>

                        {error && <p className="text-sm text-red-500">{error}</p>}

                        <div className="flex flex-col gap-2">
                            <button
                                type="submit"
                                className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition disabled:opacity-70"
                                disabled={submitting}
                            >
                                {submitting ? "Creating trial…" : "Start free trial"}
                            </button>

                            <button
                                type="button"
                                className="text-xs text-primary font-semibold"
                                onClick={() => navigate("/login")}
                            >
                                Have an account? Sign in
                            </button>
                        </div>
                    </form>

                    {devToken && (
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                            Dev verification token (copy/paste to verify): <strong>{devToken}</strong>
                        </div>
                    )}
                </div>
            </div>

            <BrandedFooter />
        </div>
    );
};

export default SignupPage;
