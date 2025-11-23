/**
 * TranscriptView Component
 * Displays the full transcript with word count and stats
 */

import React, { useState } from 'react';
import { FileText, Copy, Check } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const TranscriptView: React.FC = () => {
  const { transcript } = useApp();
  const [copied, setCopied] = useState(false);

  if (!transcript) {
    return null;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(transcript.full_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Transcript</h2>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-green-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>

        {/* Stats */}
        <div className="flex items-center space-x-6 mt-3 text-sm text-gray-600">
          <div>
            <span className="font-medium">{transcript.word_count.toLocaleString()}</span> words
          </div>
          <div>
            <span className="font-medium">{transcript.paragraph_count}</span> paragraphs
          </div>
          <div>
            <span className="font-medium">
              {Math.ceil(transcript.word_count / 150)}
            </span> min read
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 max-h-96 overflow-y-auto">
        <div className="prose prose-sm max-w-none">
          {transcript.full_text.split('\n\n').map((paragraph, idx) => (
            <p key={idx} className="text-gray-700 leading-relaxed mb-4">
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
};
