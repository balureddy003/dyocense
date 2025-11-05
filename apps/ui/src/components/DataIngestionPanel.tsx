import { ChangeEvent, useState } from "react";
import { UploadCloud, FileSpreadsheet, ClipboardList } from "lucide-react";

export type DataInputKey = "demand" | "holding_cost" | string;

interface DataIngestionPanelProps {
  value: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
}

const DATASETS: { key: DataInputKey; label: string; helper: string }[] = [
  {
    key: "demand",
    label: "Demand signal",
    helper: "sku, quantity columns expected",
  },
  {
    key: "holding_cost",
    label: "Holding cost",
    helper: "sku, cost columns expected",
  },
];

const parseCsv = (text: string) => {
  const [headerLine, ...rows] = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!headerLine) return [];
  const headers = headerLine.split(",").map((h) => h.trim());
  return rows.map((row) => {
    const columns = row.split(",");
    return headers.reduce<Record<string, string>>((acc, header, index) => {
      acc[header] = columns[index]?.trim() ?? "";
      return acc;
    }, {});
  });
};

export const DataIngestionPanel = ({ value, onChange }: DataIngestionPanelProps) => {
  const [selectedDataset, setSelectedDataset] = useState<DataInputKey>(DATASETS[0].key);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const records = parseCsv(text);
      onChange({ ...value, [selectedDataset]: records });
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to read CSV");
    }
  };

  return (
    <section className="border border-gray-100 rounded-2xl p-5 space-y-4">
      <header className="flex items-center gap-2">
        <ClipboardList size={18} className="text-primary" />
        <div>
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Data inputs</h3>
          <p className="text-sm text-gray-500">Upload CSVs or paste JSON to override sample data.</p>
        </div>
      </header>

      <div className="flex flex-wrap gap-2 text-sm">
        {DATASETS.map((dataset) => (
          <button
            key={dataset.key}
            className={`px-3 py-1.5 rounded-full border transition ${
              selectedDataset === dataset.key
                ? "border-primary bg-blue-50 text-primary"
                : "border-gray-200 text-gray-600 hover:border-primary"
            }`}
            onClick={() => setSelectedDataset(dataset.key)}
          >
            {dataset.label}
          </button>
        ))}
      </div>

      <label className="flex flex-col gap-2 text-sm text-gray-700">
        Upload CSV
        <div className="flex items-center gap-3">
          <label className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-gray-300 text-gray-600 cursor-pointer hover:border-primary">
            <UploadCloud size={16} />
            <span>Select file</span>
            <input type="file" accept=".csv" className="hidden" onChange={handleFile} />
          </label>
          <span className="text-xs text-gray-500">
            {DATASETS.find((d) => d.key === selectedDataset)?.helper}
          </span>
        </div>
      </label>

      <label className="flex flex-col gap-2 text-sm text-gray-700">
        Or paste JSON
        <textarea
          className="w-full min-h-[120px] rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary focus:ring-2 focus:ring-primary/10"
          placeholder='[{"sku":"widget","quantity":120}]'
          onBlur={(event) => {
            if (!event.target.value.trim()) return;
            try {
              const parsed = JSON.parse(event.target.value);
              onChange({ ...value, [selectedDataset]: parsed });
              setError(null);
            } catch (err: any) {
              setError("Invalid JSON");
            }
          }}
        />
      </label>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 text-xs text-gray-600 space-y-1">
        <p className="font-semibold text-gray-700 flex items-center gap-2">
          <FileSpreadsheet size={14} className="text-primary" /> Current {selectedDataset}
        </p>
        <pre className="whitespace-pre-wrap break-words text-xs max-h-32 overflow-auto">
          {JSON.stringify(value[selectedDataset] ?? [], null, 2)}
        </pre>
      </div>
    </section>
  );
};
