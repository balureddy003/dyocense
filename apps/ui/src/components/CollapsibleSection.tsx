import { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import clsx from "clsx";

interface CollapsibleSectionProps {
  id: string;
  title: string;
  description?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  collapsed: boolean;
  onToggle: (id: string) => void;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

export const CollapsibleSection = ({
  id,
  title,
  description,
  icon,
  actions,
  collapsed,
  onToggle,
  children,
  className,
  contentClassName,
}: CollapsibleSectionProps) => {
  const handleToggle = () => onToggle(id);

  return (
    <section className={clsx("bg-white rounded-2xl border border-gray-100 shadow-sm", className)}>
      <header className="flex items-start justify-between gap-3 px-5 py-4 border-b border-gray-100">
        <button
          type="button"
          onClick={handleToggle}
          className="flex items-start gap-3 flex-1 text-left group"
          aria-expanded={!collapsed}
          aria-controls={`${id}-body`}
        >
          <ChevronDown
            size={18}
            className={clsx(
              "mt-1 text-gray-400 transition-transform duration-150 ease-out group-hover:text-gray-500",
              collapsed ? "-rotate-90" : "rotate-0"
            )}
          />
          {icon && <span className="mt-0.5 text-primary">{icon}</span>}
          <div>
            <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{title}</h3>
            {description && <p className="text-xs text-gray-500 mt-1 leading-5">{description}</p>}
          </div>
        </button>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <div
        id={`${id}-body`}
        hidden={collapsed}
        className={clsx("px-5 py-4", contentClassName)}
      >
        {!collapsed && children}
      </div>
    </section>
  );
};
