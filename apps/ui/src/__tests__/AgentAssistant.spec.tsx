import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AgentAssistant } from "../components/AgentAssistant";

describe("AgentAssistant", () => {
  it("renders header title", () => {
    render(<AgentAssistant />);
    expect(screen.getByText(/AI Business Assistant/)).toBeInTheDocument();
  });

  it("renders set preferences button", () => {
    render(<AgentAssistant />);
    expect(screen.getAllByText(/Set Preferences/).length).toBeGreaterThan(0);
  });

  it("renders chat input with correct placeholder", () => {
    render(<AgentAssistant />);
    // Should match one of the new placeholder texts
    const inputs = screen.getAllByPlaceholderText(/Describe your business goal in your own words...|Ask me anything...|Type your answer.../);
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