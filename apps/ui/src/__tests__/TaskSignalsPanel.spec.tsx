import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import TaskSignalsPanel from "../components/TaskSignalsPanel";

vi.mock("../lib/api", () => ({
    getTaskSignals: vi.fn(async (_tenantId: string) => ({
        tenant_id: _tenantId,
        signals: {
            recent_completed: 12,
            previous_completed: 9,
            completion_delta: 3,
            adherence_on_time_pct: 75,
            on_time_count: 15,
            late_count: 5,
            overdue_open_count: 2,
            window_days: 7,
        },
    })),
}));

describe("TaskSignalsPanel", () => {
    it("renders stats from API", async () => {
        render(<TaskSignalsPanel tenantId="t-abc" />);

        await waitFor(() => {
            expect(screen.getByText("Task signals")).toBeInTheDocument();
            expect(screen.getByText("12")).toBeInTheDocument();
            expect(screen.getByText("3")).toBeInTheDocument();
            expect(screen.getByText("75%"));
        });
    });
});
