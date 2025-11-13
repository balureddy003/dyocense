import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SeasonalityInsightsPanel from "../components/SeasonalityInsightsPanel";

vi.mock("../lib/api", () => ({
    detectSeasonality: vi.fn(async (_tenantId: string, _metric: string, _freq?: string) => {
        return { result: { summary: "Weekly pattern detected", seasonality_period: 7, strength: 0.8 } };
    }),
}));

describe("SeasonalityInsightsPanel", () => {
    it("shows error when tenant not set", async () => {
        render(<SeasonalityInsightsPanel tenantId={null} />);
        const btn = screen.getByRole("button", { name: /detect/i });
        fireEvent.click(btn);
        expect(screen.getByText(/connect a tenant/i)).toBeInTheDocument();
    });

    it("calls detection and renders summary", async () => {
        render(<SeasonalityInsightsPanel tenantId="t-123" />);
        const buttons = screen.getAllByRole("button", { name: /detect/i });
        const btn = buttons[buttons.length - 1];
        fireEvent.click(btn);

        await waitFor(() => {
            expect(screen.getByText(/summary:/i)).toBeInTheDocument();
            const matches = screen.getAllByText(/weekly pattern detected/i);
            expect(matches.length).toBeGreaterThan(0);
        });
    });
});
