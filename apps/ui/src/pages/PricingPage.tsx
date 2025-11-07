import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const PricingPage = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <BrandedHeader showNav={false} />
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-12 space-y-8">
        <header className="text-center space-y-3">
          <h1 className="text-4xl font-bold text-gray-900">Pricing</h1>
          <p className="text-gray-600 max-w-2xl mx-auto">Simple, transparent plans. Start free and scale when you're ready.</p>
        </header>
        <p className="text-sm text-gray-500">(Detailed pricing matrix coming soon.)</p>
      </main>
      <BrandedFooter />
    </div>
  );
};
export default PricingPage;
