/**
 * Industry Selector - Fast vertical selection for SMBs
 */

import { Store, ShoppingBag, Briefcase, Coffee, Wrench, Package } from "lucide-react";

export type Industry = "restaurant" | "retail" | "services" | "cpg" | "logistics" | "other";

type IndustrySelectorProps = {
  selected?: Industry;
  onSelect: (industry: Industry) => void;
};

const industries: Array<{
  id: Industry;
  label: string;
  icon: React.ReactNode;
  description: string;
}> = [
  {
    id: "restaurant",
    label: "Restaurant & Café",
    icon: <Coffee size={24} />,
    description: "Food costs, staffing, menu optimization",
  },
  {
    id: "retail",
    label: "Retail Store",
    icon: <ShoppingBag size={24} />,
    description: "Inventory, sales, staffing, markdowns",
  },
  {
    id: "services",
    label: "Service Business",
    icon: <Briefcase size={24} />,
    description: "Bookings, invoices, cash flow, utilization",
  },
  {
    id: "cpg",
    label: "Manufacturing",
    icon: <Package size={24} />,
    description: "Production, materials, distribution",
  },
  {
    id: "logistics",
    label: "Logistics",
    icon: <Wrench size={24} />,
    description: "Routes, warehousing, delivery",
  },
  {
    id: "other",
    label: "Other",
    icon: <Store size={24} />,
    description: "General business planning",
  },
];

export function IndustrySelector({ selected, onSelect }: IndustrySelectorProps) {
  return (
    <div className="space-y-3">
      <div className="text-center mb-4">
        <h3 className="text-lg font-bold text-gray-900 mb-1">What kind of business do you run?</h3>
        <p className="text-sm text-gray-600">Don't worry, you can change this later!</p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {industries.map((industry) => (
          <button
            key={industry.id}
            onClick={() => onSelect(industry.id)}
            className={`p-4 rounded-xl border-2 text-left transition-all hover:shadow-md ${
              selected === industry.id
                ? "border-blue-500 bg-blue-50 shadow-lg"
                : "border-gray-200 bg-white hover:border-blue-300"
            }`}
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-2 ${
              selected === industry.id ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"
            }`}>
              {industry.icon}
            </div>
            <div className="font-semibold text-sm text-gray-900 mb-1">{industry.label}</div>
            <div className="text-xs text-gray-600 line-clamp-2">{industry.description}</div>
            {selected === industry.id && (
              <div className="mt-2 text-xs font-semibold text-blue-600">✓ Selected</div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
