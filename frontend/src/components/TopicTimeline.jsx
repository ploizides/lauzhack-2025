import React, { useEffect, useRef } from 'react';
import { formatTimestamp } from '../utils/formatters';

const TopicTimeline = ({
  topics,
  progress,
  selectedTopicId,
  onTopicSelect,
  isStreaming,
  onStart,
  onStop,
  isLoading,
}) => {
  const scrollRef = useRef(null);

  // Auto-scroll to latest topic
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = scrollRef.current.scrollWidth;
    }
  }, [topics]);

  return (
    <div className="timeline-container">
      <div className="timeline-header">
        <div className="timeline-title">TOPIC TIMELINE</div>
        <div className="controls">
          <button
            className="btn btn-start"
            onClick={onStart}
            disabled={isStreaming || isLoading}
          >
            {isLoading ? 'Starting...' : 'Start'}
          </button>
          <button
            className="btn btn-stop"
            onClick={onStop}
            disabled={!isStreaming || isLoading}
          >
            {isLoading ? 'Stopping...' : 'Stop'}
          </button>
        </div>
      </div>

      <div className="timeline-divider"></div>

      <div className="timeline-scroll" ref={scrollRef}>
        <div className="timeline-flow">
          {topics.length === 0 ? (
            <div className="loading">Click Start to begin...</div>
          ) : (
            topics.map((topic, index) => (
              <React.Fragment key={topic.topic_id}>
                <div className="topic-item">
                  <button
                    className={`topic-badge ${
                      topic.topic_id === selectedTopicId ? 'active' : ''
                    }`}
                    onClick={() => onTopicSelect(topic.topic_id)}
                  >
                    {topic.topic}
                  </button>
                  <div className="topic-timestamp">
                    {formatTimestamp(topic.timestamp)}
                  </div>
                </div>
                {index < topics.length - 1 && (
                  <div className="topic-arrow">→</div>
                )}
              </React.Fragment>
            ))
          )}
        </div>
      </div>

      <div className="progress-container">
        <div
          className="progress-fill"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
    </div>
  );
};

export default TopicTimeline;
