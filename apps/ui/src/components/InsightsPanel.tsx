import { Playbook } from "../hooks/usePlaybook";
import { BookOpen, Clock, FileText, Lightbulb, TrendingUp } from "lucide-react";
import { ForecastChart } from "./ForecastChart";

interface InsightsPanelProps {
  playbook: Playbook;
}

// Sample forecast data - in production, this would come from the playbook
const sampleForecastData = [
  { week: "Week 1", predicted: 120, low: 100, high: 140 },
  { week: "Week 2", predicted: 135, low: 115, high: 155 },
  { week: "Week 3", predicted: 145, low: 125, high: 165 },
  { week: "Week 4", predicted: 150, low: 130, high: 170 },
];

export const InsightsPanel = ({ playbook }: InsightsPanelProps) => {
  return (
    <aside className="hidden lg:flex lg:w-[340px] xl:w-[380px] flex-col border-l bg-white">
      {/* Key Recommendations Section */}
      <section className="px-5 py-4 border-b bg-gradient-to-br from-blue-50 to-white">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Lightbulb size={18} className="text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-gray-900">
            Your Recommendations
          </h3>
        </div>
        <div className="space-y-3">
          <div className="bg-white rounded-xl border border-blue-100 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-primary">ORDER NOW</span>
              <span className="text-sm font-bold text-gray-900">240 units</span>
            </div>
            <p className="text-xs text-gray-600">
              Recommended quantity to order this week
            </p>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-green-700">COST SAVINGS</span>
              <span className="text-sm font-bold text-gray-900">$1,240</span>
            </div>
            <p className="text-xs text-gray-600">
              Estimated monthly savings vs. current approach
            </p>
          </div>
          <div className="bg-white rounded-xl border border-orange-100 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-orange-700">STOCK RISK</span>
              <span className="text-sm font-bold text-gray-900">Low</span>
            </div>
            <p className="text-xs text-gray-600">
              Chance of running out before next order
            </p>
          </div>
        </div>
      </section>

      {/* Forecast Section */}
      <section className="px-5 py-4 border-b overflow-x-hidden">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp size={16} className="text-primary" />
          <h3 className="text-sm font-semibold text-gray-900">
            Sales Prediction
          </h3>
        </div>
        <ForecastChart data={sampleForecastData} title="" unit="units" />
      </section>

      {/* Supporting Documents */}
      <section className="px-5 py-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <FileText size={16} className="text-primary" />
            Supporting Documents
          </h3>
          <span className="text-xs text-gray-500">{playbook.evidence.length}</span>
        </div>
        <ul className="space-y-2 text-sm text-gray-700">
          {playbook.evidence.map((item) => (
            <li key={item.id} className="rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-medium text-gray-900 text-xs">{item.name}</div>
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">{item.summary}</p>
                </div>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600 whitespace-nowrap">
                  {item.type}
                </span>
              </div>
              {item.link && (
                <a
                  href={item.link}
                  className="text-xs text-primary font-medium mt-2 inline-block hover:underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  View file →
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Activity Timeline */}
      <section className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
          <Clock size={16} className="text-primary" />
          Recent Activity
        </h3>
        <ol className="space-y-3 text-sm text-gray-600">
          {playbook.history.map((entry) => (
            <li key={entry.timestamp} className="border-l-2 border-primary/40 pl-3 pb-2">
              <p className="text-xs text-gray-500 flex items-center gap-2">
                <BookOpen size={12} className="text-primary" />
                {new Date(entry.timestamp).toLocaleTimeString(undefined, {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-xs text-gray-800 mt-1 font-medium">{entry.event}</p>
              <p className="text-xs text-gray-500 mt-0.5">{entry.author}</p>
            </li>
          ))}
        </ol>
      </section>
    </aside>
  );
};
