/**
 * Main App Component
 * Orchestrates the entire UI layout and component interaction
 */

import React, { useState } from 'react';
import { Brain, MessageSquare, CheckSquare } from 'lucide-react';
import { AppProvider, useApp } from './context/AppContext';
import { AudioUpload } from './components/AudioUpload';
import { ProcessingStatus } from './components/ProcessingStatus';
import { TopicAgenda } from './components/TopicAgenda';
import { TopicTimeline } from './components/TopicTimeline';
import { TranscriptView } from './components/TranscriptView';
import { FactCheckCard } from './components/FactCheckCard';

type ViewMode = 'agenda' | 'timeline';

const AppContent: React.FC = () => {
  const { factChecks, processingStage, summary, error } = useApp();
  const [viewMode, setViewMode] = useState<ViewMode>('agenda');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Podcast AI Assistant
                </h1>
                <p className="text-sm text-gray-600">
                  Real-time transcription, topic tracking, and fact-checking
                </p>
              </div>
            </div>

            {/* Summary Stats */}
            {summary && (
              <div className="hidden md:flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className="font-bold text-2xl text-primary-600">
                    {summary.total_topics}
                  </div>
                  <div className="text-gray-600">Topics</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-2xl text-green-600">
                    {summary.verified_claims}
                  </div>
                  <div className="text-gray-600">Verified</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-2xl text-red-600">
                    {summary.false_claims}
                  </div>
                  <div className="text-gray-600">False</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="mb-8">
          <AudioUpload />
        </div>

        {/* Processing Status */}
        {processingStage !== 'idle' && processingStage !== 'complete' && (
          <div className="mb-8">
            <ProcessingStatus />
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-semibold text-red-900 mb-1">Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Results Section */}
        {processingStage === 'complete' && (
          <div className="space-y-8">
            {/* Topics Section with View Toggle */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
                  <MessageSquare className="w-6 h-6 text-primary-600" />
                  <span>Conversation Topics</span>
                </h2>

                {/* View Mode Toggle */}
                <div className="inline-flex rounded-lg border border-gray-300 bg-white p-1">
                  <button
                    onClick={() => setViewMode('agenda')}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      viewMode === 'agenda'
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    Agenda View
                  </button>
                  <button
                    onClick={() => setViewMode('timeline')}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      viewMode === 'timeline'
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    Timeline View
                  </button>
                </div>
              </div>

              {viewMode === 'agenda' ? <TopicAgenda /> : <TopicTimeline />}
            </div>

            {/* Two Column Layout for Transcript and Fact-Checks */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Transcript */}
              <div>
                <TranscriptView />
              </div>

              {/* Fact-Checks */}
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                  <CheckSquare className="w-6 h-6 text-primary-600" />
                  <span>Fact-Checks</span>
                </h2>

                {factChecks && factChecks.length > 0 ? (
                  <div className="space-y-4">
                    {factChecks.map((factCheck, index) => (
                      <FactCheckCard key={index} factCheck={factCheck} />
                    ))}
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow-md border border-gray-200 p-12 text-center">
                    <CheckSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No factual claims detected</p>
                    <p className="text-sm text-gray-400 mt-1">
                      The transcript didn't contain verifiable claims
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {processingStage === 'idle' && (
          <div className="text-center py-16">
            <Brain className="w-20 h-20 text-gray-300 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Get Started
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Upload an audio file to analyze the conversation, track topics,
              and verify factual claims automatically.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Podcast AI Assistant • Built for LauzHack 2025
          </p>
        </div>
      </footer>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;
