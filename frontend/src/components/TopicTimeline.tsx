/**
 * TopicTimeline Component
 * Displays topics in a vertical timeline format
 * Allows users to visualize the conversation flow chronologically
 */

import React, { useState } from 'react';
import { Clock, Hash, Circle } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const TopicTimeline: React.FC = () => {
  const { topics } = useApp();
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!topics || topics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-12 text-center">
        <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No timeline available</p>
        <p className="text-sm text-gray-400 mt-1">Topics will appear here as they're detected</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Clock className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Topic Timeline</h2>
          </div>
          <span className="text-sm text-gray-600">
            Conversation Flow
          </span>
        </div>
      </div>

      {/* Timeline */}
      <div className="p-6 max-h-96 overflow-y-auto">
        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-4 top-3 bottom-3 w-0.5 bg-gradient-to-b from-primary-500 via-primary-300 to-primary-100" />

          {/* Timeline Items */}
          <div className="space-y-6">
            {topics.map((topic, index) => {
              const isFirst = index === 0;
              const isLast = index === topics.length - 1;
              const isHovered = hoveredIndex === index;

              return (
                <div
                  key={index}
                  className="relative pl-12"
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  {/* Timeline Node */}
                  <div
                    className={`
                      absolute left-0 w-8 h-8 rounded-full border-4 border-white
                      flex items-center justify-center transition-all duration-200
                      ${isHovered
                        ? 'bg-primary-600 scale-125 shadow-lg'
                        : isFirst
                        ? 'bg-primary-500'
                        : isLast
                        ? 'bg-primary-400'
                        : 'bg-primary-300'
                      }
                    `}
                  >
                    {isFirst ? (
                      <Circle className="w-3 h-3 text-white fill-white" />
                    ) : (
                      <span className="text-xs font-bold text-white">{index + 1}</span>
                    )}
                  </div>

                  {/* Content Card */}
                  <div
                    className={`
                      bg-white border rounded-lg p-4 transition-all duration-200
                      ${isHovered
                        ? 'border-primary-400 shadow-md scale-[1.02]'
                        : 'border-gray-200 shadow-sm'
                      }
                    `}
                  >
                    {/* Topic Title */}
                    <h3 className={`font-semibold mb-2 ${
                      isHovered ? 'text-primary-900' : 'text-gray-900'
                    }`}>
                      {topic.topic}
                    </h3>

                    {/* Keywords */}
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {topic.keywords.slice(0, 5).map((keyword, kidx) => (
                        <span
                          key={kidx}
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            isHovered
                              ? 'bg-primary-100 text-primary-800'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          <Hash className="w-3 h-3 mr-0.5" />
                          {keyword}
                        </span>
                      ))}
                      {topic.keywords.length > 5 && (
                        <span className="text-xs text-gray-400">
                          +{topic.keywords.length - 5} more
                        </span>
                      )}
                    </div>

                    {/* Context Preview */}
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {topic.text_sample}
                    </p>

                    {/* Position Indicator */}
                    <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                      <span className="text-xs text-gray-500">
                        {isFirst && 'Opening topic'}
                        {isLast && !isFirst && 'Latest topic'}
                        {!isFirst && !isLast && `Topic ${index + 1} of ${topics.length}`}
                      </span>
                      {/* TODO: Add timestamp when available */}
                      {topic.timestamp && (
                        <span className="text-xs text-gray-400">
                          {new Date(topic.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* End Marker */}
          <div className="relative pl-12 mt-6">
            <div className="absolute left-0 w-8 h-8 rounded-full border-4 border-white bg-gray-300 flex items-center justify-center">
              <Circle className="w-3 h-3 text-white" />
            </div>
            <div className="text-sm text-gray-500 italic">
              End of conversation
            </div>
          </div>
        </div>
      </div>

      {/* TODO: Add progress indicator for real-time streaming */}
      {/* <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <p className="text-xs text-gray-500 text-center">
          Timeline updates automatically as new topics are detected
        </p>
      </div> */}
    </div>
  );
};
