import { Bell, ChevronDown, CircleUserRound, Globe2, LayoutDashboard, LineChart, LogOut, Shield, Settings } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Link, useLocation } from "react-router-dom";

const NAV_LINKS = [
  { label: "Control tower", icon: LayoutDashboard, path: "/home" },
  { label: "Playbooks", icon: LineChart, path: "/home" },
  { label: "Marketplace", path: "/home" },
  { label: "Evidence", path: "/home" },
  { label: "Reports", path: "/home" },
];

export const TopNav = () => {
  const { user, authenticated, login, logout, usingMock } = useAuth();
  const displayName = user?.fullName || user?.username || "Guest";
  const location = useLocation();
  const adminTenantId = import.meta.env.VITE_ADMIN_TENANT_ID || "admin";
  const isAdmin = authenticated && user?.id === adminTenantId;

  return (
    <div className="bg-white border-b shadow-sm">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between text-sm text-gray-700">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2 text-primary font-semibold text-lg">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white font-bold">
              D
            </span>
            Dyocense
          </Link>
          <nav className="hidden md:flex items-center gap-5">
            {NAV_LINKS.map((item) => {
              const Icon = item.icon;
              return (
                <Link 
                  key={item.label} 
                  to={item.path || "#"}
                  className="flex items-center gap-1 text-gray-600 hover:text-primary"
                >
                  {Icon && <Icon size={16} className="text-gray-400" />}
                  {item.label}
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                to="/admin"
                className={`flex items-center gap-1 font-semibold ${
                  location.pathname === "/admin" ? "text-primary" : "text-gray-600 hover:text-primary"
                }`}
              >
                <Shield size={16} className={location.pathname === "/admin" ? "text-primary" : "text-gray-400"} />
                Admin
              </Link>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <button className="flex items-center gap-1 text-gray-600 hover:text-primary">
            <Globe2 size={16} /> EN
            <ChevronDown size={14} />
          </button>
          <button className="flex items-center gap-1 text-gray-600 hover:text-primary">
            Support
          </button>
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
              <Link
                to="/settings"
                className="flex items-center gap-1 text-gray-600 hover:text-primary"
                title="Settings"
              >
                <Settings size={16} />
              </Link>
              <button
                className="flex items-center gap-1 text-gray-600 hover:text-primary"
                onClick={() => void logout()}
                title={usingMock ? "Sign out (mock)" : "Sign out"}
              >
                <LogOut size={16} /> Logout
              </button>
            </div>
          ) : (
            <button
              className="flex items-center gap-2 rounded-lg border border-primary px-3 py-1.5 text-primary font-medium hover:bg-blue-50"
              onClick={() => void login()}
            >
              <CircleUserRound size={18} className="text-primary" />
              Sign in
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
