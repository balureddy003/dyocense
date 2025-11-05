import { useMemo, useState } from "react";
import { Loader2, Workflow, Grid2x2 } from "lucide-react";
import { Playbook } from "../hooks/usePlaybook";
import { ItineraryDayCard } from "./ItineraryDayCard";
import { StageCard } from "./StageCard";

interface ItineraryColumnProps {
  playbook: Playbook;
  loading: boolean;
}

const OVERVIEW_TAB = "Overview";

export const ItineraryColumn = ({ playbook, loading }: ItineraryColumnProps) => {
  const [activeTab, setActiveTab] = useState<string>(OVERVIEW_TAB);
  const tabs = useMemo(
    () => [OVERVIEW_TAB, ...playbook.itinerary.map((_, idx) => `Stage ${idx + 1}`)],
    [playbook.itinerary]
  );

  const renderContent = () => {
    if (activeTab === OVERVIEW_TAB) {
      return (
        <div className="space-y-5">
          <div className="grid gap-4">
            {playbook.itinerary.map((day, idx) => (
              <ItineraryDayCard key={day.id} day={day} accentIndex={idx} />
            ))}
          </div>
         <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
           <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Run stages</h3>
           <div className="mt-4 space-y-4">
             {playbook.plan.map((stage, idx) => (
               <StageCard
                 key={stage.title}
                 title={stage.title}
                 description={stage.description}
                 activities={stage.activities}
                 accentColor={["#0ea5e9", "#f97316", "#22c55e"][idx % 3]}
               />
             ))}
           </div>
         </section>
          <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Scenario analysis</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {playbook.whatIfs.map((scenario) => (
                <article key={scenario.title} className="border border-gray-100 rounded-xl p-4 bg-gray-50 space-y-2">
                  <h4 className="text-sm font-semibold text-gray-900">{scenario.title}</h4>
                  <p className="text-xs text-gray-600 leading-5">{scenario.summary}</p>
                  {Object.keys(scenario.delta).length ? (
                    <dl className="text-xs text-gray-500 grid grid-cols-2 gap-2">
                      {Object.entries(scenario.delta).map(([label, value]) => (
                        <div key={label}>
                          <dt className="uppercase text-gray-400">{label.replace(/_/g, " ")}</dt>
                          <dd className="text-gray-700 font-semibold">{value}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-xs text-gray-400">No KPI deltas provided.</p>
                  )}
                </article>
              ))}
            </div>
          </section>
          <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Backlog actions</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              {playbook.unscheduled.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-gray-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>
          <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Follow-ups</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              {playbook.notes.map((note, idx) => (
                <li key={idx} className="border border-dashed border-gray-200 rounded-lg px-3 py-2 bg-gray-50">
                  {note}
                </li>
              ))}
            </ul>
          </section>
        </div>
      );
    }

    const stageIndex = tabs.indexOf(activeTab) - 1;
    const day = stageIndex >= 0 ? playbook.itinerary[stageIndex] : undefined;
    if (!day) return null;
    return (
      <div className="space-y-4">
        <ItineraryDayCard day={day} />
        <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Suggested actions</h3>
          <ul className="mt-3 space-y-2 text-sm text-gray-600">
            {day.entries.map((entry) => (
              <li key={entry} className="flex items-start gap-2">
                <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-gray-300" />
                <span>{entry}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    );
  };

  return (
    <main className="flex-1 min-w-0 overflow-y-auto px-6 py-6 space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Workflow size={18} /> Execution playbook
          </h2>
          <p className="text-xs text-gray-500">
            Last updated: {new Date().toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <button className="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <Grid2x2 size={16} /> Scenario compare
          </button>
        </div>
      </header>

      <nav className="flex items-center gap-4 overflow-x-auto text-sm border-b border-gray-200 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab ? "border-primary text-primary" : "border-transparent text-gray-500"
            }`}
          >
            {tab}
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 size={16} className="animate-spin" /> Fetching latest playbook…
        </div>
      ) : (
        renderContent()
      )}
    </main>
  );
};
