import { Header } from "../components/Header";
import { Hero } from "../components/Hero";
import { SidebarAI } from "../components/SidebarAI";
import { ItineraryTabs } from "../components/ItineraryTabs";
import { MapPanel } from "../components/MapPanel";
import { FloatingCTA } from "../components/FloatingCTA";

export default function App() {
  return (
    <div className="h-full flex flex-col bg-bg text-gray-900">
      <Header />
      <Hero />
      <div className="flex-1 flex flex-col lg:flex-row">
        <div className="flex flex-1 min-h-0">
          <ItineraryTabs />
          <MapPanel />
        </div>
        <SidebarAI />
      </div>
      <FloatingCTA />
    </div>
  );
}
