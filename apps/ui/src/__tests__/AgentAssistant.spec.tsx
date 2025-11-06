import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgentAssistant } from "../components/AgentAssistant";

describe("AgentAssistant", () => {
  it("renders welcome message", () => {
    render(<AgentAssistant />);
    expect(screen.getByText(/intelligent AI business assistant/)).toBeInTheDocument();
  });

  it("renders set preferences button", () => {
    render(<AgentAssistant />);
    expect(screen.getAllByText(/Set Preferences/).length).toBeGreaterThan(0);
  });

  it("renders chat input with default placeholder", () => {
    render(<AgentAssistant />);
    // Check for the input element with the specific placeholder (modal is hidden so only 1 visible)
    const inputs = screen.getAllByPlaceholderText("Ask me anything about your goals...");
    expect(inputs.length).toBeGreaterThan(0);
    expect(inputs[0]).toBeInTheDocument();
  });

  it("renders data upload button with count", () => {
    render(<AgentAssistant />);
    // Check for the Data button text (there might be multiple svg elements with Data)
    const dataElements = screen.getAllByText(/Data/);
    expect(dataElements.length).toBeGreaterThan(0);
  });
});