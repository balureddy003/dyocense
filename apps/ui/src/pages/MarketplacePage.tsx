import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  Search, 
  Package, 
  Database, 
  Plug, 
  Blocks,
  ShoppingCart,
  FileSpreadsheet,
  CreditCard,
  Box,
  Cloud,
  Cpu,
  TrendingUp,
  Users,
  Calendar,
  DollarSign,
  CheckCircle2,
  ExternalLink,
  Zap,
  BarChart,
  Globe,
  Lock
} from "lucide-react";
import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

type MarketplaceItem = {
  id: string;
  name: string;
  category: "Data Connector" | "MCP Tool" | "Archetype" | "Solver" | "Integration";
  description: string;
  provider: string;
  icon: any;
  status: "Available" | "Coming Soon" | "Beta";
  pricing: "Free" | "Included" | "Premium" | "Enterprise";
  features: string[];
  compatibleWith?: string[];
  documentation?: string;
  setupTime?: string;
  popular?: boolean;
};

const MARKETPLACE_ITEMS: MarketplaceItem[] = [
  // Data Connectors
  {
    id: "shopify-connector",
    name: "Shopify",
    category: "Data Connector",
    description: "Connect your Shopify store automatically. Keep inventory, orders, and customer data in sync without manual work.",
    provider: "Dyocense",
    icon: ShoppingCart,
    status: "Available",
    pricing: "Included",
    setupTime: "5 minutes",
    features: [
      "Automatic inventory updates",
      "Works with multiple store locations",
      "Complete order history",
      "Customer buying patterns",
      "Product catalog sync"
    ],
    compatibleWith: ["Inventory Helper", "Sales Prediction"],
    popular: true,
  },
  {
    id: "square-connector",
    name: "Square POS",
    category: "Data Connector",
    description: "Connect your Square register. Automatically track sales, inventory levels, and see when you're busiest.",
    provider: "Dyocense",
    icon: CreditCard,
    status: "Available",
    pricing: "Included",
    setupTime: "5 minutes",
    features: [
      "Automatic sales tracking",
      "Employee schedule sync",
      "Payment and tip analysis",
      "Multiple location support",
      "Customer visit patterns"
    ],
    compatibleWith: ["Staff Scheduler", "Inventory Helper"],
    popular: true,
  },
  {
    id: "quickbooks-connector",
    name: "QuickBooks",
    category: "Data Connector",
    description: "Connect your accounting software. Make decisions that respect your budgets and understand your costs.",
    provider: "Dyocense",
    icon: FileSpreadsheet,
    status: "Available",
    pricing: "Included",
    setupTime: "10 minutes",
    features: [
      "Automatic expense tracking",
      "Vendor and supplier info",
      "Budget constraints",
      "Financial reporting",
      "Cost allocation"
    ],
    compatibleWith: ["All Archetypes"],
    popular: true,
  },
  {
    id: "excel-connector",
    name: "Excel / CSV",
    category: "Data Connector",
    description: "Import data from Excel spreadsheets and CSV files. Perfect for businesses without specialized software.",
    provider: "Dyocense",
    icon: FileSpreadsheet,
    status: "Available",
    pricing: "Free",
    setupTime: "2 minutes",
    features: [
      "Drag & drop upload",
      "Template library",
      "Data validation",
      "Bulk import/export",
      "Schedule auto-import"
    ],
    compatibleWith: ["All Business Templates"],
  },
  {
    id: "clover-connector",
    name: "Clover POS",
    category: "Data Connector",
    description: "Integration with Clover point-of-sale systems. Sync sales, inventory, and employee data automatically.",
    provider: "Dyocense",
    icon: CreditCard,
    status: "Coming Soon",
    pricing: "Included",
    setupTime: "5 minutes",
    features: [
      "Sales data sync",
      "Inventory management",
      "Employee scheduling",
      "Customer analytics",
      "Multi-location support"
    ],
    compatibleWith: ["Inventory Optimizer", "Staff Scheduler"],
  },
  {
    id: "toast-connector",
    name: "Toast POS",
    category: "Data Connector",
    description: "For restaurants using Toast. Track menu sales, ingredients, and see your busiest tables and times.",
    provider: "Dyocense",
    icon: CreditCard,
    status: "Coming Soon",
    pricing: "Included",
    setupTime: "5 minutes",
    features: [
      "Track what sells best",
      "Monitor ingredient levels",
      "Understand labor costs",
      "Table and seat analysis",
      "Predict future sales"
    ],
    compatibleWith: ["Restaurant Helper", "Staff Scheduler"],
  },
  {
    id: "warehouse-connector",
    name: "Warehouse Systems",
    category: "Data Connector",
    description: "Connect to warehouse and shipping providers like ShipBob and ShipStation. See all your inventory in one place.",
    provider: "Dyocense",
    icon: Box,
    status: "Beta",
    pricing: "Premium",
    setupTime: "15 minutes",
    features: [
      "Current stock levels everywhere",
      "Multiple warehouse locations",
      "Shipping cost optimization",
      "Third-party warehouse support",
      "Transfer tracking"
    ],
    compatibleWith: ["Inventory Helper", "Supply Chain Planning"],
  },
  {
    id: "api-connector",
    name: "Custom Connection",
    category: "Data Connector",
    description: "Need something special? Our technical team can help you connect any system you use. Enterprise support included.",
    provider: "Dyocense",
    icon: Cloud,
    status: "Available",
    pricing: "Enterprise",
    setupTime: "Variable",
    features: [
      "Custom data connections",
      "Automatic updates",
      "Technical documentation",
      "Developer tools provided",
      "Dedicated support team"
    ],
    compatibleWith: ["All Business Templates"],
  },

  // MCP Tools - Advanced AI Integrations
  {
    id: "mcp-compiler",
    name: "Smart Goal Translator",
    category: "MCP Tool",
    description: "For advanced users: Connect Dyocense to AI tools like Claude. Turns your goals into actionable plans automatically.",
    provider: "Dyocense",
    icon: Cpu,
    status: "Available",
    pricing: "Included",
    features: [
      "Understands plain English",
      "Learns your goals",
      "Handles complex requests",
      "Creates detailed plans",
      "Works conversationally"
    ],
    compatibleWith: ["Claude Desktop", "Developer Tools", "Custom Apps"],
    documentation: "https://docs.dyocense.com/advanced/ai-integration",
  },
  {
    id: "mcp-forecast",
    name: "Smart Predictions",
    category: "MCP Tool",
    description: "For advanced users: Powerful forecasting that works with AI tools. Predicts sales, demand, and trends automatically.",
    provider: "Dyocense",
    icon: TrendingUp,
    status: "Available",
    pricing: "Included",
    features: [
      "Multiple prediction methods",
      "Finds seasonal patterns",
      "Spots trends early",
      "Shows confidence levels",
      "Picks best method automatically"
    ],
    compatibleWith: ["Claude Desktop", "Developer Tools", "Custom Apps"],
    documentation: "https://docs.dyocense.com/advanced/forecasting",
  },
  {
    id: "mcp-optimizer",
    name: "Smart Decision Maker",
    category: "MCP Tool",
    description: "For advanced users: The core engine that finds the best solutions to complex business problems.",
    provider: "Dyocense",
    icon: Zap,
    status: "Available",
    pricing: "Included",
    features: [
      "Linear programming",
      "Mixed-integer optimization",
      "Multi-objective optimization",
      "Constraint handling",
      "Solution explanation"
    ],
    compatibleWith: ["Claude Desktop", "Cline", "Custom MCP Clients"],
    documentation: "https://docs.dyocense.com/mcp/optimizer",
  },
  {
    id: "mcp-explainer",
    name: "Decision Explainer",
    category: "MCP Tool",
    description: "Generate human-readable explanations for optimization results and AI decisions.",
    provider: "Dyocense",
    icon: BarChart,
    status: "Available",
    pricing: "Included",
    features: [
      "Natural language explanations",
      "Trade-off analysis",
      "Sensitivity reports",
      "What-if scenarios",
      "Audit trail generation"
    ],
    compatibleWith: ["Claude Desktop", "Cline", "Custom MCP Clients"],
    documentation: "https://docs.dyocense.com/mcp/explainer",
  },
  {
    id: "mcp-policy",
    name: "Policy Verifier",
    category: "MCP Tool",
    description: "Verify decisions against business policies and compliance rules using Open Policy Agent.",
    provider: "Dyocense",
    icon: Lock,
    status: "Available",
    pricing: "Premium",
    features: [
      "Policy-as-code",
      "Compliance checking",
      "Rule violations detection",
      "Audit logging",
      "Custom policy support"
    ],
    compatibleWith: ["Claude Desktop", "Cline", "Custom MCP Clients"],
    documentation: "https://docs.dyocense.com/mcp/policy",
  },
  {
    id: "marketplace-browser",
    name: "Marketplace Browser - For Advanced Users",
    category: "MCP Tool",
    description: "Browse and discover available business templates, solvers, and connectors programmatically.",
    provider: "Dyocense",
    icon: Globe,
    status: "Available",
    pricing: "Free",
    features: [
      "Catalog browsing",
      "Template discovery",
      "Connector listing",
      "Version management",
      "Metadata queries"
    ],
    compatibleWith: ["Claude Desktop", "Cline", "Custom MCP Clients"],
    documentation: "https://docs.dyocense.com/mcp/marketplace",
  },

  // Ready-to-Use Business Solutions
  {
    id: "inventory-basic",
    name: "Inventory Helper",
    category: "Archetype",
    description: "Never run out or overstock again. Tells you exactly what to order and when, saving money on storage and avoiding lost sales.",
    provider: "Dyocense",
    icon: Package,
    status: "Available",
    pricing: "Included",
    features: [
      "Predicts what you'll need",
      "Calculates best order sizes",
      "Safety stock recommendations",
      "Smart reorder alerts",
      "Identifies your best sellers"
    ],
    compatibleWith: ["Shopify", "Square", "QuickBooks", "Excel"],
    popular: true,
  },
  {
    id: "staff-scheduler",
    name: "Staff Scheduler",
    category: "Archetype",
    description: "Create perfect work schedules automatically. Match staff to busy times, respect availability, and stay within budget.",
    provider: "Dyocense",
    icon: Users,
    status: "Available",
    pricing: "Included",
    features: [
      "Matches staff to busy periods",
      "Skill matching",
      "Availability constraints",
      "Labor budget optimization",
      "Overtime minimization"
    ],
    compatibleWith: ["Square", "Toast", "Clover", "Excel"],
    popular: true,
  },
  {
    id: "pricing-optimizer",
    name: "Pricing Helper",
    category: "Archetype",
    description: "Find the sweet spot for your prices. Get suggestions on what to charge based on what customers are willing to pay and your costs.",
    provider: "Dyocense",
    icon: DollarSign,
    status: "Available",
    pricing: "Premium",
    features: [
      "Understands customer buying patterns",
      "Watches competitor prices",
      "Plan sales and markdowns",
      "Plan promotions that work",
      "Increase your profit"
    ],
    compatibleWith: ["Shopify", "Square", "Custom API"],
  },
  {
    id: "supply-chain",
    name: "Supply Chain Helper",
    category: "Archetype",
    description: "Manage your entire supply chain from ordering to delivery. Works across multiple locations and products.",
    provider: "Dyocense",
    icon: Box,
    status: "Beta",
    pricing: "Enterprise",
    features: [
      "Manage inventory across locations",
      "Find best suppliers",
      "Plan deliveries and shipping",
      "Schedule production",
      "Plan warehouse network"
    ],
    compatibleWith: ["Warehouse Management", "QuickBooks", "Custom API"],
  },
  {
    id: "restaurant-optimizer",
    name: "Restaurant Helper",
    category: "Archetype",
    description: "Built for restaurants. Plan your menu, order ingredients, schedule prep work, and manage staff efficiently.",
    provider: "Dyocense",
    icon: Calendar,
    status: "Coming Soon",
    pricing: "Premium",
    features: [
      "Optimize menu profitability",
      "Predict ingredient needs",
      "Plan prep schedules",
      "Optimize labor costs",
      "Reduce food waste"
    ],
    compatibleWith: ["Toast", "Square", "Clover"],
  },
  {
    id: "retail-merchandising",
    name: "Retail Helper",
    category: "Archetype",
    description: "Perfect for retail stores. Plan what products to carry, how to arrange your store, and when to run sales.",
    provider: "Dyocense",
    icon: ShoppingCart,
    status: "Coming Soon",
    pricing: "Premium",
    features: [
      "Choose best product mix",
      "Plan store layout",
      "Plan sales and clearances",
      "Manage product categories",
      "Seasonal planning"
    ],
    compatibleWith: ["Shopify", "Square", "Custom API"],
  },

  // Solvers
  {
    id: "or-tools",
    name: "OR-Tools (Google) - For Advanced Users",
    category: "Solver",
    description: "Google's free calculation engine that powers Dyocense recommendations. Fast and reliable for all types of business problems.",
    provider: "Google",
    icon: Blocks,
    status: "Available",
    pricing: "Free",
    features: [
      "Solves scheduling problems",
      "Plans routes and deliveries",
      "Optimizes resource allocation",
      "No extra costs",
      "Used by major companies"
    ],
    compatibleWith: ["All Business Templates"],
    popular: true,
  },
  {
    id: "highs",
    name: "HiGHS - For Advanced Users",
    category: "Solver",
    description: "High-performance free calculation engine. Excellent for handling large amounts of data and complex problems.",
    provider: "University of Edinburgh",
    icon: Blocks,
    status: "Available",
    pricing: "Free",
    features: [
      "Handles large datasets",
      "Fast calculations",
      "Solves complex problems",
      "Parallel processing",
      "Free and open source"
    ],
    compatibleWith: ["All Business Templates"],
  },
  {
    id: "gurobi",
    name: "Gurobi - For Advanced Users",
    category: "Solver",
    description: "Premium calculation engine for complex business problems. Industry standard used by Fortune 500 companies.",
    provider: "Gurobi Optimization",
    icon: Blocks,
    status: "Available",
    pricing: "Enterprise",
    features: [
      "Best-in-class performance",
      "Handles advanced math",
      "Solves complex scenarios",
      "Cloud-based option",
      "Priority support included"
    ],
    compatibleWith: ["All Business Templates"],
  },

  // Integrations
  {
    id: "claude-desktop",
    name: "Claude Desktop - For Advanced Users",
    category: "Integration",
    description: "Use Dyocense recommendations directly inside Claude Desktop. Ask questions in plain English and get smart business advice.",
    provider: "Anthropic",
    icon: Plug,
    status: "Available",
    pricing: "Free",
    features: [
      "Ask questions naturally",
      "Automate decisions",
      "Get instant recommendations",
      "Contextual assistance",
      "Multi-step planning"
    ],
    documentation: "https://docs.dyocense.com/integrations/claude",
    popular: true,
  },
  {
    id: "vscode-cline",
    name: "VSCode with Cline - For Developers",
    category: "Integration",
    description: "Use Dyocense in your coding environment. Perfect for developers who want to build custom business tools.",
    provider: "Microsoft / Cline",
    icon: Plug,
    status: "Available",
    pricing: "Free",
    features: [
      "Build custom solutions",
      "In-editor recommendations",
      "Developer workflow",
      "Version control",
      "Team collaboration"
    ],
    documentation: "https://docs.dyocense.com/integrations/vscode",
  },
  {
    id: "langchain",
    name: "LangChain Tool - For Developers",
    category: "Integration",
    description: "Use Dyocense in your custom AI applications. For developers building advanced automation workflows.",
    provider: "LangChain",
    icon: Plug,
    status: "Coming Soon",
    pricing: "Free",
    features: [
      "Build custom AI agents",
      "Create workflows",
      "Memory support",
      "Async execution",
      "Python & TypeScript support"
    ],
    documentation: "https://docs.dyocense.com/integrations/langchain",
  },
];

const CATEGORIES = [
  { id: "all", name: "All", icon: Package },
  { id: "Data Connector", name: "Data Connectors", icon: Database },
  { id: "MCP Tool", name: "MCP Tools", icon: Cpu },
  { id: "Archetype", name: "Business Templates", icon: Blocks },
  { id: "Solver", name: "Solvers", icon: Zap },
  { id: "Integration", name: "Integrations", icon: Plug },
];

export const MarketplacePage = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredItems = MARKETPLACE_ITEMS.filter(item => {
    const matchesSearch = 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.provider.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = selectedCategory === "all" || item.category === selectedCategory;
    const matchesStatus = statusFilter === "all" || item.status === statusFilter;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Available":
        return "bg-green-50 text-green-700 border-green-200";
      case "Beta":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "Coming Soon":
        return "bg-gray-50 text-gray-700 border-gray-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getPricingBadge = (pricing: string) => {
    switch (pricing) {
      case "Free":
        return "bg-green-50 text-green-700";
      case "Included":
        return "bg-blue-50 text-blue-700";
      case "Premium":
        return "bg-purple-50 text-purple-700";
      case "Enterprise":
        return "bg-orange-50 text-orange-700";
      default:
        return "bg-gray-50 text-gray-700";
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-white via-blue-50/40 to-blue-100/30">
      <BrandedHeader showNav={false} />

      <main className="flex-1 px-6 py-12">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto mb-16">
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition mb-6"
          >
            <ArrowLeft size={16} />
            Back to Home
          </button>

          <div className="text-center mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Business Solutions Marketplace
            </h1>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Connect your business data, choose from proven templates, and get AI-powered recommendations. Everything you need to make smarter business decisions.
            </p>
          </div>

          {/* Search */}
          <div className="max-w-2xl mx-auto mb-8">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search connectors, tools, templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-full border-2 border-gray-200 focus:border-primary focus:outline-none transition"
              />
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            {CATEGORIES.map((category) => {
              const Icon = category.icon;
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-4 py-2 rounded-full text-sm font-semibold transition inline-flex items-center gap-2 ${
                    selectedCategory === category.id
                      ? "bg-primary text-white"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  <Icon size={16} />
                  {category.name}
                </button>
              );
            })}
          </div>

          {/* Status Filter */}
          <div className="flex justify-center gap-2">
            {["all", "Available", "Beta", "Coming Soon"].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                  statusFilter === status
                    ? "bg-gray-900 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50 border border-gray-200"
                }`}
              >
                {status === "all" ? "All Status" : status}
              </button>
            ))}
          </div>
        </section>

        {/* Marketplace Grid */}
        <section className="max-w-7xl mx-auto">
          <div className="mb-6 text-sm text-gray-600">
            Showing {filteredItems.length} {filteredItems.length === 1 ? 'item' : 'items'}
          </div>

          {filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <Package size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No items found matching your criteria.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredItems.map((item) => {
                const Icon = item.icon;
                return (
                  <article
                    key={item.id}
                    className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition group"
                  >
                    {/* Header */}
                    <div className="p-6 border-b border-gray-100">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-blue-50">
                            <Icon size={24} className="text-primary" />
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary transition">
                              {item.name}
                            </h3>
                            <p className="text-xs text-gray-500">{item.provider}</p>
                          </div>
                        </div>
                        {item.popular && (
                          <span className="px-2 py-1 rounded-full bg-yellow-50 text-yellow-700 text-xs font-semibold">
                            Popular
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-gray-600 leading-relaxed mb-4">
                        {item.description}
                      </p>

                      <div className="flex flex-wrap gap-2 mb-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(item.status)}`}>
                          {item.status}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getPricingBadge(item.pricing)}`}>
                          {item.pricing}
                        </span>
                        {item.setupTime && (
                          <span className="px-2 py-1 rounded-full bg-gray-50 text-gray-700 text-xs font-semibold">
                            {item.setupTime} setup
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Features */}
                    <div className="p-6">
                      <h4 className="text-xs font-semibold text-gray-700 uppercase mb-3">Features</h4>
                      <ul className="space-y-2 mb-4">
                        {item.features.slice(0, 4).map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                            <CheckCircle2 size={14} className="text-green-600 mt-0.5 flex-shrink-0" />
                            {feature}
                          </li>
                        ))}
                      </ul>

                      {item.compatibleWith && (
                        <div className="mb-4">
                          <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">Compatible With</h4>
                          <div className="flex flex-wrap gap-1">
                            {item.compatibleWith.slice(0, 3).map((compat, idx) => (
                              <span key={idx} className="px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs">
                                {compat}
                              </span>
                            ))}
                            {item.compatibleWith.length > 3 && (
                              <span className="px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs">
                                +{item.compatibleWith.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2">
                        {item.status === "Available" || item.status === "Beta" ? (
                          <button
                            onClick={() => navigate("/home")}
                            className="flex-1 px-4 py-2 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-blue-700 transition"
                          >
                            {item.status === "Beta" ? "Join Beta" : "Install"}
                          </button>
                        ) : (
                          <button
                            disabled
                            className="flex-1 px-4 py-2 rounded-lg bg-gray-100 text-gray-400 text-sm font-semibold cursor-not-allowed"
                          >
                            Coming Soon
                          </button>
                        )}
                        {item.documentation && (
                          <button
                            onClick={() => window.open(item.documentation, "_blank")}
                            className="px-4 py-2 rounded-lg border border-gray-200 text-gray-700 text-sm font-semibold hover:border-primary hover:text-primary transition inline-flex items-center gap-1"
                          >
                            <ExternalLink size={14} />
                            Docs
                          </button>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* Call to Action */}
        <section className="max-w-4xl mx-auto mt-16 mb-8">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-3xl p-8 md:p-12 text-center text-white">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Need a Custom Integration?
            </h2>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              <p className="text-gray-600 mb-4">
              We can build custom connectors, business templates, or integrations for your specific needs. 
            </p> 
              Enterprise customers get priority development and dedicated support.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => navigate("/buy")}
                className="px-6 py-3 rounded-full bg-white text-primary font-semibold hover:shadow-lg transition"
              >
                Contact Sales
              </button>
              <button
                onClick={() => window.open("https://docs.dyocense.com/api", "_blank")}
                className="px-6 py-3 rounded-full border-2 border-white text-white font-semibold hover:bg-white hover:text-primary transition"
              >
                View API Docs
              </button>
            </div>
          </div>
        </section>
      </main>

      <BrandedFooter />
    </div>
  );
};
