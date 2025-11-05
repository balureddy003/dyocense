import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { PropsWithChildren } from "react";
import { LandingPage } from "./LandingPage";
import { LoginPage } from "./LoginPage";
import { ProfileSetupPage } from "./ProfileSetupPage";
import { HomePage } from "./HomePage";
import { PurchasePage } from "./PurchasePage";
import { AdminDashboardPage } from "./AdminDashboardPage";
import { AcceptInvitePage } from "./AcceptInvitePage";
import { SettingsPage } from "./SettingsPage";
import { useAuth } from "../context/AuthContext";

const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-white text-sm text-gray-500">
    Preparing your workspace…
  </div>
);

const RequireAuth = ({ children }: PropsWithChildren) => {
  const { ready, authenticated } = useAuth();
  const location = useLocation();

  if (!ready) {
    return <LoadingScreen />;
  }

  if (!authenticated) {
    const destination = `${location.pathname}${location.search}`;
    const redirect = encodeURIComponent(destination || "/home");
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }

  return <>{children}</>;
};

const RequireProfile = ({ children }: PropsWithChildren) => {
  const { profile } = useAuth();
  const location = useLocation();

  if (!profile && location.pathname !== "/profile") {
    return <Navigate to="/profile" replace />;
  }

  return <>{children}</>;
};

export const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/accept-invite/:inviteId" element={<AcceptInvitePage />} />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfileSetupPage />
          </RequireAuth>
        }
      />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <RequireProfile>
              <HomePage />
            </RequireProfile>
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <AdminDashboardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/settings"
        element={
          <RequireAuth>
            <SettingsPage />
          </RequireAuth>
        }
      />
      <Route path="/buy" element={<PurchasePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
