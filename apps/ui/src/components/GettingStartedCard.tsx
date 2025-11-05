import { Sparkles, BookOpen, Zap, TrendingUp } from "lucide-react";

interface GettingStartedCardProps {
  onCreatePlaybook: () => void;
}

export const GettingStartedCard = ({ onCreatePlaybook }: GettingStartedCardProps) => {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-white rounded-3xl border border-blue-100 p-8 shadow-lg">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-semibold">
            <Sparkles size={16} />
            Getting Started with Dyocense
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome to Your Decision Intelligence Platform
          </h2>
          <p className="text-gray-600 text-base">
            Let's create your first AI-powered playbook. Choose a path to get started:
          </p>
        </div>

        {/* Quick Start Options */}
        <div className="grid md:grid-cols-3 gap-4">
          <button
            onClick={onCreatePlaybook}
            className="group p-5 rounded-2xl border-2 border-primary bg-white hover:bg-primary hover:shadow-xl transition-all text-left"
          >
            <div className="w-12 h-12 rounded-xl bg-primary/10 group-hover:bg-white/20 flex items-center justify-center mb-3 transition-colors">
              <Zap size={24} className="text-primary group-hover:text-white transition-colors" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 group-hover:text-white mb-1 transition-colors">
              Quick Start
            </h3>
            <p className="text-sm text-gray-600 group-hover:text-white/90 transition-colors">
              Launch a playbook in under 5 minutes with sample data
            </p>
            <div className="mt-3 text-xs font-semibold text-primary group-hover:text-white transition-colors">
              Recommended for first-time users →
            </div>
          </button>

          <div className="p-5 rounded-2xl border border-gray-200 bg-white opacity-60 cursor-not-allowed text-left">
            <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
              <BookOpen size={24} className="text-gray-400" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">Browse Templates</h3>
            <p className="text-sm text-gray-600">
              Choose from pre-built industry templates
            </p>
            <div className="mt-3 text-xs font-medium text-gray-500">
              Coming soon
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-gray-200 bg-white opacity-60 cursor-not-allowed text-left">
            <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
              <TrendingUp size={24} className="text-gray-400" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">Connect Data</h3>
            <p className="text-sm text-gray-600">
              Import from CSV, Google Sheets, or your ERP
            </p>
            <div className="mt-3 text-xs font-medium text-gray-500">
              Coming soon
            </div>
          </div>
        </div>

        {/* What You'll Learn */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">What you'll create:</h3>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">1</span>
              <div>
                <div className="font-medium text-gray-900">AI Playbook</div>
                <div className="text-gray-600 text-xs">Automated decision workflow</div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">2</span>
              <div>
                <div className="font-medium text-gray-900">Forecasts</div>
                <div className="text-gray-600 text-xs">Predict demand and trends</div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">3</span>
              <div>
                <div className="font-medium text-gray-900">Optimized Plans</div>
                <div className="text-gray-600 text-xs">AI-recommended actions</div>
              </div>
            </div>
          </div>
        </div>

        {/* Help Links */}
        <div className="flex items-center justify-center gap-6 text-sm">
          <a href="#" className="text-primary font-medium hover:underline">
            📺 Watch video tutorial
          </a>
          <a href="#" className="text-primary font-medium hover:underline">
            📖 Read the docs
          </a>
          <a href="#" className="text-primary font-medium hover:underline">
            💬 Get help
          </a>
        </div>
      </div>
    </div>
  );
};
