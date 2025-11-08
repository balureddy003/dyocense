import { Bell, ChevronDown, CircleUserRound, Globe2, LayoutDashboard, LineChart, LogOut, Menu, Settings, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { HierarchyBreadcrumb } from "./HierarchyBreadcrumb";

const NAV_LINKS = [
  { label: "Control tower", icon: LayoutDashboard, path: "/home" },
  { label: "Playbooks", icon: LineChart, path: "/home" },
  { label: "Marketplace", path: "/home" },
  { label: "Evidence", path: "/home" },
  { label: "Reports", path: "/home" },
];

interface TopNavProps {
  // Plan-specific controls (optional - only shown in plan view)
  planName?: string;
  planVersion?: number;
  planDraftKey?: string; // localStorage key for persisting draft plan name
  projectOptions?: Array<{ id: string; name: string }>;
  currentProjectId?: string | null;
  onProjectChange?: (projectId: string) => void;
  onCreateProject?: () => void;
  dataSourcesConnected?: number;
  onPlanNameChange?: (newName: string) => void;
  onMenuClick?: () => void;
  onNewPlanClick?: () => void;
  showPlanControls?: boolean;
  dataStatusPosition?: "left" | "right"; // optional layout control
  steps?: {
    goal: boolean;
    generate: boolean;
    refine: boolean;
    save: boolean;
  };
  tenantName?: string;
  showHierarchyBreadcrumb?: boolean;
}

export const TopNav = ({
  planName,
  planVersion,
  planDraftKey,
  projectOptions = [],
  currentProjectId = null,
  onProjectChange,
  onCreateProject,
  dataSourcesConnected = 0,
  onPlanNameChange,
  onMenuClick,
  onNewPlanClick,
  showPlanControls = false,
  dataStatusPosition = "right",
  steps,
  tenantName,
  showHierarchyBreadcrumb = false,
}: TopNavProps = {}) => {
  const { user, authenticated, login, logout } = useAuth();
  const displayName = user?.fullName || user?.username || "Guest";
  const location = useLocation();
  const adminTenantId = import.meta.env.VITE_ADMIN_TENANT_ID || "admin";
  const isAdmin = authenticated && user?.id === adminTenantId;

  const [hasDraftName, setHasDraftName] = useState(false);
  const [draftName, setDraftName] = useState("");

  useEffect(() => {
    if (!planDraftKey) {
      setHasDraftName(false);
      setDraftName("");
      return;
    }
    try {
      const cached = localStorage.getItem(planDraftKey) || "";
      setDraftName(cached);
      setHasDraftName(!!cached && cached.trim() !== (planName || "").trim());
    } catch { }

    const onStorage = (e: StorageEvent) => {
      if (e.key === planDraftKey) {
        const v = e.newValue || "";
        setDraftName(v);
        setHasDraftName(!!v && v.trim() !== (planName || "").trim());
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [planDraftKey, planName]);

  return (
    <div className="bg-white border-b shadow-sm sticky top-0 z-40">
      {/* Level 1: Global Navigation */}
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between text-sm text-gray-700">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2 text-primary font-semibold text-lg">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white font-bold">D</span>
            Dyocense
          </Link>
          {showHierarchyBreadcrumb && (
            <div className="hidden lg:flex items-center gap-2 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-md border border-gray-200">
              {/* Use shared breadcrumb component */}
              <HierarchyBreadcrumb
                tenantName={tenantName}
                projectName={currentProjectId && projectOptions.length > 0 ? (projectOptions.find(p => p.id === currentProjectId)?.name || 'Project') : undefined}
                className="inline-flex items-center gap-2"
              />
            </div>
          )}
          <nav className="hidden md:flex items-center gap-5">
            {NAV_LINKS.map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.label} to={item.path || "#"} className="flex items-center gap-1 text-gray-600 hover:text-primary">
                  {Icon && <Icon size={16} className="text-gray-400" />}
                  {item.label}
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                to="/admin"
                className={`flex items-center gap-1 font-semibold ${location.pathname === "/admin" ? "text-primary" : "text-gray-600 hover:text-primary"}`}
              >
                <Shield size={16} className={location.pathname === "/admin" ? "text-primary" : "text-gray-400"} />
                Admin
              </Link>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {projectOptions && projectOptions.length > 0 && (
            <div className="hidden md:flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Project:</span>
              <select
                value={currentProjectId || ""}
                onChange={(e) => onProjectChange && onProjectChange(e.target.value)}
                className="text-sm border-0 bg-transparent px-2 py-0.5 text-gray-900 font-medium hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 rounded cursor-pointer"
                title="Select project"
              >
                {projectOptions.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              {onCreateProject && (
                <button
                  onClick={onCreateProject}
                  className="text-xs px-2 py-1 rounded-md bg-white border border-gray-200 text-primary hover:bg-blue-50 font-medium transition-colors"
                  title="Create new project"
                >
                  + New Project
                </button>
              )}
            </div>
          )}
          <button className="flex items-center gap-1 text-gray-600 hover:text-primary">
            <Globe2 size={16} /> EN
            <ChevronDown size={14} />
          </button>
          <button className="flex items-center gap-1 text-gray-600 hover:text-primary">Support</button>
          <button className="relative text-gray-600 hover:text-primary">
            <Bell size={18} />
            <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-primary" />
          </button>
          {authenticated ? (
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-2 text-gray-700 font-medium">
                <CircleUserRound size={22} className="text-primary" />
                {displayName}
              </span>
              <Link to="/settings" className="flex items-center gap-1 text-gray-600 hover:text-primary" title="Settings">
                <Settings size={16} />
              </Link>
              <button className="flex items-center gap-1 text-gray-600 hover:text-primary" onClick={() => void logout()} title="Sign out">
                <LogOut size={16} /> Logout
              </button>
            </div>
          ) : (
            <button className="flex items-center gap-2 rounded-lg border border-primary px-3 py-1.5 text-primary font-medium hover:bg-blue-50" onClick={() => void login()}>
              <CircleUserRound size={18} className="text-primary" />
              Sign in
            </button>
          )}
        </div>
      </div>

      {/* Level 2: Plan Controls */}
      {showPlanControls && (
        <div className="border-t border-gray-100 bg-white/90 supports-[backdrop-filter]:bg-white/70 backdrop-blur">
          <div className="w-full px-4 sm:px-6 py-2.5 flex items-center justify-between">
            <div className="flex-1 min-w-0 flex items-center gap-3">
              {/* Menu Icon - Opens Versions Sidebar */}
              <button onClick={onMenuClick} className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-gray-100 transition-colors" title="My Plans">
                <Menu size={18} className="text-gray-700" />
              </button>

              {/* Editable Plan Name */}
              {planName && onPlanNameChange && (
                <InlineEditableTitle
                  value={planName}
                  onSave={onPlanNameChange}
                  className="text-base font-semibold text-gray-900 truncate max-w-[40vw]"
                  placeholder="Enter plan name"
                  persistKey={planDraftKey}
                  onDraftChange={(exists, val) => {
                    setHasDraftName(exists);
                    setDraftName(val);
                  }}
                />
              )}
              {hasDraftName && (
                <span title={`Unsaved draft: ${draftName}`} className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700 border border-amber-200">Draft</span>
              )}

              {/* Version Badge */}
              {typeof planVersion === "number" && (
                <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">v{planVersion}</span>
              )}

              {/* Data Connection Status (left) */}
              {dataStatusPosition === "left" && dataSourcesConnected > 0 && (
                <div className="hidden md:flex items-center gap-1.5 text-xs text-green-700 bg-green-50 px-2.5 py-1 rounded-md border border-green-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  <span>{dataSourcesConnected} {dataSourcesConnected === 1 ? "data source" : "data sources"} connected</span>
                </div>
              )}

              {/* Steps */}
              {steps && (
                <div className="hidden md:flex items-center gap-1.5 ml-2">
                  {[
                    { key: "goal", label: "Goal", done: steps.goal },
                    { key: "generate", label: "Generate", done: steps.generate },
                    { key: "refine", label: "Refine", done: steps.refine },
                    { key: "save", label: "Save", done: steps.save },
                  ].map((s) => (
                    <span
                      key={s.key}
                      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${s.done ? "bg-green-50 border-green-200 text-green-700" : "bg-gray-50 border-gray-200 text-gray-600"}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${s.done ? "bg-green-500" : "bg-gray-400"}`} />
                      {s.label}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="shrink-0 flex items-center gap-3">
              {/* Data Connection Status (right) */}
              {dataStatusPosition === "right" && dataSourcesConnected > 0 && (
                <div className="hidden sm:flex items-center gap-1.5 text-xs text-green-700 bg-green-50 px-2.5 py-1 rounded-md border border-green-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  <span>{dataSourcesConnected} {dataSourcesConnected === 1 ? "data source" : "data sources"} connected</span>
                </div>
              )}
              <button onClick={onNewPlanClick} className="px-3.5 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium">
                + New Plan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Import InlineEditableTitle component
import { InlineEditableTitle } from "./InlineEditableTitle";
