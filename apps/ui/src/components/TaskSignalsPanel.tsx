import { useEffect, useState } from "react";
import { getTaskSignals } from "../lib/api";

interface TaskSignalsPanelProps {
    tenantId: string;
}

export default function TaskSignalsPanel({ tenantId }: TaskSignalsPanelProps) {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [signals, setSignals] = useState<any | null>(null);

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        getTaskSignals(tenantId)
            .then((res) => {
                if (!mounted) return;
                setSignals(res.signals);
                setError(null);
            })
            .catch((e) => {
                if (!mounted) return;
                setError((e as Error).message);
            })
            .finally(() => mounted && setLoading(false));
        return () => {
            mounted = false;
        };
    }, [tenantId]);

    const Stat = ({ label, value }: { label: string; value: any }) => (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
            <div className="text-xs text-gray-500 mb-1">{label}</div>
            <div className="text-xl font-semibold">{value ?? "—"}</div>
        </div>
    );

    if (loading) {
        return (
            <div className="space-y-2 animate-pulse">
                <div className="h-4 w-32 bg-gray-200 rounded" />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                        <div key={i} className="rounded-lg border bg-white p-4 shadow-sm">
                            <div className="h-3 w-20 bg-gray-200 rounded mb-2" />
                            <div className="h-6 w-12 bg-gray-200 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    if (error) return <div className="text-sm text-red-600">{error}</div>;

    return (
        <div className="space-y-2">
            <div className="font-semibold text-gray-800">Task signals</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Stat label="Recent Completed (7d)" value={signals?.recent_completed} />
                <Stat label="Prev Completed (7d)" value={signals?.previous_completed} />
                <Stat label="Completion Delta" value={signals?.completion_delta} />
                <Stat label="On-time % (30d)" value={signals?.adherence_on_time_pct != null ? `${signals.adherence_on_time_pct}%` : "—"} />
                <Stat label="On-time Count" value={signals?.on_time_count} />
                <Stat label="Late Count" value={signals?.late_count} />
                <Stat label="Overdue Open" value={signals?.overdue_open_count} />
                <Stat label="Window (days)" value={signals?.window_days} />
            </div>
            <p className="text-xs text-gray-500">Signals help the coach adapt pacing and tone. Improving trends will invite more ambitious steps; negative trends will invoke lighter tasks and recovery tactics.</p>
        </div>
    );
}
