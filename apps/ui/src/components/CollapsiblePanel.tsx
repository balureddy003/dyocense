/**
 * Collapsible Panel Wrapper
 * Google Maps-style panel with expand/collapse and resize controls
 */

import { ChevronLeft, ChevronRight, Maximize2, Minimize2, Maximize } from "lucide-react";
import { useState, ReactNode } from "react";

type PanelPosition = "left" | "center" | "right";

type CollapsiblePanelProps = {
  children: ReactNode;
  position: PanelPosition;
  defaultWidth?: string;
  minWidth?: string;
  maxWidth?: string;
  title?: string;
  collapsible?: boolean;
  resizable?: boolean;
  defaultCollapsed?: boolean;
  onCollapseChange?: (collapsed: boolean) => void;
  showFullscreenButton?: boolean;
};

export function CollapsiblePanel({
  children,
  position,
  defaultWidth = "384px", // 24rem
  minWidth = "320px",
  maxWidth = "600px",
  title,
  collapsible = true,
  resizable = true,
  defaultCollapsed = false,
  onCollapseChange,
  showFullscreenButton = false,
}: CollapsiblePanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [width, setWidth] = useState(defaultWidth);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleToggleCollapse = () => {
    const newCollapsed = !collapsed;
    setCollapsed(newCollapsed);
    onCollapseChange?.(newCollapsed);
  };

  const handleToggleExpand = () => {
    if (isExpanded) {
      setWidth(defaultWidth);
      setIsExpanded(false);
    } else {
      setWidth(maxWidth);
      setIsExpanded(true);
    }
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Determine collapse button position and icon
  const CollapseIcon = position === "left" ? ChevronLeft : ChevronRight;
  const ExpandIcon = collapsed
    ? position === "left"
      ? ChevronRight
      : ChevronLeft
    : CollapseIcon;

  if (collapsed) {
    return (
      <div className={`relative flex-shrink-0 bg-white border-r border-gray-200 transition-all duration-200 ease-in-out`}>
        {/* Collapsed Tab */}
        <div className="w-12 h-full flex flex-col items-center py-4 gap-4">
          {collapsible && (
            <button
              onClick={handleToggleCollapse}
              className="w-8 h-8 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 hover:border-blue-400 flex items-center justify-center shadow-sm transition-all"
              title="Expand panel"
            >
              <ExpandIcon size={16} className="text-gray-600" />
            </button>
          )}
          {title && (
            <div
              className="writing-mode-vertical text-xs font-semibold text-gray-600 tracking-wider uppercase rotate-180"
              style={{ writingMode: "vertical-rl" }}
            >
              {title}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Fullscreen mode
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex flex-col animate-in fade-in duration-200">
        {/* Fullscreen Controls */}
        <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
          <button
            onClick={handleToggleFullscreen}
            className="w-9 h-9 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 hover:border-blue-400 flex items-center justify-center shadow-md transition-all"
            title="Exit fullscreen"
          >
            <Minimize2 size={16} className="text-gray-600" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`relative bg-white transition-all duration-200 ease-in-out flex flex-col ${
        position === "center" ? "flex-1" : "flex-shrink-0"
      } ${
        position === "right" ? "border-l border-gray-200" : position === "left" ? "border-r border-gray-200" : ""
      }`}
      style={position !== "center" && resizable ? { width } : undefined}
    >
      {/* Panel Controls */}
      <div className={`absolute top-2 z-10 flex items-center gap-1 ${
        position === "right" ? "left-2" : "right-2"
      }`}>
        {showFullscreenButton && (
          <button
            onClick={handleToggleFullscreen}
            className="w-7 h-7 rounded-md bg-white border border-gray-300 hover:bg-gray-50 hover:border-blue-400 flex items-center justify-center shadow-sm transition-all"
            title="Fullscreen"
          >
            <Maximize size={14} className="text-gray-600" />
          </button>
        )}
        {resizable && (
          <button
            onClick={handleToggleExpand}
            className="w-7 h-7 rounded-md bg-white border border-gray-300 hover:bg-gray-50 hover:border-blue-400 flex items-center justify-center shadow-sm transition-all"
            title={isExpanded ? "Reduce width" : "Expand width"}
          >
            {isExpanded ? (
              <Minimize2 size={14} className="text-gray-600" />
            ) : (
              <Maximize2 size={14} className="text-gray-600" />
            )}
          </button>
        )}
        {collapsible && (
          <button
            onClick={handleToggleCollapse}
            className="w-7 h-7 rounded-md bg-white border border-gray-300 hover:bg-gray-50 hover:border-blue-400 flex items-center justify-center shadow-sm transition-all"
            title="Collapse panel"
          >
            <CollapseIcon size={14} className="text-gray-600" />
          </button>
        )}
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {children}
      </div>

      {/* Resize Handle */}
      {resizable && position !== "right" && (
        <div
          className="absolute top-0 right-0 w-1 h-full cursor-ew-resize hover:bg-blue-500 transition-colors group"
          onMouseDown={(e) => {
            e.preventDefault();
            const startX = e.clientX;
            const startWidth = parseInt(width);

            const handleMouseMove = (e: MouseEvent) => {
              const delta = e.clientX - startX;
              const newWidth = Math.max(
                parseInt(minWidth),
                Math.min(parseInt(maxWidth), startWidth + delta)
              );
              setWidth(`${newWidth}px`);
            };

            const handleMouseUp = () => {
              document.removeEventListener("mousemove", handleMouseMove);
              document.removeEventListener("mouseup", handleMouseUp);
            };

            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
          }}
        >
          <div className="absolute inset-y-0 -left-1 w-3 flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="w-1 h-8 bg-blue-500 rounded-full"></div>
          </div>
        </div>
      )}
    </div>
  );
}
