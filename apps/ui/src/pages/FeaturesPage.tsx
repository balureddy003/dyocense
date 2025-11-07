import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const FeaturesPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-12 space-y-6">
      <header className="text-center space-y-3">
        <h1 className="text-4xl font-bold text-gray-900">Features</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">Overview of Dyocense capabilities at a glance.</p>
      </header>
      <ul className="grid gap-4 md:grid-cols-2">
        <li className="p-6 bg-white rounded-2xl border">Inventory optimization and demand forecasting</li>
        <li className="p-6 bg-white rounded-2xl border">Smart staffing and schedule planning</li>
        <li className="p-6 bg-white rounded-2xl border">Clear, explainable recommendations</li>
        <li className="p-6 bg-white rounded-2xl border">Connectors for spreadsheets and POS</li>
      </ul>
    </main>
    <BrandedFooter />
  </div>
);
export default FeaturesPage;
