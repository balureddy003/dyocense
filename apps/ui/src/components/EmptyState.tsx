import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  illustration?: ReactNode;
}

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  illustration,
}: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
      {illustration || (
        <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <Icon size={32} className="text-gray-400" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 max-w-md mb-6">{description}</p>
      {(action || secondaryAction) && (
        <div className="flex items-center gap-3">
          {action && (
            <button
              onClick={action.onClick}
              className="px-5 py-2.5 rounded-lg bg-primary text-white font-semibold text-sm shadow-sm hover:bg-blue-700 transition"
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium text-sm hover:bg-gray-50 transition"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
