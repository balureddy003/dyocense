import { useState } from "react";
import { useItinerary } from "../hooks/useItinerary";
import { SummaryPanel } from "./SummaryPanel";
import { StageCard } from "./StageCard";
import { WhatIfPanel } from "./WhatIfPanel";
import { NotesPanel } from "./NotesPanel";
import { Loader2 } from "lucide-react";

const TABS = ["Goal", "Plan", "What-if", "Notes"] as const;

type Tab = (typeof TABS)[number];

export const ItineraryTabs = () => {
  const { trip, loading } = useItinerary();
  const [activeTab, setActiveTab] = useState<Tab>("Goal");

  return (
    <section className="flex-1 flex flex-col overflow-hidden">
      <div className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 lg:px-8">
          <ul className="flex flex-wrap gap-4">
            {TABS.map((tab) => (
              <li key={tab}>
                <button
                  className={`py-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab
                      ? "border-primary text-primary"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-bg">
        <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6 space-y-6">
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Loader2 className="animate-spin" size={16} /> Fetching latest plan...
            </div>
          )}

          {activeTab === "Goal" && <SummaryPanel goal={trip.goal} summary={trip.summary} />}

          {activeTab === "Plan" && (
            <div className="space-y-5">
              {trip.plan.map((stage) => (
                <StageCard
                  key={stage.title}
                  title={stage.title}
                  description={stage.description}
                  activities={stage.activities}
                />
              ))}
              <section className="bg-white rounded-xl shadow-card p-5">
                <h3 className="text-lg font-semibold text-gray-900">Additional ideas</h3>
                <ul className="mt-3 space-y-2 text-sm text-gray-600">
                  {trip.unscheduled.map((item) => (
                    <li key={item} className="border border-dashed border-gray-200 rounded-lg p-3">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          )}

          {activeTab === "What-if" && <WhatIfPanel scenarios={trip.whatIfs} />}

          {activeTab === "Notes" && <NotesPanel notes={trip.notes} />}
        </div>
      </div>
    </section>
  );
};
