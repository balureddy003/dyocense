import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const DocsPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-12 space-y-6">
      <header className="space-y-2 text-center">
        <h1 className="text-4xl font-bold text-gray-900">Documentation</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">Guides and references to help you integrate and succeed with Dyocense.</p>
      </header>
      <div className="grid gap-6 md:grid-cols-2">
        <article className="p-6 rounded-2xl bg-white border shadow-sm">
          <h2 className="font-semibold mb-2">Getting Started</h2>
          <p className="text-sm text-gray-600">Account creation, onboarding, and basic workflow setup.</p>
        </article>
        <article className="p-6 rounded-2xl bg-white border shadow-sm">
          <h2 className="font-semibold mb-2">API Reference</h2>
          <p className="text-sm text-gray-600">Endpoints for programmatic access (coming soon).</p>
        </article>
        <article className="p-6 rounded-2xl bg-white border shadow-sm">
          <h2 className="font-semibold mb-2">Data Connectors</h2>
          <p className="text-sm text-gray-600">How to sync POS, accounting, and spreadsheet data.</p>
        </article>
        <article className="p-6 rounded-2xl bg-white border shadow-sm">
          <h2 className="font-semibold mb-2">Decision Engine</h2>
          <p className="text-sm text-gray-600">Optimization and forecasting concepts explained.</p>
        </article>
      </div>
    </main>
    <BrandedFooter />
  </div>
);
export default DocsPage;
