import { useEffect, useState } from "react";
import { Sparkles, Clock, ArrowRight } from "lucide-react";
import { getPlaybookRecommendations, PlaybookRecommendation } from "../lib/api";

interface RecommendedPlaybooksProps {
  onSelectPlaybook: (archetypeId: string) => void;
}

export const RecommendedPlaybooks = ({ onSelectPlaybook }: RecommendedPlaybooksProps) => {
  const [recommendations, setRecommendations] = useState<PlaybookRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [industry, setIndustry] = useState<string>("");

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      const data = await getPlaybookRecommendations();
      setRecommendations(data.recommendations);
      setIndustry(data.industry);
    } catch (error) {
      console.error("Failed to load recommendations:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 bg-gray-100 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Sparkles size={20} className="text-primary" />
            Recommended for You
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Popular playbooks for {industry} industry
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {recommendations.map((rec) => (
          <button
            key={rec.id}
            onClick={() => onSelectPlaybook(rec.archetype_id)}
            className="group text-left p-5 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all bg-white"
          >
            <div className="space-y-3">
              {/* Icon and Tags */}
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-lg bg-blue-50 group-hover:bg-primary/10 flex items-center justify-center text-2xl transition-colors">
                  {rec.icon}
                </div>
                <div className="flex flex-wrap gap-1">
                  {rec.tags.slice(0, 1).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Title and Description */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-1 group-hover:text-primary transition-colors">
                  {rec.title}
                </h4>
                <p className="text-xs text-gray-600 line-clamp-2">
                  {rec.description}
                </p>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock size={12} />
                  {rec.estimated_time}
                </div>
                <ArrowRight
                  size={16}
                  className="text-gray-400 group-hover:text-primary group-hover:translate-x-1 transition-all"
                />
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
