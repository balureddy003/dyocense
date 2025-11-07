/**
 * Quick Tip Banner - Contextual help for SMB users
 * Shows helpful tips at the right moment
 */

import { Lightbulb, X } from "lucide-react";
import { useState } from "react";

type QuickTipBannerProps = {
  tip: string;
  onDismiss?: () => void;
  dismissible?: boolean;
  variant?: "info" | "success" | "warning";
};

export function QuickTipBanner({
  tip,
  onDismiss,
  dismissible = true,
  variant = "info",
}: QuickTipBannerProps) {
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) return null;

  const colors = {
    info: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      text: "text-blue-800",
      icon: "text-blue-500",
    },
    success: {
      bg: "bg-green-50",
      border: "border-green-200",
      text: "text-green-800",
      icon: "text-green-500",
    },
    warning: {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      text: "text-yellow-800",
      icon: "text-yellow-500",
    },
  };

  const style = colors[variant];

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  return (
    <div
      className={`${style.bg} ${style.border} border rounded-lg p-3 flex items-start gap-3 shadow-sm`}
    >
      <Lightbulb className={`${style.icon} flex-shrink-0 mt-0.5`} size={18} />
      <p className={`${style.text} text-sm flex-1`}>{tip}</p>
      {dismissible && (
        <button
          onClick={handleDismiss}
          className={`${style.text} hover:opacity-70 transition-opacity flex-shrink-0`}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
