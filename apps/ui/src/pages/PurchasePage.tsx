import { CheckCircle2, Headset, Mail, Shield } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const PurchasePage = () => {
  const { authenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-white">
      <section className="max-w-4xl mx-auto px-6 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <h1 className="text-3xl font-semibold text-gray-900">Launch Dyocense at your organization</h1>
          <p className="text-gray-600 text-base">
            Choose the bundle that matches your scale. Our team partners with you on onboarding, integrations, and
            first wins inside 30 days.
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          <article className="border rounded-3xl p-6 shadow-sm bg-blue-50/40 space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Growth</h2>
            <p className="text-sm text-gray-600">For teams standing up their first AI planning playbooks.</p>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                2 Dyocense decision archetypes
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                Managed data onboarding & governance
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                3 guided AI copilots with usage analytics
              </li>
            </ul>
            <div className="pt-3 text-sm text-gray-600">Starts at $4,800 / month</div>
          </article>

          <article className="border rounded-3xl p-6 shadow-sm bg-white space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Enterprise</h2>
            <p className="text-sm text-gray-600">For global operations with advanced control tower needs.</p>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                Unlimited decision archetypes & sandboxing
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                Fine-grained governance, audit, and SOC2 tooling
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={18} className="text-primary mt-0.5" />
                Dedicated solution architects & 24/7 support
              </li>
            </ul>
            <div className="pt-3 text-sm text-gray-600">Custom pricing</div>
          </article>
        </div>

        <section className="border rounded-3xl p-6 bg-white shadow-sm space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Next steps</h2>
          <p className="text-sm text-gray-600">
            Share a few details and we’ll schedule a tailored walkthrough of Dyocense with your stakeholders.
          </p>
          <div className="grid gap-4 md:grid-cols-2 text-sm text-gray-700">
            <p className="flex items-center gap-2">
              <Mail size={18} className="text-primary" /> hello@dyocense.ai
            </p>
            <p className="flex items-center gap-2">
              <Headset size={18} className="text-primary" /> Live implementation support included
            </p>
            <p className="flex items-center gap-2">
              <Shield size={18} className="text-primary" /> SOC2 Type II and GDPR-ready
            </p>
            <p className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-primary" /> {authenticated ? `We’ll reach out to ${user?.email}` : "We’ll follow up within 1 business day"}
            </p>
          </div>
          <form className="grid gap-4 md:grid-cols-2">
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Name"
            />
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Company"
            />
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Email"
              defaultValue={user?.email}
            />
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Phone (optional)"
            />
            <textarea
              className="md:col-span-2 px-3 py-2 min-h-[120px] rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Tell us about your priorities"
            />
            <button
              type="submit"
              className="md:col-span-2 px-4 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition"
            >
              Schedule a strategy session
            </button>
          </form>
        </section>
      </section>
    </div>
  );
};
