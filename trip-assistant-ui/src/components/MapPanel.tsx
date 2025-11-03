import { Globe } from "lucide-react";

export const MapPanel = () => (
  <aside className="hidden xl:flex w-[360px] bg-white border-l flex-col">
    <div className="p-4 border-b flex items-center gap-2 text-primary font-semibold">
      <Globe size={18} /> Scenario map
    </div>
    <div className="flex-1 flex items-center justify-center text-sm text-gray-500 p-6">
      Live network view coming soon. Plug in a Mapbox token to render route impacts.
    </div>
  </aside>
);
