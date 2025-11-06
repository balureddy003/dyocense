import { ArrowRight, CheckCircle2, Shield, Sparkles, Workflow, Zap, TrendingUp, Users, Package, Calendar, DollarSign, BarChart3, Target, Clock, BookOpen, Newspaper, Database, Cpu, Blocks } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

const FEATURE_CARDS = [
  {
    title: "No Learning Curve Required",
    description:
      "Just describe your goal in plain English. No training, no manuals, no complicated setup. Start getting actionable recommendations in minutes.",
    icon: Sparkles,
  },
  {
    title: "Stop Wasting Money on Mistakes",
    description:
      "Get data-driven answers to your biggest questions: How much inventory? How many staff? What should I charge? Eliminate costly guesswork.",
    icon: Target,
  },
  {
    title: "See ROI This Week, Not Next Year",
    description:
      "Pre-built solutions for common business challenges. Start saving money immediately—most customers see positive ROI within the first month.",
    icon: Clock,
  },
];

const USE_CASES = [
  {
    title: "Never Run Out of Stock Again",
    description: "Predict demand, automate reordering, and reduce overstock. Know exactly what to order and when—saving you money and keeping customers happy.",
    icon: Package,
    benefit: "Reduce inventory costs by 20-30%",
  },
  {
    title: "Perfect Your Staffing Schedule",
    description: "Match labor to demand. Create optimal schedules, reduce overtime costs, and ensure you're always properly staffed during peak hours.",
    icon: Calendar,
    benefit: "Cut labor costs by 15-25%",
  },
  {
    title: "Boost Your Bottom Line",
    description: "Optimize pricing, reduce waste, and improve cash flow. Get clear recommendations to increase profitability across your entire operation.",
    icon: DollarSign,
    benefit: "Increase profit margins by 10-20%",
  },
];

const PRICING_TIERS = [
  {
    name: "Starter",
    price: "$49",
    period: "/month",
    description: "Perfect for single-location businesses",
    features: [
      "1 location or business unit",
      "10 business decisions per month",
      "3 team members",
      "Email support",
      "Basic templates & integrations",
      "7-day free trial",
    ],
    cta: "Start Free Trial",
    highlight: false,
  },
  {
    name: "Growth",
    price: "$199",
    period: "/month",
    description: "For businesses ready to scale",
    features: [
      "Up to 3 locations",
      "50 business decisions per month",
      "10 team members",
      "Priority support + chat",
      "Advanced analytics & forecasting",
      "API access for integrations",
      "Custom data connectors",
    ],
    cta: "Start Free Trial",
    highlight: true,
  },
  {
    name: "Business",
    price: "$499",
    period: "/month",
    description: "For multi-location operations",
    features: [
      "Up to 10 locations",
      "200 business decisions per month",
      "25 team members",
      "Dedicated success manager",
      "Custom integrations & workflows",
      "SSO & advanced security",
      "White-label options",
    ],
    cta: "Contact Sales",
    highlight: false,
  },
];

const VALUE_POINTS = [
  "Start making better decisions in under 30 minutes",
  "No consultants, no data scientists, no complicated software",
  "Works with your existing data—spreadsheets, POS systems, or manual entry",
  "See real results within the first week",
  "Cancel anytime—no contracts, no hidden fees",
];

const TESTIMONIALS = [
  {
    quote: "Dyocense helped us reduce overstock by 35% in the first month. It's like having a business analyst on our team.",
    author: "Sarah Chen",
    role: "Owner, Urban Threads Boutique",
  },
  {
    quote: "We were wasting so much on labor costs. The smart scheduling alone paid for itself in two weeks.",
    author: "Marcus Johnson", 
    role: "Manager, Riverside Cafe",
  },
  {
    quote: "Finally, AI that actually solves my problems instead of making me feel stupid. Worth every penny.",
    author: "Priya Patel",
    role: "CEO, TechFix Repairs",
  },
];

const COMPARISON_TABLE = [
  {
    feature: "Decision Accuracy",
    others: "Basic suggestions based on patterns",
    dyocense: "Proven mathematical methods that deliver the best possible results",
  },
  {
    feature: "Forecasting",
    others: "Simple estimates or guesswork",
    dyocense: "Smart predictions that account for seasons, trends, and your business patterns",
  },
  {
    feature: "Business Rules",
    others: "Can't handle complex situations",
    dyocense: "Respects your budgets, capacity limits, and business policies automatically",
  },
  {
    feature: "Understanding Decisions",
    others: "No explanation - 'Trust the AI'",
    dyocense: "Clear explanations showing exactly why each recommendation makes sense",
  },
  {
    feature: "Data Import",
    others: "Manual data entry or limited options",
    dyocense: "Connects to Excel, your POS system, accounting software, or any tool you use",
  },
  {
    feature: "Reliability",
    others: "No way to verify recommendations",
    dyocense: "Every recommendation is checked against your business rules and policies",
  },
  {
    feature: "Results",
    others: "Just ideas and suggestions",
    dyocense: "Real action plans that balance cost, time, quality, and profit",
  },
];

const BLOG_POSTS = [
  {
    type: "Customer Story",
    title: "How Urban Threads Reduced Overstock by 35% in 30 Days",
    excerpt: "Sarah Chen shares how Dyocense transformed her boutique's inventory management and saved thousands in holding costs.",
    date: "November 1, 2025",
    readTime: "5 min read",
    image: "customer-story",
    tag: "Success Story",
  },
  {
    type: "Feature Update",
    title: "New: Manage Multiple Locations from One Dashboard",
    excerpt: "Run all your stores from a single screen with our latest update. Plus, smarter predictions that factor in weather and local events.",
    date: "October 28, 2025",
    readTime: "3 min read",
    image: "product-update",
    tag: "Product News",
  },
  {
    type: "Customer Story",
    title: "Riverside Cafe Cuts Labor Costs by 22% with Smart Scheduling",
    excerpt: "Learn how Marcus Johnson optimized his cafe's staffing and improved employee satisfaction at the same time.",
    date: "October 20, 2025",
    readTime: "6 min read",
    image: "customer-story",
    tag: "Success Story",
  },
  {
    type: "Guide",
    title: "5 Signs Your Business Needs AI Decision Support",
    excerpt: "Are you still making critical business decisions based on gut feeling? Here's how to know when it's time for an upgrade.",
    date: "October 15, 2025",
    readTime: "4 min read",
    image: "guide",
    tag: "Best Practices",
  },
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
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-white via-blue-50/40 to-blue-100/30 text-gray-900">
      <BrandedHeader showNav={false} />

      <main className="flex-1 px-6">
        {/* Hero Section */}
        <section className="max-w-5xl mx-auto text-center py-20 space-y-6">
          <p className="text-primary font-semibold uppercase tracking-widest text-xs">Your AI Business Agent</p>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
            Stop Losing Money on<br />Guesswork and Gut Feelings
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            <strong>Dyocense</strong> gives small business owners AI-powered recommendations for inventory, 
            staffing, and pricing—so you can save 20-30% on costs and boost profits by up to 20%.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm pt-4">
            <button
              className="px-8 py-4 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl hover:bg-blue-700 transition flex items-center gap-2 text-base"
              onClick={startFreeTrial}
            >
              <Zap size={20} />
              Start Free 7-Day Trial
            </button>
            <button
              className="px-8 py-4 rounded-full bg-white border-2 border-gray-200 text-gray-700 font-semibold hover:border-primary hover:text-primary transition text-base"
              onClick={startFree}
            >
              Get Started Free Forever
            </button>
          </div>
          <p className="text-sm text-gray-500 pt-2">
            ✓ No credit card required  ✓ Setup in under 5 minutes  ✓ Cancel anytime
          </p>
        </section>

        {/* Social Proof */}
        <section className="max-w-4xl mx-auto py-8 text-center">
          <p className="text-sm text-gray-500 mb-6">Join 500+ small businesses already saving money with Dyocense</p>
          <div className="flex flex-wrap justify-center items-center gap-12 text-gray-700">
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center gap-2 text-2xl font-bold text-primary">
                <DollarSign size={28} />
                <span>$2M+</span>
              </div>
              <span className="text-xs font-medium text-gray-500">Saved for Customers</span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center gap-2 text-2xl font-bold text-primary">
                <Users size={28} />
                <span>500+</span>
              </div>
              <span className="text-xs font-medium text-gray-500">Active Businesses</span>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center gap-2 text-2xl font-bold text-primary">
                <TrendingUp size={28} />
                <span>18%</span>
              </div>
              <span className="text-xs font-medium text-gray-500">Avg. Profit Increase</span>
            </div>
          </div>
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
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">What Dyocense Can Do For You</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Solve Your Biggest Business Headaches
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Stop wasting money on guesswork. Get AI-powered recommendations for the decisions 
              that matter most to your bottom line.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {USE_CASES.map((useCase) => {
              const Icon = useCase.icon;
              return (
                <article
                  key={useCase.title}
                  className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition"
                >
                  <Icon size={32} className="text-primary mb-4" />
                  <h3 className="text-lg font-semibold mb-2">{useCase.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed mb-4">{useCase.description}</p>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold">
                    <CheckCircle2 size={14} />
                    {useCase.benefit}
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* Testimonials */}
        <section className="max-w-6xl mx-auto py-16">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Customer Success Stories</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Real Results from Real Businesses
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {TESTIMONIALS.map((testimonial) => (
              <article
                key={testimonial.author}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
              >
                <p className="text-gray-700 italic mb-4">"{testimonial.quote}"</p>
                <div className="border-t border-gray-100 pt-4">
                  <p className="font-semibold text-gray-900 text-sm">{testimonial.author}</p>
                  <p className="text-xs text-gray-500">{testimonial.role}</p>
                </div>
              </article>
            ))}
          </div>
          
          {/* Trust Badges */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <p className="text-center text-sm text-gray-500 mb-6">Trusted and Secure</p>
            <div className="flex flex-wrap justify-center items-center gap-8 text-gray-600">
              <div className="flex items-center gap-2 text-sm">
                <Shield size={20} className="text-green-600" />
                <span>Bank-Level Security</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle2 size={20} className="text-green-600" />
                <span>SOC 2 Compliant</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Shield size={20} className="text-green-600" />
                <span>GDPR Ready</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle2 size={20} className="text-green-600" />
                <span>99.9% Uptime SLA</span>
              </div>
            </div>
          </div>
        </section>

        {/* Why We're Different */}
        <section className="max-w-6xl mx-auto py-16">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Not Just Another AI Tool</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Dyocense Delivers Real Results
            </h2>
            <p className="text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Most AI tools just chat and suggest ideas. Dyocense combines three powerful technologies to give you 
              <strong> proven, reliable recommendations</strong> you can actually use—not just guesses.
            </p>
          </div>

          {/* Key Differentiators */}
          <div className="grid gap-6 md:grid-cols-3 mb-12">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl p-6 shadow-lg">
              <div className="text-3xl font-bold mb-2">1</div>
              <div className="text-sm font-semibold mb-3 text-blue-100">Understands Your Goals</div>
              <p className="text-sm text-blue-50 leading-relaxed">
                Just tell us what you want in plain English. Our AI understands your business needs like a consultant would.
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-2xl p-6 shadow-lg">
              <div className="text-3xl font-bold mb-2">2</div>
              <div className="text-sm font-semibold mb-3 text-purple-100">Predicts What's Coming</div>
              <p className="text-sm text-purple-50 leading-relaxed">
                Smart forecasting looks at your history, seasonal patterns, and trends to predict future needs accurately.
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-600 to-green-700 text-white rounded-2xl p-6 shadow-lg">
              <div className="text-3xl font-bold mb-2">3</div>
              <div className="text-sm font-semibold mb-3 text-green-100">Finds the Best Solution</div>
              <p className="text-sm text-green-50 leading-relaxed">
                Advanced math (the same techniques used by large companies) finds the most profitable solution for your situation.
              </p>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4">
              <h3 className="text-xl font-bold">Dyocense vs. Other AI Tools</h3>
              <p className="text-sm text-blue-100 mt-1">See what makes us different</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Capability</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-600">Other AI Agents</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-primary">Dyocense</th>
                  </tr>
                </thead>
                <tbody>
                  {COMPARISON_TABLE.map((row, idx) => (
                    <tr 
                      key={row.feature} 
                      className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.feature}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{row.others}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-2">
                          <CheckCircle2 size={16} className="text-green-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-900 font-medium">{row.dyocense}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="bg-blue-50 border-t border-blue-100 px-6 py-4">
              <div className="flex items-start gap-3">
                <Shield size={20} className="text-primary mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-900 mb-1">The Bottom Line</p>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    Other AI tools give you ideas. Dyocense gives you <strong>tested, reliable action plans</strong> that 
                    show their work and explain the reasoning. That's the difference between suggestions and decisions 
                    you can confidently act on.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Simple, Transparent Pricing</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Start Free, Upgrade When You're Ready
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              No hidden fees, no surprises. Choose the plan that fits your business.
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
                  <span className="text-gray-600 ml-2 text-sm">{tier.period}</span>
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
                    if (tier.name === "Professional") startFreeTrial();
                    else if (tier.name === "Free Forever") startFree();
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

        {/* Blog & Updates Section */}
        <section id="blog" className="max-w-6xl mx-auto py-16">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Latest Updates</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Customer Stories & Product News
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Real results from real businesses, plus the latest features and best practices.
            </p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {BLOG_POSTS.map((post) => (
              <article
                key={post.title}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition group cursor-pointer"
                onClick={() => navigate("/blog")}
              >
                {/* Image Placeholder */}
                <div className={`h-40 ${
                  post.image === "customer-story" 
                    ? "bg-gradient-to-br from-green-400 to-green-600" 
                    : post.image === "product-update"
                    ? "bg-gradient-to-br from-blue-400 to-blue-600"
                    : "bg-gradient-to-br from-purple-400 to-purple-600"
                } flex items-center justify-center`}>
                  {post.image === "customer-story" ? (
                    <Users size={48} className="text-white opacity-90" />
                  ) : post.image === "product-update" ? (
                    <Sparkles size={48} className="text-white opacity-90" />
                  ) : (
                    <BookOpen size={48} className="text-white opacity-90" />
                  )}
                </div>
                
                {/* Content */}
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                      post.tag === "Success Story" 
                        ? "bg-green-50 text-green-700" 
                        : post.tag === "Product News"
                        ? "bg-blue-50 text-blue-700"
                        : "bg-purple-50 text-purple-700"
                    }`}>
                      {post.tag}
                    </span>
                  </div>
                  
                  <h3 className="text-base font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-primary transition">
                    {post.title}
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3 leading-relaxed">
                    {post.excerpt}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{post.date}</span>
                    <span>{post.readTime}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
          
          <div className="text-center mt-10">
            <button
              onClick={() => navigate("/blog")}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-white border-2 border-gray-200 text-gray-700 font-semibold hover:border-primary hover:text-primary transition"
            >
              <Newspaper size={18} />
              View All Updates
            </button>
          </div>
        </section>

        {/* Marketplace Teaser */}
        <section className="max-w-6xl mx-auto py-16 bg-gradient-to-br from-purple-50 to-blue-50 rounded-3xl px-8 my-12">
          <div className="text-center mb-12">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold mb-3">Ecosystem</p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Connect Everything You Already Use
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Pre-built connections to popular business tools, plus advanced integrations for AI-powered workflows.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <Database size={32} className="text-primary mb-4" />
              <h3 className="text-lg font-semibold mb-2">20+ Data Connectors</h3>
              <p className="text-sm text-gray-600 mb-4">
                Connect Shopify, Square, QuickBooks, Toast, and more. Your data flows automatically.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Shopify</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Square</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">QuickBooks</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">+17 more</span>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <Cpu size={32} className="text-primary mb-4" />
              <h3 className="text-lg font-semibold mb-2">Advanced AI Integrations</h3>
              <p className="text-sm text-gray-600 mb-4">
                Use Dyocense directly in popular AI tools like Claude and development environments.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Claude Desktop</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Development Tools</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Custom Apps</span>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <Blocks size={32} className="text-primary mb-4" />
              <h3 className="text-lg font-semibold mb-2">Ready-to-Use Templates</h3>
              <p className="text-sm text-gray-600 mb-4">
                Pre-built solutions for common business needs—just plug in your data and go.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Inventory</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Staffing</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">Pricing</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">+5 more</span>
              </div>
            </div>
          </div>

          <div className="text-center">
            <button
              onClick={() => navigate("/marketplace")}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-white font-semibold hover:shadow-lg transition"
            >
              <Package size={18} />
              Explore Marketplace
            </button>
          </div>
        </section>

        {/* Why Dyocense */}
        <section id="platform" className="max-w-5xl mx-auto py-16 grid gap-10 md:grid-cols-[minmax(0,1fr)_320px]">
          <div className="bg-white rounded-3xl border border-gray-100 p-8 shadow-sm space-y-6">
            <p className="text-xs uppercase text-primary tracking-widest font-semibold">Why Business Owners Choose Dyocense</p>
            <h2 className="text-3xl font-bold text-gray-900">AI That Actually Helps You Run Your Business</h2>
            <p className="text-gray-600 leading-relaxed">
              We built Dyocense because small business owners don't need more dashboards—they need 
              <strong> better decisions</strong>. Our AI agent understands your business challenges and 
              gives you clear, actionable recommendations you can implement today.
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
            <p className="text-xs uppercase tracking-widest font-semibold text-white/80">Get Started Today</p>
            <h3 className="text-xl font-semibold">See Results This Week</h3>
            <ul className="space-y-3 text-sm">
              <li>✓ 5-minute setup—no training required</li>
              <li>✓ Works with Excel, POS, or manual data</li>
              <li>✓ Get your first AI recommendation today</li>
              <li>✓ Free support to help you succeed</li>
            </ul>
            <button
              className="mt-6 px-4 py-2 rounded-full bg-white text-primary font-semibold hover:shadow-xl transition w-full"
              onClick={() => navigate("/buy?plan=trial")}
            >
              Start Free Trial
            </button>
          </aside>
        </section>

        {/* Footer CTA */}
        <section className="max-w-4xl mx-auto text-center py-20">
          <div className="bg-gradient-to-br from-blue-50 to-white rounded-3xl p-12 border border-blue-100 shadow-lg">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Stop Losing Money. Start Making Smarter Decisions.
            </h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Join 500+ small businesses saving 20-30% on costs with AI-powered recommendations. 
              Get started in 5 minutes—no credit card required.
            </p>
            <div className="flex flex-wrap justify-center gap-4 mb-6">
              <button
                className="px-8 py-4 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl hover:bg-blue-700 transition flex items-center gap-2 text-lg"
                onClick={startFreeTrial}
              >
                <Zap size={22} />
                Start Free 7-Day Trial
              </button>
              <button
                className="px-8 py-4 rounded-full bg-white border-2 border-gray-300 text-gray-700 font-semibold hover:border-primary hover:text-primary hover:shadow-md transition text-lg"
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
            <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600 mb-4">
              <span className="flex items-center gap-1">
                <CheckCircle2 size={16} className="text-green-600" />
                No credit card required
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 size={16} className="text-green-600" />
                Setup in 5 minutes
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 size={16} className="text-green-600" />
                Free forever plan available
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Need help getting started? <a href="mailto:hello@dyocense.com" className="text-primary hover:underline font-medium">Email us</a> or <a href="/demo" className="text-primary hover:underline font-medium">schedule a free demo</a>.
            </p>
          </div>
        </section>
      </main>
      
      <BrandedFooter />
    </div>
  );
};
