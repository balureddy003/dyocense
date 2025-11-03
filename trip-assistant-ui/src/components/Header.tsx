import { useState } from "react";
import { HistoryModal } from "./HistoryModal";
import { Clock3, Compass, History, UserCircle, Workflow } from "lucide-react";

export const Header = () => {
  const [showHistory, setShowHistory] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-primary font-semibold">
          <Compass size={20} /> Dyocense Trip Planner
        </div>
        <nav className="hidden md:flex items-center gap-5 text-gray-600">
          <button className="flex items-center gap-1" onClick={() => setShowHistory(true)}>
            <History size={16} /> Previous plans
          </button>
          <button className="flex items-center gap-1">
            <Workflow size={16} /> Explore archetypes
          </button>
          <button className="flex items-center gap-1">
            <Clock3 size={16} /> Schedule refresh
          </button>
        </nav>
        <UserCircle size={26} className="text-gray-500" />
      </div>
      {showHistory && <HistoryModal onClose={() => setShowHistory(false)} />}
    </header>
  );
};
