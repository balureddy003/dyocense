/**
 * Getting Started Guide - Onboarding for new users
 * Shows clear steps to get value from Dyocense
 */

import { Database, MessageSquare, Target, TrendingUp, ArrowRight, Sparkles } from "lucide-react";
import { Industry } from "./IndustrySelector";

type GettingStartedGuideProps = {
  onConnectData: () => void;
  onStartChat: () => void;
  hasConnectors: boolean;
  selectedIndustry?: Industry;
};

export function GettingStartedGuide({
  onConnectData,
  onStartChat,
  hasConnectors,
  selectedIndustry,
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
            Ready to grow your business?
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Just tell us your goal. We'll give you a clear plan with weekly tasks and show you the potential impact.
          </p>
        </div>

        {/* Quick Start Steps */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Step 1: Set Your Goal */}
          <div className="bg-white rounded-xl border-2 border-blue-500 shadow-lg shadow-blue-100 p-6 transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-blue-100">
                <MessageSquare className="text-blue-600" size={24} />
              </div>
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                Step 1
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Set Your Goal</h3>
            <p className="text-sm text-gray-600 mb-4">
              What do you want to achieve this month or quarter? Be specific!
            </p>
            <button
              onClick={onStartChat}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              Start Now
              <ArrowRight size={16} />
            </button>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Takes less than 2 minutes
            </p>
          </div>

          {/* Step 2: Connect Data (Optional) */}
          <div className={`bg-white rounded-xl border-2 p-6 transition-all ${
            hasConnectors 
              ? "border-green-500" 
              : "border-gray-200"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                hasConnectors ? "bg-green-100" : "bg-gray-100"
              }`}>
                <Database className={hasConnectors ? "text-green-600" : "text-gray-400"} size={24} />
              </div>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                hasConnectors 
                  ? "bg-green-100 text-green-700" 
                  : "bg-gray-100 text-gray-500"
              }`}>
                {hasConnectors ? "✓ Done" : "Step 2"}
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Connect Your Tools</h3>
            <p className="text-sm text-gray-600 mb-4">
              {hasConnectors 
                ? "✓ Your tools are connected!"
                : "Optional: Connect QuickBooks, Shopify, or Square to get personalized insights."
              }
            </p>
            {!hasConnectors ? (
              <>
                <button
                  onClick={onConnectData}
                  className="w-full border border-blue-600 text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
                >
                  Connect Data
                  <ArrowRight size={16} />
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  I'll do this later
                </p>
              </>
            ) : (
              <button
                onClick={onConnectData}
                className="w-full border border-gray-200 text-gray-700 px-4 py-2 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Manage Connectors
              </button>
            )}
          </div>

          {/* Step 3: Execute & Track */}
          <div className="bg-white rounded-xl border-2 border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <Target className="text-gray-400" size={24} />
              </div>
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-gray-100 text-gray-500">
                Step 3
              </span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Get Your Plan & Track Progress</h3>
            <p className="text-sm text-gray-600 mb-4">
              See your weekly tasks with estimated impact. Track what's working and adjust as you go.
            </p>
            <div className="w-full border border-gray-200 text-gray-400 px-4 py-2 rounded-lg font-semibold text-center text-sm">
              After Step 1
            </div>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="text-blue-600" size={20} />
            What you'll get (in plain English!)
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Week-by-week to-do list</p>
                <p className="text-xs text-gray-600">Clear tasks you can start today</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">See the dollar impact</p>
                <p className="text-xs text-gray-600">Know what each action could save or earn</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Made for your business</p>
                <p className="text-xs text-gray-600">Based on your industry and size</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                ✓
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Real-time progress tracking</p>
                <p className="text-xs text-gray-600">See what's working, adjust what's not</p>
              </div>
            </div>
          </div>
        </div>

        {/* Example Questions */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 mb-3">Try one of these popular goals:</p>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              onClick={onStartChat}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              💰 Cut food costs 10%
            </button>
            <button
              onClick={onStartChat}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              📈 Boost sales 15%
            </button>
            <button
              onClick={onStartChat}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              ⚡ Get paid faster
            </button>
            <button
              onClick={onStartChat}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
              🎯 Cut labor costs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
