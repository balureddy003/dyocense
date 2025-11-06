import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExecutionPanel } from "../components/ExecutionPanel";

describe("ExecutionPanel", () => {
  it("renders empty state when no stages provided", () => {
    render(<ExecutionPanel stages={[]} />);
    expect(screen.getByText("No execution plan yet")).toBeInTheDocument();
  });

  it("renders stages with todos", () => {
    const stages = [
      {
        id: "stage-1",
        title: "Stage 1: Setup",
        description: "Initial setup phase",
        todos: ["Todo 1", "Todo 2"],
      },
    ];
    render(<ExecutionPanel stages={stages} title="Test Plan" />);
    expect(screen.getByText("Test Plan")).toBeInTheDocument();
    expect(screen.getByText("Stage 1: Setup")).toBeInTheDocument();
  });
});
