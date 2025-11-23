import { useState, useEffect, useCallback, useRef } from 'react';
import apiService from '../services/apiService';

/**
 * Custom hook for managing stream data with polling
 */
const useStreamData = () => {
  const [streamData, setStreamData] = useState({
    status: 'idle',
    progress: 0,
    topics: [],
    topic_path: [],
    topic_images: [],
    edges: [],
    fact_checks: [],
    fact_verdicts: {
      SUPPORTED: 0,
      CONTRADICTED: 0,
      UNCERTAIN: 0,
    },
    metadata: null,
    transcripts: [],
  });

  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const pollingIntervalRef = useRef(null);

  /**
   * Fetch results from API
   */
  const fetchResults = useCallback(async () => {
    try {
      const data = await apiService.getResults();
      setStreamData(data);

      // Auto-stop if completed
      if (data.status === 'completed' && isStreaming) {
        stopStream();
      }

      setError(null);
    } catch (err) {
      console.error('Error fetching results:', err);
      setError(err.message);
    }
  }, [isStreaming]);

  /**
   * Start polling
   */
  const startPolling = useCallback(() => {
    // Immediate fetch
    fetchResults();

    // Poll every 1 second
    pollingIntervalRef.current = setInterval(() => {
      fetchResults();
    }, 1000);
  }, [fetchResults]);

  /**
   * Stop polling
   */
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  /**
   * Start stream
   */
  const startStream = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await apiService.startStream();
      setIsStreaming(true);
      startPolling();
    } catch (err) {
      setError(err.message || 'Failed to start stream');
      console.error('Start stream error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [startPolling]);

  /**
   * Stop stream
   */
  const stopStream = useCallback(async () => {
    setIsLoading(true);

    try {
      await apiService.stopStream();
      stopPolling();
      setIsStreaming(false);

      // Final fetch
      await fetchResults();
    } catch (err) {
      setError(err.message || 'Failed to stop stream');
      console.error('Stop stream error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [stopPolling, fetchResults]);

  /**
   * Initial load - fetch results once
   */
  useEffect(() => {
    fetchResults();
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    streamData,
    isStreaming,
    isLoading,
    error,
    startStream,
    stopStream,
  };
};

export default useStreamData;
