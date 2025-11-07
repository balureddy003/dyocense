import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

export const SecurityPage = () => (
  <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-blue-100">
    <BrandedHeader showNav={false} />
    <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold text-gray-900">Security</h1>
        <p className="text-gray-600">Overview of our approach to protecting your data.</p>
      </header>
      <section className="space-y-4 text-sm text-gray-700 leading-relaxed">
        <p>All data encrypted in transit (TLS) and at rest (cloud provider managed keys). Customer-segregated namespaces for tenant isolation.</p>
        <p>Role-based access controls govern sensitive operations. Audit logging in progress for privileged actions.</p>
        <p>Regular dependency scanning and infrastructure hardening. Planned SOC 2 Type I readiness work.</p>
        <p>Report security concerns to security@dyocense.com.</p>
      </section>
    </main>
    <BrandedFooter />
  </div>
);
export default SecurityPage;
