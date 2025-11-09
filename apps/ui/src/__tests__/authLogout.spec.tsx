
// Mock keycloak-js before any imports
vi.mock('keycloak-js', () => ({
  default: function () {
    return {
      logout: vi.fn().mockResolvedValue(undefined),
      init: vi.fn().mockResolvedValue(true),
      onTokenExpired: undefined,
      tokenParsed: {
        sub: 'test-tenant',
        name: 'Tester',
        email: 'tester@example.com',
        preferred_username: 'tester',
      },
      token: 'test-token',
      login: vi.fn().mockResolvedValue(undefined),
    };
  },
}));

import { act, renderHook } from '@testing-library/react';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '../context/AuthContext';
import * as api from '../lib/api';

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe('Auth logout clears state', () => {
  beforeEach(() => {
    // Mock getTenantProfile and fetchUserProfile to avoid real API calls
    vi.spyOn(api, 'getTenantProfile').mockResolvedValue({
      tenant_id: 'test-tenant',
      name: 'Test Tenant',
      owner_email: 'tester@example.com',
      plan: {
        tier: 'basic',
        name: 'Basic',
        price_per_month: 0,
        description: 'Basic plan',
        limits: {
          max_projects: 5,
          max_playbooks: 10,
          max_members: 3,
          support_level: 'email',
        },
        features: ['feature1', 'feature2'],
      },
      status: 'active',
      usage: {
        projects: 1,
        playbooks: 1,
        members: 1,
        cycle_started_at: new Date().toISOString(),
      },
    });
    vi.spyOn(api, 'fetchUserProfile').mockResolvedValue({
      user_id: 'test-tenant',
      tenant_id: 'test-tenant',
      email: 'tester@example.com',
      full_name: 'Tester',
      roles: ['user'],
    });
  });
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
