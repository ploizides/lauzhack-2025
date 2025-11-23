import React from 'react';
import { extractEpisodeName, formatTime, calculateCurrentTime } from '../utils/formatters';

const EpisodeBar = ({ metadata, progress, isStreaming }) => {
  const episodeName = metadata ? extractEpisodeName(metadata.filename) : 'Waiting...';
  const currentTime = metadata
    ? calculateCurrentTime(progress, metadata.duration_seconds)
    : 0;

  return (
    <div className="episode-container">
      <div className="episode-info">
        <div className="episode-title">
          Episode <span className="episode-number">42</span> - "{episodeName}"
        </div>
        <div className="episode-time">Time: {formatTime(currentTime)}</div>
      </div>

      <div className={`waveform ${isStreaming ? 'active' : ''}`}>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
      </div>
    </div>
  );
};

export default EpisodeBar;
