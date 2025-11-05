import { ChangeEvent, useState } from "react";
import { ClipboardList } from "lucide-react";
import { CSVUpload } from "./CSVUpload";

export type DataInputKey = "demand" | "holding_cost" | string;

interface DataIngestionPanelProps {
  value: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
}

const DATASETS: { key: DataInputKey; label: string; helper: string }[] = [
  {
    key: "demand",
    label: "Sales or demand data",
    helper: "Shows expected sales for each product",
  },
  {
    key: "holding_cost",
    label: "Storage costs",
    helper: "Cost to keep each product in stock",
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
          <h3 className="text-sm font-semibold text-gray-800">Upload Your Data</h3>
          <p className="text-xs text-gray-500">Add your sales data to get personalized recommendations</p>
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

      <CSVUpload
        title={`Upload ${DATASETS.find((d) => d.key === selectedDataset)?.label}`}
        description={DATASETS.find((d) => d.key === selectedDataset)?.helper || "Drag and drop your CSV file here"}
        onFileSelect={(file, preview) => {
          onChange({ ...value, [selectedDataset]: preview });
          setError(null);
        }}
      />

      {error && <p className="text-sm text-red-500">{error}</p>}
    </section>
  );
};
