import React, { useState, useEffect } from 'react';

const MediaDisplay = ({ selectedTopic, topicImages }) => {
  // Cache the current image URL to prevent flickering
  const [currentImageUrl, setCurrentImageUrl] = useState(null);
  const [currentTopicName, setCurrentTopicName] = useState(null);

  // Update cached image when selected topic or images change
  useEffect(() => {
    if (selectedTopic?.topic_id) {
      // Find image for selected topic
      const topicImage = topicImages.find(
        (img) => img.topic_id === selectedTopic.topic_id
      );

      // Only update if we found a new image URL
      if (topicImage && topicImage.image_url) {
        setCurrentImageUrl(topicImage.image_url);
        setCurrentTopicName(selectedTopic.topic);
      } else if (!currentImageUrl) {
        // If no cached image exists yet, update the topic name at least
        setCurrentTopicName(selectedTopic.topic);
      }
    }
  }, [selectedTopic, topicImages]);

  const hasImage = currentImageUrl !== null;

  return (
    <div className="media-container">
      {hasImage ? (
        <>
          <img
            src={currentImageUrl}
            alt={currentTopicName || 'Topic image'}
            className="media-image visible"
            onError={(e) => {
              // Hide image on error
              e.target.classList.remove('visible');
            }}
          />
          <div className="media-topic">{currentTopicName}</div>
        </>
      ) : (
        <div className="media-placeholder">
          &lt;MEDIA
          <br />
          PLACEHOLDER&gt;
        </div>
      )}
    </div>
  );
};

export default MediaDisplay;
