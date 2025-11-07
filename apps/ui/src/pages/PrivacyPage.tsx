import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const PrivacyPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
        <p className="text-gray-600">How we handle and protect your data. Full legal version coming soon.</p>
      </header>
      <section className="space-y-4 text-sm text-gray-700 leading-relaxed">
        <p>We only collect data required to provide forecasting, optimization, and collaboration features. We do not sell your data.</p>
        <p>Data is encrypted at rest and in transit. Access is restricted and audited.</p>
        <p>You can request deletion of your account and associated data at any time by emailing support@dyocense.com.</p>
        <p>Third-party integrations are opt-in and can be revoked at any time.</p>
      </section>
    </main>
    <BrandedFooter />
  </div>
);
export default PrivacyPage;
