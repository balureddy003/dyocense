import { Link, useNavigate } from "react-router-dom";
import { Building2, Settings, LogOut, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface BrandedHeaderProps {
  showNav?: boolean;
}

export const BrandedHeader = ({ showNav = false }: BrandedHeaderProps) => {
  const { authenticated, profile, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Brand */}
          <Link to={authenticated ? "/home" : "/"} className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold text-lg shadow-md group-hover:shadow-lg transition">
              D
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition">
                Dyocense
              </h1>
              <p className="text-xs text-gray-500 leading-none">
                Your AI Business Agent
              </p>
            </div>
          </Link>

          {/* Navigation */}
          {showNav && authenticated && (
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link
                to="/home"
                className="text-gray-700 hover:text-blue-600 font-medium transition"
              >
                Dashboard
              </Link>
              <Link
                to="/marketplace"
                className="text-gray-700 hover:text-blue-600 font-medium transition"
              >
                Marketplace
              </Link>
              <Link
                to="/blog"
                className="text-gray-700 hover:text-blue-600 font-medium transition"
              >
                Blog
              </Link>
              <Link
                to="/projects"
                className="text-gray-700 hover:text-blue-600 font-medium transition"
              >
                Projects
              </Link>
            </nav>
          )}

          {/* User Menu */}
          <div className="flex items-center gap-3">
            {authenticated && profile ? (
              <>
                <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 border border-gray-200">
                  <Building2 size={16} className="text-gray-500" />
                  <span className="text-sm text-gray-700 font-medium">
                    {profile.companyName || "My Business"}
                  </span>
                </div>
                <Link
                  to="/settings"
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition"
                  title="Settings"
                >
                  <Settings size={20} />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition"
                  title="Sign out"
                >
                  <LogOut size={20} />
                </button>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="text-sm font-medium text-gray-700 hover:text-blue-600 transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/buy?plan=trial"
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 shadow-md hover:shadow-lg transition"
                >
                  Start Free Trial
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
