import { ArrowRight, CheckCircle2, Shield, Sparkles, Workflow, Zap, TrendingUp, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const FEATURE_CARDS = [
  {
    title: "AI-Powered Decision Intelligence",
    description:
      "Turn natural language goals into optimal, explainable decisions. Our Decision Kernel combines LLMs, forecasting, and operational research.",
    icon: Sparkles,
  },
  {
    title: "Built for Small Businesses",
    description:
      "No data science expertise needed. Start with pre-built supply chain archetypes and scale as you grow.",
    icon: Users,
  },
  {
    title: "Enterprise-Grade Compliance",
    description:
      "Built-in explainability, audit trails, and policy verification. Trust and compliance from day one.",
    icon: Shield,
  },
];

const USE_CASES = [
  {
    title: "Inventory Optimization",
    description: "Reduce stockouts and overstock with AI-driven demand forecasting and replenishment planning.",
    icon: TrendingUp,
  },
  {
    title: "Workforce Planning",
    description: "Optimize staffing schedules, manage shifts, and forecast labor needs across your business.",
    icon: Users,
  },
  {
    title: "Supply Chain Planning",
    description: "End-to-end visibility and optimization from procurement to delivery.",
    icon: Workflow,
  },
];

const PRICING_TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for exploring Dyocense capabilities",
    features: [
      "1 active project",
      "3 AI playbooks",
      "2 team members",
      "Community support",
    ],
    cta: "Start Free",
    highlight: false,
  },
  {
    name: "Silver Trial",
    price: "$0",
    period: "7 days free",
    description: "Full-featured trial for serious evaluation",
    features: [
      "5 active projects",
      "25 AI playbooks",
      "15 team members",
      "Business-hours support",
      "Evidence history export",
      "Then $149/month",
    ],
    cta: "Start Free Trial",
    highlight: true,
  },
  {
    name: "Gold",
    price: "$499",
    period: "/month",
    description: "For growing businesses with complex needs",
    features: [
      "20 active projects",
      "150 AI playbooks",
      "75 team members",
      "Priority support",
      "SSO + SCIM",
    ],
    cta: "Contact Sales",
    highlight: false,
  },
];

const VALUE_POINTS = [
  "Launch in weeks with pre-built supply chain archetypes",
  "Blend internal and external data without re-platforming",
  "Collaborate across Ops, Finance, and Merchandising",
  "Explainable AI decisions with full audit trails",
];

export const LandingPage = () => {
  const navigate = useNavigate();
  const { authenticated } = useAuth();
  
  const startFreeTrial = () => {
    navigate("/buy?plan=trial");
  };
  
  const startFree = () => {
    navigate("/buy?plan=free");
  };
  
  const goToLogin = (redirect: string) => {
    const encoded = encodeURIComponent(redirect);
    navigate(`/login?redirect=${encoded}`);
  };

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
            onClick={() => {
              if (authenticated) {
                navigate("/home");
              } else {
                goToLogin("/home");
              }
            }}
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
        {/* Hero Section */}
        <section className="max-w-5xl mx-auto text-center py-20 space-y-6">
          <p className="text-primary font-semibold uppercase tracking-widest text-xs">Decision Intelligence Platform</p>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
            Turn AI Insights Into Optimal Decisions
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            The missing Decision Kernel for small businesses. Get explainable, optimal plans for inventory, 
            staffing, and supply chain—without needing a data science team.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm pt-4">
            <button
              className="px-6 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition flex items-center gap-2 text-base"
              onClick={startFreeTrial}
            >
              <Zap size={18} />
              Start 7-Day Free Trial
            </button>
            <button
              className="px-6 py-3 rounded-full bg-white border-2 border-gray-200 text-gray-700 font-semibold hover:border-primary hover:text-primary transition text-base"
              onClick={startFree}
            >
              Start Free Forever
            </button>
          </div>
          <p className="text-sm text-gray-500 pt-2">
            No credit card required • Full access during trial • Upgrade anytime
          </p>
        </section>

        {/* Feature Cards */}
        <section className="max-w-6xl mx-auto py-12">
          <div className="grid gap-6 md:grid-cols-3">
            {FEATURE_CARDS.map((feature) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className="bg-white border border-blue-100 rounded-2xl p-8 shadow-sm hover:shadow-md transition"
                >
                  <div className="inline-flex p-3 rounded-xl bg-blue-50 mb-4">
                    <Icon size={28} className="text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
                </article>
              );
            })}
          </div>
        </section>

        {/* Use Cases */}
        <section id="solutions" className="max-w-6xl mx-auto py-16 bg-gradient-to-br from-blue-50 to-white rounded-3xl px-8 my-12">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Use Cases</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Built for Real Business Challenges
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Pre-built archetypes for common supply chain and planning scenarios. 
              Deploy in weeks, not months.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {USE_CASES.map((useCase) => {
              const Icon = useCase.icon;
              return (
                <article
                  key={useCase.title}
                  className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
                >
                  <Icon size={32} className="text-primary mb-4" />
                  <h3 className="text-lg font-semibold mb-2">{useCase.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{useCase.description}</p>
                </article>
              );
            })}
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Pricing</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Start Free, Scale As You Grow
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Try Dyocense risk-free. No credit card required for Free or Trial tiers.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {PRICING_TIERS.map((tier) => (
              <article
                key={tier.name}
                className={`rounded-2xl p-8 border-2 ${
                  tier.highlight
                    ? "border-primary bg-gradient-to-br from-blue-50 to-white shadow-xl scale-105"
                    : "border-gray-200 bg-white shadow-sm"
                }`}
              >
                {tier.highlight && (
                  <div className="inline-block px-3 py-1 rounded-full bg-primary text-white text-xs font-semibold mb-4">
                    MOST POPULAR
                  </div>
                )}
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">{tier.price}</span>
                  <span className="text-gray-600 ml-2">{tier.period}</span>
                </div>
                <p className="text-sm text-gray-600 mb-6">{tier.description}</p>
                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => {
                    if (tier.name === "Silver Trial") startFreeTrial();
                    else if (tier.name === "Free") startFree();
                    else navigate("/buy");
                  }}
                  className={`w-full py-3 rounded-full font-semibold transition ${
                    tier.highlight
                      ? "bg-primary text-white shadow-lg hover:shadow-xl"
                      : "bg-white border-2 border-gray-200 text-gray-700 hover:border-primary hover:text-primary"
                  }`}
                >
                  {tier.cta}
                </button>
              </article>
            ))}
          </div>
        </section>

        {/* Why Dyocense */}
        <section id="platform" className="max-w-5xl mx-auto py-16 grid gap-10 md:grid-cols-[minmax(0,1fr)_320px]">
          <div className="bg-white rounded-3xl border border-gray-100 p-8 shadow-sm space-y-6">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold">Why Dyocense</p>
            <h2 className="text-3xl font-bold text-gray-900">The Decision Kernel Small Businesses Need</h2>
            <p className="text-gray-600 leading-relaxed">
              Most AI tools give you insights. Dyocense gives you <strong>optimal decisions</strong>. 
              Our Decision Kernel combines LLMs, forecasting, and operational research to turn your goals 
              into explainable, verified action plans.
            </p>
            <ul className="space-y-4">
              {VALUE_POINTS.map((point) => (
                <li key={point} className="flex items-start gap-3">
                  <CheckCircle2 size={20} className="text-primary mt-1 flex-shrink-0" />
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
            <button
              className="px-6 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition inline-flex items-center gap-2"
              onClick={startFreeTrial}
            >
              Start Your Free Trial <ArrowRight size={18} />
            </button>
          </div>
          <aside className="bg-gradient-to-br from-blue-600 to-blue-500 text-white rounded-3xl p-6 shadow-lg space-y-4 h-fit">
            <p className="text-xs uppercase tracking-widest font-semibold text-white/80">Quick Start</p>
            <h3 className="text-xl font-semibold">Launch in 30 Days</h3>
            <ul className="space-y-3 text-sm">
              <li>✓ Pre-built decision archetypes</li>
              <li>✓ Managed data onboarding</li>
              <li>✓ 3 guided playbooks with live KPIs</li>
              <li>✓ Full team collaboration</li>
            </ul>
            <button
              className="mt-6 px-4 py-2 rounded-full bg-white text-primary font-semibold hover:shadow-xl transition w-full"
              onClick={() => navigate("/buy")}
            >
              Talk to Sales
            </button>
          </aside>
        </section>

        {/* Footer CTA */}
        <section className="max-w-4xl mx-auto text-center py-20">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Ready to Make Better Decisions?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Join small businesses using Dyocense to optimize inventory, staffing, and supply chains.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <button
              className="px-8 py-4 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition flex items-center gap-2 text-lg"
              onClick={startFreeTrial}
            >
              <Zap size={20} />
              Start 7-Day Free Trial
            </button>
            <button
              className="px-8 py-4 rounded-full bg-white border-2 border-gray-200 text-gray-700 font-semibold hover:border-primary hover:text-primary transition text-lg"
              onClick={() => {
                if (authenticated) {
                  navigate("/home");
                } else {
                  goToLogin("/home");
                }
              }}
            >
              {authenticated ? "Go to Dashboard" : "Sign In"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};
