import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatPanel } from '../components/ChatPanel';

describe('<ChatPanel />', () => {
  it('renders and disables analyze until context is ready', () => {
    const noop = () => {};
    render(<ChatPanel onContext={noop} onPlanRequest={noop} />);
    const analyze = screen.getByRole('button', { name: /Analyze with AI/i });
    expect(analyze).toBeDisabled();
  });
});
