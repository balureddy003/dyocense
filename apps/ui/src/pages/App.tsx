import { PropsWithChildren } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AboutPage from "./AboutPage";
import { AcceptInvitePage } from "./AcceptInvitePage";
import { AdminDashboardPage } from "./AdminDashboardPage";
import { BlogPage } from "./BlogPage";
import DocsPage from "./DocsPage";
import FeaturesPage from "./FeaturesPage";
import HelpPage from "./HelpPage";
import { HomePage } from "./HomePage";
import { LandingPage } from "./LandingPage";
import { LoginPage } from "./LoginPage";
import { MarketplacePage } from "./MarketplacePage";
import { OAuthCallbackPage } from "./OAuthCallbackPage";
import { OnboardingPage } from "./OnboardingPage";
import PricingPage from "./PricingPage";
import PrivacyPage from "./PrivacyPage";
import { ProfileSetupPage } from "./ProfileSetupPage";
import { PurchasePage } from "./PurchasePage";
import SalesInsightsPage from "./SalesInsightsPage";
import SecurityPage from "./SecurityPage";
import { SettingsPage } from "./SettingsPage";
import SignupPage from "./SignupPage";
import TermsPage from "./TermsPage";
import VerifyPage from "./VerifyPage";


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
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/verify" element={<VerifyPage />} />
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
        path="/sales"
        element={
          <RequireAuth>
            <SalesInsightsPage />
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
