import { useEffect, useState } from "react";
import { TopNav } from "../components/TopNav";
import { getAuthHeaders } from "../lib/config";
import { API_BASE_URL } from "../lib/config";

interface TenantItem {
  tenant_id: string;
  name: string;
  owner_email: string;
  plan_tier: string;
  status: string;
  created_at: string;
  usage: {
    projects: number;
    playbooks: number;
    members: number;
  };
}

interface TenantsResponse {
  tenants: TenantItem[];
  total: number;
  limit: number;
  skip: number;
}

interface AnalyticsSummary {
  total_events: number;
  events_by_type: Record<string, number>;
  tenants_with_activity: number;
  date_range: {
    start: string;
    end: string;
  };
}

export const AdminDashboardPage = () => {
  const [tenants, setTenants] = useState<TenantItem[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPlan, setFilterPlan] = useState<string>("all");

  useEffect(() => {
    loadTenants();
    loadAnalytics();
  }, [skip]);

  const loadTenants = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/v1/admin/tenants?limit=${limit}&skip=${skip}`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("Access denied. Admin privileges required.");
        }
        throw new Error("Failed to load tenants");
      }
      const data: TenantsResponse = await response.json();
      setTenants(data.tenants);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.message || "Failed to load tenants");
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/admin/analytics?days=30`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.warn("Failed to load analytics", err);
    }
  };

  const changePlan = async (tenantId: string, newPlan: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/admin/tenants/${tenantId}/plan?plan_tier=${newPlan}`, {
        method: "PUT",
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error("Failed to update plan");
      await loadTenants();
    } catch (err: any) {
      alert(err.message || "Failed to update plan");
    }
  };

  const filteredTenants = tenants.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.owner_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.tenant_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPlan = filterPlan === "all" || t.plan_tier === filterPlan;
    return matchesSearch && matchesPlan;
  });

  return (
    <div className="min-h-screen flex flex-col bg-bg text-gray-900">
      <TopNav />
      <div className="max-w-7xl mx-auto w-full px-6 pt-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">Platform management and analytics</p>
          </div>
        </div>

        {/* Analytics Summary */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm px-6 py-4">
              <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Total Events</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.total_events}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm px-6 py-4">
              <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Active Tenants</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.tenants_with_activity}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm px-6 py-4">
              <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Total Tenants</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{total}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm px-6 py-4">
              <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Event Types</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{Object.keys(analytics.events_by_type).length}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Filters and Search */}
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm px-6 py-4 flex flex-wrap items-center gap-4">
          <input
            type="text"
            placeholder="Search by name, email, or tenant ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 min-w-[300px] px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <select
            value={filterPlan}
            onChange={(e) => setFilterPlan(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All Plans</option>
            <option value="free">Free</option>
            <option value="silver">Silver</option>
            <option value="gold">Gold</option>
            <option value="platinum">Platinum</option>
          </select>
        </div>

        {/* Tenants Table */}
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          {loading ? (
            <div className="px-6 py-12 text-center text-sm text-gray-500">Loading tenants...</div>
          ) : filteredTenants.length === 0 ? (
            <div className="px-6 py-12 text-center text-sm text-gray-500">No tenants found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Tenant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Owner
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Plan
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Usage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredTenants.map((tenant) => (
                    <tr key={tenant.tenant_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">{tenant.name}</p>
                          <p className="text-xs text-gray-500">{tenant.tenant_id}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700">{tenant.owner_email}</td>
                      <td className="px-6 py-4">
                        <select
                          value={tenant.plan_tier}
                          onChange={(e) => changePlan(tenant.tenant_id, e.target.value)}
                          className="px-3 py-1 border border-gray-300 rounded text-xs font-semibold uppercase focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                          <option value="free">Free</option>
                          <option value="silver">Silver</option>
                          <option value="gold">Gold</option>
                          <option value="platinum">Platinum</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 text-gray-600 text-xs">
                        {tenant.usage.projects} projects · {tenant.usage.playbooks} playbooks · {tenant.usage.members} members
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                            tenant.status === "active"
                              ? "bg-green-100 text-green-800"
                              : tenant.status === "trial"
                              ? "bg-blue-100 text-blue-800"
                              : tenant.status === "suspended"
                              ? "bg-red-100 text-red-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {tenant.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-600 text-xs">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          className="text-xs text-primary font-semibold hover:underline"
                          onClick={() => {
                            alert(`View details for ${tenant.name} (coming soon)`);
                          }}
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {total > limit && (
          <div className="flex items-center justify-between px-6">
            <p className="text-sm text-gray-600">
              Showing {skip + 1}-{Math.min(skip + limit, total)} of {total} tenants
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setSkip(Math.max(0, skip - limit))}
                disabled={skip === 0}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setSkip(skip + limit)}
                disabled={skip + limit >= total}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
