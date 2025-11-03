import { Activity } from "../hooks/usePlaybook";
import { CalendarDays, ChevronRight } from "lucide-react";

interface Props {
  title: string;
  description: string;
  activities: Activity[];
  accentColor?: string;
}

export const StageCard = ({ title, description, activities, accentColor = "#2563EB" }: Props) => (
  <article className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
    <header className="flex items-center justify-between gap-3 px-5 py-4 border-b border-gray-100">
      <div className="flex items-start gap-3">
        <span
          className="h-10 w-1.5 rounded-full flex-none"
          style={{ backgroundColor: accentColor }}
        />
        <div>
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
      <CalendarDays size={18} className="text-gray-400" />
    </header>
    <ul className="divide-y divide-gray-100">
      {activities.map((activity, index) => (
        <li key={activity.name} className="px-5 py-4 flex items-start gap-3">
          <div className="mt-1 h-2 w-2 rounded-full bg-gray-300" />
          <div className="flex-1">
            <div className="flex items-center justify-between gap-3">
              <h4 className="text-sm font-medium text-gray-800">{activity.name}</h4>
              <ChevronRight size={16} className="text-gray-300" />
            </div>
            <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
            {activity.impact && (
              <p className="text-xs text-primary font-medium mt-2">Impact: {activity.impact}</p>
            )}
          </div>
          <span className="text-xs text-gray-400 font-semibold mt-1">#{index + 1}</span>
        </li>
      ))}
    </ul>
  </article>
);
