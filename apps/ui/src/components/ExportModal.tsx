import { useState } from "react";
import { Playbook } from "../hooks/usePlaybook";
import { X } from "lucide-react";

interface ExportModalProps {
  open: boolean;
  onClose: () => void;
  playbook: Playbook;
}

export const ExportModal = ({ open, onClose, playbook }: ExportModalProps) => {
  const [selection, setSelection] = useState<"excel" | "photos">("excel");
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-gray-900/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-5">
        <header className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Export playbook</h2>
            <p className="text-sm text-gray-500">Package actions for hand-off to stakeholders.</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </header>

        <div className="flex items-center gap-4 text-sm font-medium text-gray-700">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="export-type"
              value="excel"
              checked={selection === "excel"}
              onChange={() => setSelection("excel")}
            />
            Spreadsheet
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="export-type"
              value="photos"
              checked={selection === "photos"}
              onChange={() => setSelection("photos")}
            />
            Snapshot deck
          </label>
        </div>

        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 text-sm font-semibold text-gray-700">
            {playbook.title}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-gray-700">
              <thead className="bg-white">
                <tr className="border-b border-gray-200">
                  <th className="px-4 py-2 text-left">Stage</th>
                  <th className="px-4 py-2 text-left">Objective</th>
                  <th className="px-4 py-2 text-left">Key actions</th>
                  <th className="px-4 py-2 text-left">Owners / notes</th>
                </tr>
              </thead>
              <tbody>
                {playbook.itinerary.map((day) => (
                  <tr key={day.id} className="border-b border-gray-100">
                    <td className="px-4 py-2 text-gray-600">{day.date}</td>
                    <td className="px-4 py-2 text-gray-800 font-medium">{day.title}</td>
                    <td className="px-4 py-2 text-gray-600">
                      {day.entries.slice(0, 2).join("; ")}
                      {day.entries.length > 2 ? "…" : ""}
                    </td>
                    <td className="px-4 py-2 text-gray-400">Pending</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <footer className="flex justify-end gap-3">
          <button
            className="px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-600"
            onClick={onClose}
          >
            Cancel
          </button>
          <button className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-semibold">
            Download
          </button>
        </footer>
      </div>
    </div>
  );
};
