import { TripSummary } from "../hooks/useItinerary";
import { Lightbulb, Target } from "lucide-react";

export const SummaryPanel = ({ goal, summary }: { goal: string; summary: TripSummary }) => (
  <section className="bg-white rounded-xl shadow-card p-6 space-y-5">
    <header className="space-y-2">
      <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase">
        <Target size={18} /> Goal
      </div>
      <p className="text-gray-800 text-base leading-6">{goal}</p>
    </header>
    <div>
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Situation</h3>
      <p className="text-sm text-gray-600 mt-1 leading-6">{summary.context}</p>
    </div>
    <div className="grid gap-3 sm:grid-cols-3">
      {summary.primaryKpis.map((kpi) => (
        <div key={kpi.label} className="bg-blue-50 rounded-lg p-4 text-center">
          <div className="text-xs uppercase text-blue-700 tracking-wide">{kpi.label}</div>
          <div className="text-lg font-semibold text-blue-900 mt-1">{kpi.value}</div>
        </div>
      ))}
    </div>
    <div>
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
        <Lightbulb size={16} /> Quick wins
      </h3>
      <ul className="mt-2 space-y-2 text-sm text-gray-600">
        {summary.quickWins.map((item, idx) => (
          <li key={idx} className="flex gap-2">
            <span className="mt-1 inline-block h-2 w-2 rounded-full bg-primary"></span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  </section>
);
