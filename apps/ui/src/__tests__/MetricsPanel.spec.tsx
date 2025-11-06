import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricsPanel } from "../components/MetricsPanel";

describe("MetricsPanel", () => {
  it("renders header and default KPIs", () => {
    render(<MetricsPanel />);
    expect(screen.getByText("Impact & Results")).toBeInTheDocument();
    expect(screen.getByText("Before vs. After")).toBeInTheDocument();
    expect(screen.getByText("Operating Cost")).toBeInTheDocument();
  });

  it("renders quick wins when provided", () => {
    const quickWins = ["Quick win 1", "Quick win 2"];
    render(<MetricsPanel quickWins={quickWins} />);
    expect(screen.getByText("Quick win 1")).toBeInTheDocument();
    expect(screen.getByText("Quick win 2")).toBeInTheDocument();
  });

  it("renders evidence cards", () => {
    render(<MetricsPanel />);
    expect(screen.getAllByText("Evidence & Validation").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Demand Forecasting Accuracy").length).toBeGreaterThan(0);
  });
});
