import { useHistory } from "../hooks/useHistory";
import { X } from "lucide-react";

export const HistoryModal = ({ onClose }: { onClose: () => void }) => {
  const trips = useHistory();
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm relative">
        <button
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
          onClick={onClose}
          aria-label="Close history modal"
        >
          <X size={20} />
        </button>
        <h3 className="font-semibold text-lg mb-4">Recent plans</h3>
        <ul className="space-y-3 text-sm">
          {trips.map((trip) => (
            <li key={trip.id} className="border rounded-lg p-3 hover:border-primary transition">
              <div className="font-medium text-gray-800">{trip.title}</div>
              <div className="text-gray-500">{trip.dates}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
