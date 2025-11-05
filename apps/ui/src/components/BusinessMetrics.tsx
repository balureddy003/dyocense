import { TrendingUp, TrendingDown, DollarSign, Package, AlertTriangle, CheckCircle } from "lucide-react";

interface Metric {
  label: string;
  value: string | number;
  change?: number;
  trend?: "up" | "down" | "neutral";
  icon: "money" | "inventory" | "risk" | "service";
  status?: "good" | "warning" | "danger";
}

interface BusinessMetricsProps {
  metrics?: Metric[];
}

const defaultMetrics: Metric[] = [
  {
    label: "Estimated Monthly Savings",
    value: "$1,240",
    change: 18,
    trend: "up",
    icon: "money",
    status: "good",
  },
  {
    label: "Current Stock Level",
    value: "87%",
    change: -5,
    trend: "down",
    icon: "inventory",
    status: "good",
  },
  {
    label: "Stock-Out Risk",
    value: "Low",
    trend: "neutral",
    icon: "risk",
    status: "good",
  },
  {
    label: "Service Level",
    value: "94%",
    change: 3,
    trend: "up",
    icon: "service",
    status: "good",
  },
];

export const BusinessMetrics = ({ metrics = defaultMetrics }: BusinessMetricsProps) => {
  const getIcon = (icon: string) => {
    switch (icon) {
      case "money":
        return DollarSign;
      case "inventory":
        return Package;
      case "risk":
        return AlertTriangle;
      case "service":
        return CheckCircle;
      default:
        return Package;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "good":
        return "bg-green-50 border-green-200 text-green-700";
      case "warning":
        return "bg-orange-50 border-orange-200 text-orange-700";
      case "danger":
        return "bg-red-50 border-red-200 text-red-700";
      default:
        return "bg-blue-50 border-blue-200 text-blue-700";
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => {
        const Icon = getIcon(metric.icon);
        const statusColor = getStatusColor(metric.status);

        return (
          <div
            key={index}
            className={`rounded-xl border p-5 transition-all hover:shadow-md ${statusColor}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                metric.status === "good" ? "bg-green-100" :
                metric.status === "warning" ? "bg-orange-100" :
                metric.status === "danger" ? "bg-red-100" :
                "bg-blue-100"
              }`}>
                <Icon size={20} className={
                  metric.status === "good" ? "text-green-600" :
                  metric.status === "warning" ? "text-orange-600" :
                  metric.status === "danger" ? "text-red-600" :
                  "text-blue-600"
                } />
              </div>
              {metric.change !== undefined && (
                <div
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                    metric.trend === "up"
                      ? "bg-green-100 text-green-700"
                      : metric.trend === "down"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {metric.trend === "up" ? (
                    <TrendingUp size={12} />
                  ) : metric.trend === "down" ? (
                    <TrendingDown size={12} />
                  ) : null}
                  {Math.abs(metric.change)}%
                </div>
              )}
            </div>
            <div>
              <p className="text-xs font-medium mb-1 opacity-90">
                {metric.label}
              </p>
              <p className="text-2xl font-bold">
                {metric.value}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
