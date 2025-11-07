import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { PropsWithChildren } from "react";
import { LandingPage } from "./LandingPage";
import { LoginPage } from "./LoginPage";
import { ProfileSetupPage } from "./ProfileSetupPage";
import { HomePage } from "./HomePage";
import { OnboardingPage } from "./OnboardingPage";
import { PurchasePage } from "./PurchasePage";
import { AdminDashboardPage } from "./AdminDashboardPage";
import { AcceptInvitePage } from "./AcceptInvitePage";
import { SettingsPage } from "./SettingsPage";
import { BlogPage } from "./BlogPage";
import { MarketplacePage } from "./MarketplacePage";
import { useAuth } from "../context/AuthContext";
import PricingPage from "./PricingPage";
import FeaturesPage from "./FeaturesPage";
import DocsPage from "./DocsPage";
import HelpPage from "./HelpPage";
import AboutPage from "./AboutPage";
import PrivacyPage from "./PrivacyPage";
import TermsPage from "./TermsPage";
import SecurityPage from "./SecurityPage";
import { OAuthCallbackPage } from "./OAuthCallbackPage";
 

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

export const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
    <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
      <Route path="/blog" element={<BlogPage />} />
      <Route path="/blog/:postId" element={<BlogPage />} />
      <Route path="/marketplace" element={<MarketplacePage />} />
  {/* Public marketing/support pages */}
  <Route path="/pricing" element={<PricingPage />} />
  <Route path="/features" element={<FeaturesPage />} />
  <Route path="/docs" element={<DocsPage />} />
  <Route path="/help" element={<HelpPage />} />
  <Route path="/about" element={<AboutPage />} />
  <Route path="/privacy" element={<PrivacyPage />} />
  <Route path="/terms" element={<TermsPage />} />
  <Route path="/security" element={<SecurityPage />} />
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
        path="/onboarding"
        element={
          <RequireAuth>
            <OnboardingPage />
          </RequireAuth>
        }
      />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomePage />
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
