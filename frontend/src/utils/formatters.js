/**
 * Utility functions for formatting data
 */

/**
 * Format ISO timestamp to HH:MM:SS
 */
export const formatTimestamp = (isoString) => {
  if (!isoString) return '00:00:00';

  try {
    const date = new Date(isoString);
    const hours = String(date.getHours()).padStart(2, '0');
    const mins = String(date.getMinutes()).padStart(2, '0');
    const secs = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${mins}:${secs}`;
  } catch (error) {
    return '00:00:00';
  }
};

/**
 * Format seconds to MM:SS
 */
export const formatTime = (seconds) => {
  if (!seconds || seconds < 0) return '00:00';

  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

/**
 * Extract domain from URL
 */
export const extractDomain = (url) => {
  try {
    const domain = new URL(url).hostname;
    return domain.replace('www.', '');
  } catch (error) {
    return '??';
  }
};

/**
 * Extract episode name from filename
 */
export const extractEpisodeName = (filename) => {
  if (!filename) return 'Unknown';
  return filename.replace('.wav', '').replace('.mp3', '');
};

/**
 * Calculate current time from progress and duration
 */
export const calculateCurrentTime = (progress, duration) => {
  if (!progress || !duration) return 0;
  return (progress / 100) * duration;
};
