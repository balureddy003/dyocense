import { CheckCircle2, Package, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { HierarchyBreadcrumb } from "./HierarchyBreadcrumb";

type KPI = {
  id: string;
  label: string;
  before: string;
  after: string;
  improvement: string;
  positive: boolean;
};

type Evidence = {
  id: string;
  title: string;
  description: string;
  impact: string;
};

export type MetricsPanelProps = {
  kpis?: KPI[];
  evidence?: Evidence[];
  quickWins?: string[];
  tenantName?: string;
  projectName?: string;
};

const DEFAULT_KPIS: KPI[] = [
  {
    id: "cost",
    label: "Operating Cost",
    before: "$42,000/mo",
    after: "$34,500/mo",
    improvement: "-18%",
    positive: true,
  },
  {
    id: "stock",
    label: "Stock Accuracy",
    before: "73%",
    after: "94%",
    improvement: "+29%",
    positive: true,
  },
  {
    id: "waste",
    label: "Waste/Spoilage",
    before: "$8,200/mo",
    after: "$2,900/mo",
    improvement: "-65%",
    positive: true,
  },
  {
    id: "service",
    label: "Stockout Incidents",
    before: "12/month",
    after: "2/month",
    improvement: "-83%",
    positive: true,
  },
];

const DEFAULT_EVIDENCE: Evidence[] = [
  {
    id: "e1",
    title: "Demand Forecasting Accuracy",
    description: "ML model improved ordering precision by analyzing 18 months of sales history",
    impact: "Reduced over-ordering by 42%",
  },
  {
    id: "e2",
    title: "Supplier Consolidation",
    description: "Negotiated volume discounts with top 3 suppliers by consolidating orders",
    impact: "Saved $1,200/month on procurement",
  },
  {
    id: "e3",
    title: "Automated Reordering",
    description: "Implemented smart reorder points based on lead time and daily usage",
    impact: "Eliminated 89% of stockouts",
  },
];

export function MetricsPanel({ kpis = DEFAULT_KPIS, evidence = DEFAULT_EVIDENCE, quickWins, tenantName, projectName }: MetricsPanelProps) {
  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-white">
      {/* Header */}
      <header className="border-b bg-gradient-to-b from-green-50/40 to-white px-4 py-2.5 flex-shrink-0">
        <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-green-700">
          <TrendingUp size={14} /> Impact & Results
        </div>
        <h2 className="text-base font-semibold text-gray-900">Before vs. After</h2>
        <p className="text-xs leading-relaxed text-gray-600">Track improvements and validate with data-backed evidence</p>
        {(tenantName || projectName) && (
          <div className="mt-2 inline-flex items-center gap-2 text-xs text-gray-600 bg-white px-2 py-1 rounded border border-gray-200">
            <HierarchyBreadcrumb tenantName={tenantName} projectName={projectName} className="inline-flex items-center gap-2" />
          </div>
        )}
      </header>

      {/* Quick Wins */}
      {quickWins && quickWins.length > 0 && (
        <section className="border-b px-5 py-4">
          <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <Zap size={14} className="text-amber-500" /> Quick Wins
          </div>
          <div className="space-y-2">
            {quickWins.map((win, idx) => (
              <div key={idx} className="flex items-start gap-2 rounded-lg border border-green-100 bg-green-50/50 px-3 py-2 text-xs text-gray-700">
                <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-green-600" />
                {win}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* KPI Cards */}
      <section className="space-y-4 overflow-y-auto px-5 pb-5 pt-5">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Key Metrics</div>
        {kpis.map((kpi) => (
          <div key={kpi.id} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 bg-gray-50 px-4 py-2.5">
              <div className="text-sm font-semibold text-gray-900">{kpi.label}</div>
            </div>
            <div className="px-4 py-3">
              <div className="mb-3 grid grid-cols-2 gap-3">
                <div>
                  <div className="mb-1 text-xs text-gray-500">Before</div>
                  <div className="text-lg font-semibold text-gray-700">{kpi.before}</div>
                </div>
                <div>
                  <div className="mb-1 text-xs text-gray-500">After</div>
                  <div className="text-lg font-semibold text-green-700">{kpi.after}</div>
                </div>
              </div>
              <div
                className={`flex items-center justify-center gap-1 rounded-lg px-3 py-2 text-sm font-semibold ${kpi.positive ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                  }`}
              >
                {kpi.positive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {kpi.improvement}
              </div>
            </div>
          </div>
        ))}

        {/* Evidence Section */}
        <div className="mb-2 mt-6 text-xs font-semibold uppercase tracking-wide text-gray-500">Evidence & Validation</div>
        {evidence.map((item) => (
          <div key={item.id} className="rounded-xl border border-gray-200 bg-gradient-to-br from-blue-50/30 to-white p-4 shadow-sm">
            <div className="mb-2 flex items-start gap-2">
              <div className="rounded-lg bg-primary/10 p-2">
                <Package size={16} className="text-primary" />
              </div>
              <div className="flex-1">
                <h4 className="mb-1 text-sm font-semibold text-gray-900">{item.title}</h4>
                <p className="mb-2 text-xs leading-relaxed text-gray-600">{item.description}</p>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                  <CheckCircle2 size={12} />
                  {item.impact}
                </div>
              </div>
            </div>
          </div>
        ))}
      </section>
    </aside>
  );
}
