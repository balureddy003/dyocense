import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const TermsPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold text-gray-900">Terms of Service</h1>
        <p className="text-gray-600">Key points. Full legal agreement pending final review.</p>
      </header>
      <section className="space-y-4 text-sm text-gray-700 leading-relaxed">
        <p>Use of the platform is subject to fair usage. Abuse, fraud, or attempts to reverse-engineer the service may result in suspension.</p>
        <p>Recommendations are generated using best-effort modeling. Final business decisions remain your responsibility.</p>
        <p>Paid plans renew monthly unless canceled prior to renewal date.</p>
        <p>We may update these terms; changes will be communicated to administrators.</p>
      </section>
    </main>
    <BrandedFooter />
  </div>
);
export default TermsPage;
