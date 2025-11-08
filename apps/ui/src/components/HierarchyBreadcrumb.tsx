import React from "react";

export type HierarchyBreadcrumbProps = {
    tenantName?: string;
    projectName?: string;
    className?: string; // applied to wrapper span
    tenantClassName?: string;
    projectClassName?: string;
    separatorClassName?: string;
    showIcons?: boolean;
    separator?: React.ReactNode;
};

export function HierarchyBreadcrumb({
    tenantName,
    projectName,
    className,
    tenantClassName = "font-semibold text-gray-700",
    projectClassName = "font-semibold text-primary",
    separatorClassName = "text-gray-400",
    showIcons = true,
    separator,
}: HierarchyBreadcrumbProps) {
    if (!tenantName && !projectName) return null;

    const Separator = () => (
        <span className={separatorClassName}>
            {separator !== undefined ? separator : "→"}
        </span>
    );

    return (
        <span className={className}>
            {tenantName && (
                <>
                    <span className={tenantClassName}>{showIcons ? "📊 " : ""}{tenantName}</span>
                    {projectName && <Separator />}
                </>
            )}
            {projectName && (
                <span className={projectClassName}>{showIcons ? "📁 " : ""}{projectName}</span>
            )}
        </span>
    );
}
