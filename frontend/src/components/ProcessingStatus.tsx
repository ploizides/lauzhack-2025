/**
 * ProcessingStatus Component
 * Shows the current processing stage with progress indicators
 */

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Upload, FileText, Brain, Search } from 'lucide-react';
import { useApp } from '../context/AppContext';

const stages = [
  { id: 'uploading', label: 'Uploading', icon: Upload },
  { id: 'transcribing', label: 'Transcribing', icon: FileText },
  { id: 'analyzing', label: 'Analyzing Topics', icon: Brain },
  { id: 'fact-checking', label: 'Fact-Checking', icon: Search },
];

export const ProcessingStatus: React.FC = () => {
  const { processingStage, uploadProgress, isProcessing } = useApp();

  if (processingStage === 'idle' || processingStage === 'complete') {
    return null;
  }

  if (processingStage === 'error') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <XCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-900">Processing Failed</h3>
            <p className="text-sm text-red-700">Please try again with a different file</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Processing Audio</h3>

      <div className="space-y-4">
        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const isActive = processingStage === stage.id;
          const isComplete = stages.findIndex(s => s.id === processingStage) > index;

          return (
            <div key={stage.id} className="flex items-center space-x-3">
              <div className={`
                flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                ${isComplete ? 'bg-green-100' : isActive ? 'bg-primary-100' : 'bg-gray-100'}
              `}>
                {isComplete ? (
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
                ) : (
                  <Icon className="w-5 h-5 text-gray-400" />
                )}
              </div>

              <div className="flex-1">
                <p className={`font-medium ${
                  isActive ? 'text-primary-900' : isComplete ? 'text-green-900' : 'text-gray-500'
                }`}>
                  {stage.label}
                </p>

                {isActive && stage.id === 'uploading' && (
                  <div className="mt-1">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{uploadProgress}%</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
