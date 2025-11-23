/**
 * TopicAgenda Component
 * Displays topics in an agenda/list format with keywords and context
 * Allows users to navigate through the conversation topics
 */

import React, { useState } from 'react';
import { List, Hash, ChevronRight, Search } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const TopicAgenda: React.FC = () => {
  const { topics } = useApp();
  const [selectedTopicIndex, setSelectedTopicIndex] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  if (!topics || topics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-12 text-center">
        <List className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No topics detected yet</p>
        <p className="text-sm text-gray-400 mt-1">Upload an audio file to see topics</p>
      </div>
    );
  }

  // Filter topics based on search query
  const filteredTopics = topics.filter(topic =>
    topic.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
    topic.keywords.some(kw => kw.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <List className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Topic Agenda</h2>
          </div>
          <span className="text-sm font-medium text-gray-600">
            {topics.length} topic{topics.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search topics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Topics List */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {filteredTopics.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No topics match your search
          </div>
        ) : (
          filteredTopics.map((topic, index) => {
            const actualIndex = topics.findIndex(t => t === topic);
            const isSelected = selectedTopicIndex === actualIndex;

            return (
              <div
                key={actualIndex}
                className={`
                  p-4 cursor-pointer transition-all duration-200
                  ${isSelected ? 'bg-primary-50 border-l-4 border-primary-600' : 'hover:bg-gray-50 border-l-4 border-transparent'}
                `}
                onClick={() => setSelectedTopicIndex(isSelected ? null : actualIndex)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Topic Number and Title */}
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-700 text-xs font-semibold flex items-center justify-center">
                        {actualIndex + 1}
                      </span>
                      <h3 className={`font-semibold ${isSelected ? 'text-primary-900' : 'text-gray-900'}`}>
                        {topic.topic}
                      </h3>
                    </div>

                    {/* Keywords */}
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {topic.keywords.map((keyword, kidx) => (
                        <span
                          key={kidx}
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            isSelected
                              ? 'bg-primary-100 text-primary-800'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          <Hash className="w-3 h-3 mr-0.5" />
                          {keyword}
                        </span>
                      ))}
                    </div>

                    {/* Expandable Context */}
                    {isSelected && (
                      <div className="mt-3 pt-3 border-t border-primary-200">
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {topic.text_sample}
                        </p>
                      </div>
                    )}
                  </div>

                  <ChevronRight
                    className={`w-5 h-5 flex-shrink-0 ml-2 transition-transform ${
                      isSelected ? 'rotate-90 text-primary-600' : 'text-gray-400'
                    }`}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer with navigation hint */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <p className="text-xs text-gray-500 text-center">
          Click on a topic to see more details
        </p>
      </div>
    </div>
  );
};
