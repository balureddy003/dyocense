import { Clipboard, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { detectSeasonality } from "../lib/api";

type Metric = "revenue" | "health_score";
type FreqHint = "H" | "D" | "W" | "";

interface SeasonalityInsightsPanelProps {
    tenantId: string | null | undefined;
    defaultMetric?: Metric;
    defaultFreqHint?: FreqHint;
}

export default function SeasonalityInsightsPanel({ tenantId, defaultMetric = "revenue", defaultFreqHint = "" }: SeasonalityInsightsPanelProps) {
    // Restore last selections from localStorage per-tenant
    const loadInitialMetric = (): Metric => {
        try {
            const key = tenantId ? `dyocense-seasonality-${tenantId}-metric` : null;
            const val = key ? localStorage.getItem(key) : null;
            if (val === "revenue" || val === "health_score") return val;
        } catch { }
        return defaultMetric;
    };
    const loadInitialFreq = (): FreqHint => {
        try {
            const key = tenantId ? `dyocense-seasonality-${tenantId}-freq` : null;
            const val = key ? localStorage.getItem(key) : null;
            if (val === "H" || val === "D" || val === "W" || val === "") return val as FreqHint;
        } catch { }
        return defaultFreqHint;
    };

    const [metric, setMetric] = useState<Metric>(loadInitialMetric);
    const [freqHint, setFreqHint] = useState<FreqHint>(loadInitialFreq);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<any | null>(null);
    const [lastRunAt, setLastRunAt] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        try {
            if (tenantId) localStorage.setItem(`dyocense-seasonality-${tenantId}-metric`, metric);
        } catch { }
    }, [tenantId, metric]);

    useEffect(() => {
        try {
            if (tenantId) localStorage.setItem(`dyocense-seasonality-${tenantId}-freq`, freqHint);
        } catch { }
    }, [tenantId, freqHint]);

    const runDetection = async () => {
        if (!tenantId) {
            setError("Tenant not set");
            return;
        }
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await detectSeasonality(tenantId, metric, freqHint || undefined);
            setResult(res);
            setLastRunAt(new Date().toLocaleString());
        } catch (e: any) {
            const msg = e?.message || "Failed to detect seasonality";
            const hint = /404|not found|disabled/i.test(msg) ? " (feature may be disabled)" : "";
            setError(`${msg}${hint}`);
        } finally {
            setLoading(false);
        }
    };

    // Try to extract a human-friendly summary if present
    const summary = (() => {
        const r = result || {};
        const out = r.result || r.data || r;
        const parts: string[] = [];
        if (out.summary) parts.push(String(out.summary));
        if (out.seasonality_period) parts.push(`Period: ${out.seasonality_period}`);
        if (out.freq || out.frequency) parts.push(`Freq: ${out.freq || out.frequency}`);
        if (out.strength != null) parts.push(`Strength: ${out.strength}`);
        return parts.length ? parts.join(" · ") : null;
    })();

    return (
        <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
            <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div>
                    <h3 className="text-sm font-semibold text-gray-800">Seasonality insights</h3>
                    <p className="text-xs text-gray-500 mt-0.5">Detect recurring patterns to guide pacing and planning</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        className="px-2 py-1 text-xs border border-gray-300 rounded"
                        value={metric}
                        onChange={(e) => setMetric(e.target.value as Metric)}
                        disabled={loading}
                    >
                        <option value="revenue">Revenue</option>
                        <option value="health_score">Health Score</option>
                    </select>
                    <select
                        className="px-2 py-1 text-xs border border-gray-300 rounded"
                        value={freqHint}
                        onChange={(e) => setFreqHint(e.target.value as FreqHint)}
                        disabled={loading}
                    >
                        <option value="">Auto</option>
                        <option value="H">Hourly</option>
                        <option value="D">Daily</option>
                        <option value="W">Weekly</option>
                    </select>
                    <button
                        onClick={runDetection}
                        disabled={loading || !tenantId}
                        className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                    >
                        {loading ? (<><Loader2 className="h-3 w-3 animate-spin" /> Analyzing…</>) : "Detect"}
                    </button>
                </div>
            </header>

            <div className="px-4 py-3 space-y-3">
                {!tenantId && (
                    <div className="text-xs text-gray-500">Connect a tenant to analyze seasonality.</div>
                )}
                {error && (
                    <div className="text-xs text-red-600">{error}</div>
                )}
                {summary && (
                    <div className="text-xs text-gray-700">
                        <span className="font-semibold">Summary:</span> {summary}
                    </div>
                )}
                {result && (
                    <details className="rounded border border-gray-100 bg-gray-50 p-3">
                        <summary className="text-xs text-gray-600 cursor-pointer flex items-center justify-between">
                            <span>Raw result</span>
                            <button
                                type="button"
                                className="inline-flex items-center gap-1 rounded border border-gray-300 bg-white px-2 py-0.5 text-[10px] text-gray-700 hover:bg-gray-100"
                                onClick={async (e) => {
                                    e.preventDefault();
                                    try {
                                        await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
                                        setCopied(true);
                                        setTimeout(() => setCopied(false), 1200);
                                    } catch { }
                                }}
                            >
                                <Clipboard className="h-3 w-3" /> {copied ? "Copied" : "Copy"}
                            </button>
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto text-[10px] leading-4 text-gray-700">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </details>
                )}
                {lastRunAt && (
                    <div className="text-[10px] text-gray-400">Last run: {lastRunAt}</div>
                )}
            </div>
        </section>
    );
}
