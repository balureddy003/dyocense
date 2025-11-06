import { describe, it, expect } from 'vitest';
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe('Auth logout clears state', () => {
  it('clears local storage and user state after token login', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.loginWithToken({
        apiToken: 'test-token',
        tenantId: 'test-tenant',
        displayName: 'Tester',
        email: 'tester@example.com',
        remember: true,
      });
    });

    expect(result.current.authenticated).toBe(true);
    expect(localStorage.getItem('dyocense-api-token')).toBe('test-token');
    expect(localStorage.getItem('dyocense-tenant-id')).toBe('test-tenant');

    await act(async () => {
      await result.current.logout();
    });

    expect(localStorage.getItem('dyocense-api-token')).toBeNull();
    expect(localStorage.getItem('dyocense-tenant-id')).toBeNull();
    expect(result.current.authenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});
