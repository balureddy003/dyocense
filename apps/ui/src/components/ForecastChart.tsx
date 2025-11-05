import { TrendingUp, TrendingDown, Info } from "lucide-react";

interface ForecastData {
  week: string;
  predicted: number;
  low?: number;
  high?: number;
  actual?: number;
}

interface ForecastChartProps {
  data: ForecastData[];
  title?: string;
  unit?: string;
}

export const ForecastChart = ({ 
  data, 
  title = "Sales Forecast", 
  unit = "units" 
}: ForecastChartProps) => {
  if (!data || data.length === 0) {
    return null;
  }

  // Calculate max value for scaling
  const maxValue = Math.max(
    ...data.map((d) => Math.max(d.predicted, d.high || d.predicted, d.actual || 0))
  );
  const minValue = Math.min(
    ...data.map((d) => Math.min(d.low || d.predicted, d.predicted))
  );
  const range = maxValue - minValue;
  const padding = range * 0.1;
  const chartMax = maxValue + padding;
  const chartMin = Math.max(0, minValue - padding);

  // Calculate scale
  const getY = (value: number) => {
    return ((chartMax - value) / (chartMax - chartMin)) * 100;
  };

  // Generate SVG path for line
  const generatePath = (values: number[]) => {
    return values
      .map((value, index) => {
        const x = (index / (data.length - 1)) * 100;
        const y = getY(value);
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  };

  const predictedPath = generatePath(data.map((d) => d.predicted));
  const actualPath = data.some((d) => d.actual)
    ? generatePath(data.filter((d) => d.actual).map((d) => d.actual!))
    : null;

  // Calculate trend
  const firstValue = data[0].predicted;
  const lastValue = data[data.length - 1].predicted;
  const trend = lastValue > firstValue ? "up" : lastValue < firstValue ? "down" : "stable";
  const trendPercent = ((lastValue - firstValue) / firstValue) * 100;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            {title}
            <button className="text-gray-400 hover:text-gray-600 transition">
              <Info size={16} />
            </button>
          </h3>
          <p className="text-xs text-gray-500 mt-1">Next {data.length} weeks</p>
        </div>
        <div
          className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-semibold ${
            trend === "up"
              ? "bg-green-50 text-green-700"
              : trend === "down"
              ? "bg-red-50 text-red-700"
              : "bg-gray-50 text-gray-700"
          }`}
        >
          {trend === "up" ? (
            <TrendingUp size={16} />
          ) : trend === "down" ? (
            <TrendingDown size={16} />
          ) : null}
          {Math.abs(trendPercent).toFixed(1)}%
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-48 bg-gray-50 rounded-xl p-4">
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          {/* Range area (high to low) */}
          {data.some((d) => d.high && d.low) && (
            <polygon
              points={data
                .map((d, i) => {
                  const x = (i / (data.length - 1)) * 100;
                  const yHigh = getY(d.high || d.predicted);
                  return `${x},${yHigh}`;
                })
                .concat(
                  data
                    .reverse()
                    .map((d, i) => {
                      const x = ((data.length - 1 - i) / (data.length - 1)) * 100;
                      const yLow = getY(d.low || d.predicted);
                      return `${x},${yLow}`;
                    })
                )
                .join(" ")}
              fill="rgb(59, 130, 246)"
              opacity="0.1"
            />
          )}

          {/* Predicted line */}
          <path
            d={predictedPath}
            fill="none"
            stroke="rgb(59, 130, 246)"
            strokeWidth="0.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />

          {/* Actual line (if available) */}
          {actualPath && (
            <path
              d={actualPath}
              fill="none"
              stroke="rgb(34, 197, 94)"
              strokeWidth="0.5"
              strokeDasharray="2,2"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          )}

          {/* Data points */}
          {data.map((d, i) => (
            <circle
              key={i}
              cx={(i / (data.length - 1)) * 100}
              cy={getY(d.predicted)}
              r="1"
              fill="rgb(59, 130, 246)"
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>

        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-gray-500 pr-2">
          <span>{Math.round(chartMax).toLocaleString()}</span>
          <span>{Math.round((chartMax + chartMin) / 2).toLocaleString()}</span>
          <span>{Math.round(chartMin).toLocaleString()}</span>
        </div>
      </div>

      {/* X-axis (weeks) */}
      <div className="flex justify-between text-xs text-gray-500">
        {data.map((d, i) => (
          <span key={i} className={i % 2 === 0 ? "" : "opacity-0"}>
            {d.week}
          </span>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-primary rounded"></div>
          <span className="text-gray-600">Expected Sales</span>
        </div>
        {data.some((d) => d.high && d.low) && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-3 bg-primary/10 rounded"></div>
            <span className="text-gray-600">Range (Low to High)</span>
          </div>
        )}
        {actualPath && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-green-500 rounded border-dashed border border-green-500"></div>
            <span className="text-gray-600">Actual Sales</span>
          </div>
        )}
      </div>
    </div>
  );
};
