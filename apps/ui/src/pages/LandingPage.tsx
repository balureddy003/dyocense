import { ArrowRight, CheckCircle2, Shield, Sparkles, Workflow } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const FEATURE_CARDS = [
  {
    title: "Decision operating system",
    description:
      "Align teams around scenario-based playbooks that keep planning, execution, and measurement in one loop.",
    icon: Workflow,
  },
  {
    title: "AI copilots everywhere",
    description:
      "Guide planners with contextual copilots that surface signals, automate analysis, and capture institutional knowledge.",
    icon: Sparkles,
  },
  {
    title: "Enterprise-grade controls",
    description:
      "Enforce guardrails, approvals, and audit trails with our governance layer built for regulated industries.",
    icon: Shield,
  },
];

const VALUE_POINTS = [
  "Bootstrap in weeks with pre-built supply chain archetypes",
  "Blend internal and external data feeds without re-platforming",
  "Collaborate across Ops, Finance, and Merchandising workstreams",
];

export const LandingPage = () => {
  const navigate = useNavigate();
  const { login, authenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50/40 to-blue-100/30 text-gray-900">
      <header className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3 text-primary text-xl font-semibold">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-bold">
            D
          </span>
          Dyocense
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm text-gray-600">
          <button className="hover:text-primary" onClick={() => navigate("/#platform")}>
            Platform
          </button>
          <button className="hover:text-primary" onClick={() => navigate("/#solutions")}>
            Solutions
          </button>
          <button className="hover:text-primary" onClick={() => navigate("/#pricing")}>
            Pricing
          </button>
          <button className="hover:text-primary" onClick={() => navigate("/#resources")}>
            Resources
          </button>
        </nav>
        <div className="flex items-center gap-3 text-sm">
          <button
            className="px-4 py-2 text-primary font-semibold rounded-full border border-primary hover:bg-primary hover:text-white transition"
            onClick={() => void login(`${window.location.origin}/home`)}
          >
            {authenticated ? "Go to platform" : "Sign in"}
          </button>
          <button
            className="px-4 py-2 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition flex items-center gap-2"
            onClick={() => navigate("/buy")}
          >
            Buy Dyocense <ArrowRight size={16} />
          </button>
        </div>
      </header>

      <main className="px-6">
        <section className="max-w-5xl mx-auto text-center py-20 space-y-6">
          <p className="text-primary font-semibold uppercase tracking-widest text-xs">Dyocense Platform</p>
          <h1 className="text-4xl md:text-5xl font-semibold leading-tight">
            The AI-native command center for supply chain and planning teams.
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Unite data, copilots, and KPIs in an adaptive operating system. Move from fire drills to proactive,
            scenario-driven decisions in every planning cycle.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <button
              className="px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-card flex items-center gap-2 hover:shadow-lg transition"
              onClick={() => void login(`${window.location.origin}/home`)}
            >
              Explore the platform <ArrowRight size={16} />
            </button>
            <button
              className="px-5 py-3 rounded-full bg-white border border-gray-200 text-gray-700 font-semibold hover:border-primary transition"
              onClick={() => navigate("/buy")}
            >
              Talk to our team
            </button>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {FEATURE_CARDS.map((feature) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className="bg-white/90 border border-blue-100 rounded-3xl p-6 text-left shadow-sm hover:shadow-md transition"
                >
                  <Icon size={26} className="text-primary" />
                  <h3 className="text-lg font-semibold mt-4">{feature.title}</h3>
                  <p className="text-sm text-gray-600 mt-2 leading-6">{feature.description}</p>
                </article>
              );
            })}
          </div>
        </section>

        <section id="platform" className="max-w-5xl mx-auto py-16 grid gap-10 md:grid-cols-[minmax(0,1fr)_320px]">
          <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm space-y-4">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold">Platform value</p>
            <h2 className="text-2xl font-semibold text-gray-900">Why teams choose Dyocense</h2>
            <p className="text-sm text-gray-600 leading-6">
              Dyocense compresses the time between insight and action. Configure data ingestion, orchestrate
              simulations, and roll out execution playbooks with approvals built in.
            </p>
            <ul className="space-y-3 text-sm text-gray-700">
              {VALUE_POINTS.map((point) => (
                <li key={point} className="flex items-start gap-3">
                  <CheckCircle2 size={18} className="text-primary mt-0.5" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
          <aside className="bg-gradient-to-br from-blue-600 to-blue-500 text-white rounded-3xl p-6 shadow-lg space-y-4">
            <p className="text-xs uppercase tracking-widest font-semibold text-white/80">Launch in 30 days</p>
            <h3 className="text-xl font-semibold">Starter bundle</h3>
            <ul className="space-y-3 text-sm">
              <li>• 2 decision archetypes</li>
              <li>• Managed data onboarding</li>
              <li>• 3 guided playbooks with live KPIs</li>
            </ul>
            <button
              className="mt-6 px-4 py-2 rounded-full bg-white text-primary font-semibold"
              onClick={() => navigate("/buy")}
            >
              Request pricing
            </button>
          </aside>
        </section>
      </main>
    </div>
  );
};
