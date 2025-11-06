/**
 * Getting Started Guide - Onboarding for new users
 * Shows clear steps to get value from Dyocense
 */

import { Database, MessageSquare, Target, TrendingUp, ArrowRight, Sparkles } from "lucide-react";

type GettingStartedGuideProps = {
  onConnectData: () => void;
  onStartChat: () => void;
  hasConnectors: boolean;
};

export function GettingStartedGuide({
  onConnectData,
  onStartChat,
  hasConnectors,
}: GettingStartedGuideProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-4xl w-full">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4">
            <Sparkles className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Welcome to Your AI Business Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get data-driven, measurable plans in minutes. I'll help you achieve your business goals with personalized strategies.
          </p>
        </div>

        {/* Quick Start Steps */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Step 1: Connect Data */}
          <div className={`bg-white rounded-xl border-2 p-6 transition-all ${
            !hasConnectors 
              ? "border-blue-500 shadow-lg shadow-blue-100" 
              : "border-green-500"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                hasConnectors ? "bg-green-100" : "bg-blue-100"
              }`}>
                <Database className={hasConnectors ? "text-green-600" : "text-blue-600"} size={24} />
              </div>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                hasConnectors 
                  ? "bg-green-100 text-green-700" 
                  : "bg-blue-100 text-blue-700"
              }`}>
                {hasConnectors ? "✓ Done" : "Step 1"}
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Connect Your Data</h3>
            <p className="text-sm text-gray-600 mb-4">
              {hasConnectors 
                ? "Great! Your data sources are connected."
                : "Link Xero, Shopify, Google Drive, or other business tools for personalized insights."
              }
            </p>
            {!hasConnectors ? (
              <button
                onClick={onConnectData}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                Connect Data
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={onConnectData}
                className="w-full border border-gray-200 text-gray-700 px-4 py-2 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Manage Connectors
              </button>
            )}
          </div>

          {/* Step 2: Chat with AI */}
          <div className={`bg-white rounded-xl border-2 p-6 transition-all ${
            hasConnectors 
              ? "border-blue-500 shadow-lg shadow-blue-100" 
              : "border-gray-200"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                hasConnectors ? "bg-blue-100" : "bg-gray-100"
              }`}>
                <MessageSquare className={hasConnectors ? "text-blue-600" : "text-gray-400"} size={24} />
              </div>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                hasConnectors 
                  ? "bg-blue-100 text-blue-700" 
                  : "bg-gray-100 text-gray-500"
              }`}>
                Step 2
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Tell Me Your Goal</h3>
            <p className="text-sm text-gray-600 mb-4">
              Share what you want to achieve: reduce costs, increase revenue, improve efficiency, or any business goal.
            </p>
            <button
              onClick={onStartChat}
              disabled={!hasConnectors}
              className={`w-full px-4 py-2 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2 ${
                hasConnectors
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-gray-100 text-gray-400 cursor-not-allowed"
              }`}
            >
              Start Chatting
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Step 3: Get Your Plan */}
          <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <Target className="text-gray-400" size={24} />
              </div>
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-gray-100 text-gray-500">
                Step 3
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Execute & Track</h3>
            <p className="text-sm text-gray-600 mb-4">
              I'll create a step-by-step plan with measurable milestones. Track progress and adjust as you go.
            </p>
            <div className="w-full border border-gray-200 text-gray-400 px-4 py-2 rounded-lg font-semibold text-center">
              Coming soon...
            </div>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="text-blue-600" size={20} />
            What You'll Get
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Data-Driven Insights</p>
                <p className="text-xs text-gray-600">Based on your actual business data, not generic advice</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">SMART Goals</p>
                <p className="text-xs text-gray-600">Specific, Measurable, Achievable, Relevant, Time-bound</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Actionable Steps</p>
                <p className="text-xs text-gray-600">Clear tasks you can start working on today</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Progress Tracking</p>
                <p className="text-xs text-gray-600">Monitor KPIs and adjust your strategy in real-time</p>
              </div>
            </div>
          </div>
        </div>

        {/* Example Questions */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 mb-3">Not sure what to ask? Try these:</p>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              onClick={() => {
                onStartChat();
                // Could auto-populate the chat with this question
              }}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              💰 "Reduce operating costs by 15%"
            </button>
            <button
              onClick={() => {
                onStartChat();
              }}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              📈 "Increase monthly revenue by 20%"
            </button>
            <button
              onClick={() => {
                onStartChat();
              }}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              ⚡ "Improve cash flow cycle time"
            </button>
            <button
              onClick={() => {
                onStartChat();
              }}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              🎯 "Boost customer retention rate"
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
