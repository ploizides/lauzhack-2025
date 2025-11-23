import React, { useState, useEffect } from 'react';
import TopicTimeline from './components/TopicTimeline';
import MediaDisplay from './components/MediaDisplay';
import FactCheckPanel from './components/FactCheckPanel';
import EpisodeBar from './components/EpisodeBar';
import useStreamData from './hooks/useStreamData';
import './App.css';

function App() {
  const {
    streamData,
    isStreaming,
    isLoading,
    error,
    startStream,
    stopStream,
  } = useStreamData();

  const [selectedTopicId, setSelectedTopicId] = useState(null);

  // Auto-select latest topic when new topics arrive
  useEffect(() => {
    if (streamData.topics && streamData.topics.length > 0) {
      const latestTopic = streamData.topics[streamData.topics.length - 1];
      setSelectedTopicId(latestTopic.topic_id);
    }
  }, [streamData.topics]);

  // Find selected topic object
  const selectedTopic = streamData.topics.find(
    (t) => t.topic_id === selectedTopicId
  );

  return (
    <div className="app-container">
      {/* Logo */}
      <div className="logo">
        <div className="logo-text">AMPLIFY</div>
        <div className="logo-subtitle">Real-Time Fact Checking</div>
      </div>

      {/* Error Display */}
      {error && (
        <div
          className="error-message"
          style={{
            position: 'absolute',
            top: '250px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
          }}
        >
          Error: {error}
        </div>
      )}

      {/* Topic Timeline */}
      <TopicTimeline
        topics={streamData.topics}
        progress={streamData.progress}
        selectedTopicId={selectedTopicId}
        onTopicSelect={setSelectedTopicId}
        isStreaming={isStreaming}
        onStart={startStream}
        onStop={stopStream}
        isLoading={isLoading}
      />

      {/* Media Display */}
      <MediaDisplay
        selectedTopic={selectedTopic}
        topicImages={streamData.topic_images}
      />

      {/* Fact-Check Panel */}
      <FactCheckPanel
        factChecks={streamData.fact_checks}
        factVerdicts={streamData.fact_verdicts}
      />

      {/* Episode Bar */}
      <EpisodeBar
        metadata={streamData.metadata}
        progress={streamData.progress}
        isStreaming={isStreaming}
      />
    </div>
  );
}

export default App;
