import { ArrowRight, CheckCircle2, Sparkles, Zap } from "lucide-react";
import React from "react";
import { useNavigate } from "react-router-dom";
import { BrandedFooter } from "../components/BrandedFooter";
import { BrandedHeader } from "../components/BrandedHeader";
import { useAuth } from "../context/AuthContext";

const FEATURE_CARDS = [
  {
    title: "No Learning Curve Required",
    description: "Just describe your goal in plain English and get actionable recommendations in minutes.",
    icon: Sparkles,
  },
  {
    title: "Reduce Costly Mistakes",
    description: "Get data-driven answers for inventory, staffing, and pricing to eliminate guesswork.",
    icon: ArrowRight,
  },
  {
    title: "Fast ROI",
    description: "Most customers see measurable gains in the first few weeks.",
    icon: CheckCircle2,
  },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { authenticated } = useAuth();

  const startFreeTrial = () => navigate("/signup?plan=trial");
  const startFree = () => navigate("/signup?plan=free");
  const goToLogin = (redirect: string) => navigate(`/login?redirect=${encodeURIComponent(redirect)}`);

  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      <BrandedHeader showNav={false} />

      <main className="flex-1 px-6">
        <section className="max-w-5xl mx-auto text-center py-20">
          <p className="text-primary font-semibold uppercase tracking-widest text-xs">Your AI Business Agent</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight mt-4">Stop Losing Money on Guesswork</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto mt-4">Dyocense gives small business owners AI-powered recommendations for inventory, staffing, and pricing—so you can save money and operate with confidence.</p>

          <div className="flex justify-center gap-4 mt-8">
            <button className="px-6 py-3 rounded-full bg-primary text-white font-semibold" onClick={startFreeTrial}><Zap size={18} /> Start Free Trial</button>
            <button className="px-6 py-3 rounded-full border border-gray-200 text-gray-700" onClick={startFree}>Get Started Free</button>
          </div>
        </section>

        <section className="max-w-6xl mx-auto py-12">
          <div className="grid gap-6 md:grid-cols-3">
            {FEATURE_CARDS.map((f) => {
              const Icon = f.icon as any;
              return (
                <article key={f.title} className="bg-white border rounded-2xl p-6 shadow-sm">
                  <div className="p-3 rounded-full bg-blue-50 inline-flex mb-4"><Icon size={22} className="text-primary" /></div>
                  <h3 className="text-xl font-semibold">{f.title}</h3>
                  <p className="text-sm text-gray-600 mt-2">{f.description}</p>
                </article>
              );
            })}
          </div>
        </section>
      </main>

      <BrandedFooter />
    </div>
  );
};

export { LandingPage };
export default LandingPage;
