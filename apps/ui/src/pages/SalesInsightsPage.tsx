import { SalesInsightsFlow } from "../components/SalesInsightsFlow";

export const SalesInsightsPage = () => {
    return (
        <div className="min-h-screen p-6 bg-bg">
            <h2 className="text-lg font-semibold mb-4">Sales Insights (Beta)</h2>
            <SalesInsightsFlow />
        </div>
    );
};

export default SalesInsightsPage;
