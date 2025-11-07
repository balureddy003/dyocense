import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const HelpPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 space-y-8">
      <header className="text-center space-y-3">
        <h1 className="text-4xl font-bold text-gray-900">Help Center</h1>
        <p className="text-gray-600 max-w-xl mx-auto">Find answers to common questions. More detailed FAQs coming soon.</p>
      </header>
      <section className="space-y-4">
        <div className="p-6 bg-white rounded-2xl border">
          <h2 className="font-semibold mb-2">How do I invite team members?</h2>
          <p className="text-sm text-gray-600">Use the settings page after creating your organization to send invitations.</p>
        </div>
        <div className="p-6 bg-white rounded-2xl border">
          <h2 className="font-semibold mb-2">Can I export data?</h2>
          <p className="text-sm text-gray-600">Yes, exports for key decision outputs and forecasts are available on paid tiers.</p>
        </div>
        <div className="p-6 bg-white rounded-2xl border">
          <h2 className="font-semibold mb-2">Is my data secure?</h2>
          <p className="text-sm text-gray-600">We follow industry best practices for encryption at rest and in transit.</p>
        </div>
      </section>
    </main>
    <BrandedFooter />
  </div>
);
export default HelpPage;
