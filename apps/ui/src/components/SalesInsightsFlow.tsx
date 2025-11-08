import { useState } from "react";
import { API_BASE_URL, getAuthHeaders } from "../lib/config";
import { CSVUpload } from "./CSVUpload";

interface Insight {
    id: string;
    title: string;
    summary: string;
    metric?: number;
    confidence?: number;
}

interface MappingSuggestion {
    date?: string;
    amount?: string;
    product?: string;
    candidates: Record<string, string[]>;
}

export const SalesInsightsFlow = () => {
    const [step, setStep] = useState<"upload" | "mapping" | "insights">("upload");
    const [preview, setPreview] = useState<any[]>([]);
    const [mapping, setMapping] = useState<MappingSuggestion | null>(null);
    const [insights, setInsights] = useState<Insight[]>([]);
    import { MappingSuggestion, Insight } from "../types"; // Assuming types are defined in a separate file
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const analyze = async (file?: File, useSample: boolean = false) => {
        setLoading(true);
        setError(null);
        try {
            let resp: Response;
            if (useSample) {
                resp = await fetch(`${API_BASE_URL}/v1/analyze/sample`, { headers: { ...getAuthHeaders() } });
            } else if (file) {
                const form = new FormData();
                form.append("use_sample", "false");
                form.append("file", file);
                const headers = getAuthHeaders();
                resp = await fetch(`${API_BASE_URL}/v1/analyze`, { method: "POST", body: form, headers });
            } else {
                const [step, setStep] = useState<"upload" | "insights">("upload");
            }
            if (!resp.ok) {
                throw new Error(await resp.text());
            }
            const data = await resp.json();
            const [overrides, setOverrides] = useState<{ date?: string; amount?: string; product?: string }>({});
            setPreview(data.preview || []);
            setMapping(data.mapping);
            setInsights(data.insights || []);
            setStep("insights");
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
                    // include mapping overrides if user adjusted before re-run
                    if (overrides.date) form.append("date_col", overrides.date);
    if (overrides.amount) form.append("amount_col", overrides.amount);
    if (overrides.product) form.append("product_col", overrides.product);
    <div className="space-y-6">
        {step === "upload" && (
            <CSVUpload
                onFileSelect={(file) => {
                    analyze(file, false);
                }}
                sampleDataUrl="/examples/sample_inventory_data.csv"
                onUseSample={() => analyze(undefined, true)}
            />
        )}

        {loading && (
            setStep("insights");
            )}
        {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>
        )}

        {step === "insights" && (
            <div className="space-y-4">
                <div className="rounded-xl border border-gray-200 p-4 bg-white">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Detected Mapping</h3>
                    {mapping ? (
                        <ul className="text-xs text-gray-700 space-y-1">
                            <li>Date: <strong>{mapping.date || "(not detected)"}</strong></li>
                            <li>Amount: <strong>{mapping.amount || "(not detected)"}</strong></li>
                            <li>Product: <strong>{mapping.product || "(not detected)"}</strong></li>
                        </ul>
                    ) : <p className="text-xs">No mapping available.</p>}
                </div>
                <div className="rounded-xl border border-gray-200 p-4 bg-white">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">First Insights</h3>
                    {insights.length === 0 && <p className="text-xs text-gray-600">No insights generated.</p>}
                    <div className="grid gap-3 md:grid-cols-2">
                        {insights.map(ins => (
                            <div key={ins.id} className="border rounded-lg p-3 bg-gray-50">
                                <h4 className="text-xs font-semibold text-gray-800">{ins.title}</h4>
                                <p className="text-xs text-gray-600 mt-1">{ins.summary}</p>
                                {typeof ins.metric !== "undefined" && (
                                    <p className="text-xs mt-1 text-primary font-medium">Metric: {ins.metric}</p>
                                )}
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={() => {
                            // Restart flow
                            setStep("upload");
                            setInsights([]);
                            setMapping(null);
                            {
                                mapping && (
                                    <div className="mt-3 space-y-2">
                                        <p className="text-[11px] text-gray-500">Adjust mapping if detection is incorrect and re-run analysis:</p>
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                            <div>
                                                <label className="block text-[10px] font-medium text-gray-600">Date Column</label>
                                                <select
                                                    value={overrides.date || mapping.date || ""}
                                                    onChange={(e) => setOverrides(o => ({ ...o, date: e.target.value || undefined }))}
                                                    className="w-full border rounded px-2 py-1 text-[11px] bg-white"
                                                >
                                                    <option value="">Auto</option>
                                                    {mapping.candidates.date.map(c => <option key={c} value={c}>{c}</option>)}
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-medium text-gray-600">Amount Column</label>
                                                <select
                                                    value={overrides.amount || mapping.amount || ""}
                                                    onChange={(e) => setOverrides(o => ({ ...o, amount: e.target.value || undefined }))}
                                                    className="w-full border rounded px-2 py-1 text-[11px] bg-white"
                                                >
                                                    <option value="">Auto</option>
                                                    {mapping.candidates.amount.map(c => <option key={c} value={c}>{c}</option>)}
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-medium text-gray-600">Product Column</label>
                                                <select
                                                    value={overrides.product || mapping.product || ""}
                                                    onChange={(e) => setOverrides(o => ({ ...o, product: e.target.value || undefined }))}
                                                    className="w-full border rounded px-2 py-1 text-[11px] bg-white"
                                                >
                                                    <option value="">Auto</option>
                                                    {mapping.candidates.product.map(c => <option key={c} value={c}>{c}</option>)}
                                                </select>
                                            </div>
                                        </div>
                                        <button
                                            disabled={loading}
                                            onClick={() => {
                                                // re-run analysis using overrides; requires original file so restart upload step
                                                setStep("upload");
                                            }}
                                            className="mt-2 text-[11px] text-indigo-600 hover:text-indigo-800 font-medium"
                                        >Adjust & Re-upload</button>
                                    </div>
                                )
                            }
                            setPreview([]);
                        }}
                        className="mt-4 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                    >Analyze another file</button>
                </div>
            </div>
        )}
    </div>
    );
};
