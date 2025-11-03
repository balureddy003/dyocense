import { CalendarHeart, LineChart, ShieldCheck } from "lucide-react";

export const Hero = () => (
  <section className="bg-gradient-to-r from-blue-50 via-white to-blue-50">
    <div className="max-w-6xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6">
      <div className="space-y-3">
        <span className="text-xs font-semibold tracking-wide text-primary uppercase">AI-guided plan</span>
        <h2 className="text-2xl md:text-3xl font-semibold text-gray-900">
          Turn goal, plan, and review into a single guided flow your team can act on.
        </h2>
        <p className="text-gray-600 text-base md:text-lg">
          Capture the business objective, simulate scenarios, and package a ready-to-share playbook—no data science jargon required.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <article className="bg-white rounded-xl shadow-card p-5 space-y-2">
          <CalendarHeart className="text-primary" size={20} />
          <h3 className="text-sm font-semibold text-gray-800">Guided milestones</h3>
          <p className="text-xs text-gray-600">Goal → Plan → Review steps keep everyone aligned on progress.</p>
        </article>
        <article className="bg-white rounded-xl shadow-card p-5 space-y-2">
          <LineChart className="text-primary" size={20} />
          <h3 className="text-sm font-semibold text-gray-800">Scenario clarity</h3>
          <p className="text-xs text-gray-600">Layman-friendly charts and notes explain the "so what" for each scenario.</p>
        </article>
        <article className="bg-white rounded-xl shadow-card p-5 space-y-2">
          <ShieldCheck className="text-primary" size={20} />
          <h3 className="text-sm font-semibold text-gray-800">Evidence ready</h3>
          <p className="text-xs text-gray-600">Surface lineage and artifacts alongside recommendations for easy review.</p>
        </article>
      </div>
    </div>
  </section>
);
