import { HelpCircle } from "lucide-react";
import { useState } from "react";

interface TooltipProps {
  content: string;
  position?: "top" | "bottom" | "left" | "right";
}

export const Tooltip = ({ content, position = "top" }: TooltipProps) => {
  const [show, setShow] = useState(false);

  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  return (
    <div className="relative inline-block">
      <button
        type="button"
        className="text-gray-400 hover:text-primary transition"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onFocus={() => setShow(true)}
        onBlur={() => setShow(false)}
        aria-label="Help"
      >
        <HelpCircle size={16} />
      </button>
      {show && (
        <div
          className={`absolute z-50 ${positionClasses[position]} w-64 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg`}
        >
          <div className="relative">
            {content}
            {/* Arrow */}
            <div
              className={`absolute w-2 h-2 bg-gray-900 transform rotate-45 ${
                position === "top"
                  ? "top-full left-1/2 -translate-x-1/2 -mt-1"
                  : position === "bottom"
                  ? "bottom-full left-1/2 -translate-x-1/2 -mb-1"
                  : position === "left"
                  ? "left-full top-1/2 -translate-y-1/2 -ml-1"
                  : "right-full top-1/2 -translate-y-1/2 -mr-1"
              }`}
            />
          </div>
        </div>
      )}
    </div>
  );
};
