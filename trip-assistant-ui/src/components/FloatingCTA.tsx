import { Lightbulb, Play, Share2, Sparkles } from "lucide-react";

export const FloatingCTA = () => (
  <div className="fixed bottom-4 right-4 flex flex-col gap-3 z-40">
    <button className="bg-primary text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm">
      <Sparkles size={18} /> Generate new scenario
    </button>
    <button className="bg-accent text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm">
      <Play size={18} /> Re-run plan
    </button>
    <button className="bg-gray-900 text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm">
      <Lightbulb size={18} /> Share insights
    </button>
    <button className="bg-white text-gray-800 px-4 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm border">
      <Share2 size={18} /> Export briefing
    </button>
  </div>
);
