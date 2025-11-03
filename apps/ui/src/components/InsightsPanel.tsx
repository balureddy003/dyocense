import { Playbook } from "../hooks/usePlaybook";
import { BookOpen, Clock, FileText, Layers3 } from "lucide-react";

interface InsightsPanelProps {
  playbook: Playbook;
}

export const InsightsPanel = ({ playbook }: InsightsPanelProps) => {
  return (
    <aside className="hidden lg:flex lg:w-[320px] xl:w-[340px] flex-col border-l bg-white">
      <section className="px-5 py-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Layers3 size={16} /> Evidence
          </h3>
          <span className="text-xs text-gray-400">{playbook.evidence.length} items</span>
        </div>
        <ul className="mt-3 space-y-3 text-sm text-gray-700">
          {playbook.evidence.map((item) => (
            <li key={item.id} className="rounded-xl border border-gray-100 p-3 bg-gray-50">
              <div className="flex items-center justify-between gap-2">
                <div className="font-medium text-gray-900 flex items-center gap-2">
                  <FileText size={16} className="text-primary" /> {item.name}
                </div>
                <span className="text-xs uppercase text-gray-400">{item.type}</span>
              </div>
              <p className="text-xs text-gray-600 mt-1 leading-5">{item.summary}</p>
              {item.link && (
                <a
                  href={item.link}
                  className="text-xs text-primary font-medium mt-2 inline-block"
                  target="_blank"
                  rel="noreferrer"
                >
                  View artifact
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide flex items-center gap-2">
          <Clock size={16} /> History
        </h3>
        <ol className="space-y-4 text-sm text-gray-600">
          {playbook.history.map((entry) => (
            <li key={entry.timestamp} className="border-l-2 border-primary/40 pl-3">
              <p className="text-xs uppercase text-gray-400 flex items-center gap-2">
                <BookOpen size={14} className="text-primary" />
                {new Date(entry.timestamp).toLocaleTimeString(undefined, {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-sm text-gray-800 mt-1">{entry.event}</p>
              <p className="text-xs text-gray-400 mt-1">{entry.author}</p>
            </li>
          ))}
        </ol>
      </section>
    </aside>
  );
};
