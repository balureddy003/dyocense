import { PlaybookStage } from "../hooks/usePlaybook";
import { Workflow, ClipboardList } from "lucide-react";

interface ItineraryDayCardProps {
  day: PlaybookStage;
  accentIndex?: number;
}

const COLORS = ["#22c55e", "#2563eb", "#f97316", "#7c3aed", "#0ea5e9"]; // rotate accents

export const ItineraryDayCard = ({ day, accentIndex = 0 }: ItineraryDayCardProps) => {
  const accent = COLORS[accentIndex % COLORS.length];
  return (
    <article className="rounded-2xl border border-gray-100 bg-white shadow-sm p-4">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="mt-1 h-2.5 w-2.5 rounded-full" style={{ backgroundColor: accent }} />
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 flex items-center gap-2">
              <Workflow size={14} /> {day.date}
            </p>
            <h3 className="text-base font-semibold text-gray-900 mt-1">{day.title}</h3>
          </div>
        </div>
        <ClipboardList size={18} className="text-gray-300" />
      </header>
      <ul className="mt-3 space-y-2 text-sm text-gray-600">
        {day.entries.map((entry) => (
          <li key={entry} className="flex items-start gap-2">
            <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-gray-300" />
            <span>{entry}</span>
          </li>
        ))}
      </ul>
    </article>
  );
};
