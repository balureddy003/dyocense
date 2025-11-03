import { Activity } from "../hooks/useItinerary";
import { CheckCircle2 } from "lucide-react";

interface Props {
  title: string;
  description: string;
  activities: Activity[];
}

export const StageCard = ({ title, description, activities }: Props) => (
  <section className="bg-white rounded-xl shadow-card p-5 space-y-4">
    <header>
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-sm text-gray-600 mt-1">{description}</p>
    </header>
    <ul className="space-y-3">
      {activities.map((activity) => (
        <li key={activity.name} className="border border-gray-100 rounded-lg p-4 bg-gray-50">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={18} className="text-primary mt-1" />
            <div>
              <h4 className="font-medium text-gray-800">{activity.name}</h4>
              <p className="text-sm text-gray-600">{activity.description}</p>
              {activity.impact && (
                <p className="text-xs text-primary font-medium mt-2">Impact: {activity.impact}</p>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  </section>
);
