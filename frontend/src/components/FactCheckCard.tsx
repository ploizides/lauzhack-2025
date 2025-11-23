/**
 * FactCheckCard Component
 * Displays individual fact-check results with verdict, confidence, and sources
 */

import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { FactCheck } from '../types';

interface FactCheckCardProps {
  factCheck: FactCheck;
}

export const FactCheckCard: React.FC<FactCheckCardProps> = ({ factCheck }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const verdictConfig = {
    SUPPORTED: {
      icon: CheckCircle2,
      color: 'green',
      label: 'Verified',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      iconColor: 'text-green-600',
    },
    REFUTED: {
      icon: XCircle,
      color: 'red',
      label: 'False',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-900',
      iconColor: 'text-red-600',
    },
    UNCERTAIN: {
      icon: HelpCircle,
      color: 'yellow',
      label: 'Uncertain',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-900',
      iconColor: 'text-yellow-600',
    },
  };

  const config = verdictConfig[factCheck.verdict];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border ${config.borderColor} ${config.bgColor} overflow-hidden`}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start space-x-3 mb-3">
          <Icon className={`w-6 h-6 ${config.iconColor} flex-shrink-0 mt-0.5`} />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-semibold ${config.textColor}`}>
                {config.label}
              </span>
              <span className={`text-xs font-medium ${config.textColor}`}>
                {(factCheck.confidence * 100).toFixed(0)}% confident
              </span>
            </div>
            <p className="text-sm text-gray-900 font-medium">
              {factCheck.claim}
            </p>
          </div>
        </div>

        {/* Explanation */}
        <p className="text-sm text-gray-700 mb-3 pl-9">
          {factCheck.explanation}
        </p>

        {/* Key Facts */}
        {factCheck.key_facts && factCheck.key_facts.length > 0 && (
          <div className="pl-9 mb-3">
            <p className="text-xs font-semibold text-gray-700 mb-1">Key Facts:</p>
            <ul className="text-xs text-gray-600 space-y-1">
              {factCheck.key_facts.slice(0, 3).map((fact, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Expandable Sources Section */}
        {factCheck.sources && factCheck.sources.length > 0 && (
          <div className="pl-9">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-1 text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              <span>
                {isExpanded ? 'Hide' : 'Show'} {factCheck.sources.length} source{factCheck.sources.length !== 1 ? 's' : ''}
              </span>
            </button>

            {isExpanded && (
              <div className="mt-2 space-y-1">
                {factCheck.sources.map((source, idx) => (
                  <a
                    key={idx}
                    href={source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-800 hover:underline"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate">{source}</span>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
