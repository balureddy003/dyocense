import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const AboutPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 space-y-8">
      <header className="space-y-3 text-center">
        <h1 className="text-4xl font-bold text-gray-900">About Dyocense</h1>
        <p className="text-gray-600 max-w-xl mx-auto">We believe advanced decision intelligence should be accessible to every small business—not just giant enterprises.</p>
      </header>
      <section className="space-y-4">
        <p className="text-gray-700 leading-relaxed">Dyocense started with a simple observation: small business owners make dozens of high-impact decisions daily with limited tools. We set out to bring forecasting, optimization, and explainable AI into a single approachable workspace.</p>
        <p className="text-gray-700 leading-relaxed">Our platform blends proven quantitative methods with modern AI to deliver clear, trustworthy recommendations—not black-box guesses.</p>
        <p className="text-gray-700 leading-relaxed">We're just getting started. If you're passionate about empowering real-world businesses, we'd love to talk.</p>
      </section>
    </main>
    <BrandedFooter />
  </div>
);
export default AboutPage;
