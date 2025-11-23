/**
 * Global Application Context
 * Manages state for the entire application
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { AppState, Topic, FactCheck, Transcript, ProcessingStage } from '../types';
import { processAudioFile, UploadProgress } from '../services/api';

interface AppContextType extends AppState {
  processingStage: ProcessingStage;
  uploadProgress: number;
  processFile: (file: File) => Promise<void>;
  reset: () => void;
}

const initialState: AppState = {
  isProcessing: false,
  currentFile: null,
  transcript: null,
  topics: [],
  factChecks: [],
  summary: null,
  error: null,
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);
  const [processingStage, setProcessingStage] = useState<ProcessingStage>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);

  const processFile = useCallback(async (file: File) => {
    setState(prev => ({ ...prev, isProcessing: true, currentFile: file, error: null }));
    setProcessingStage('uploading');
    setUploadProgress(0);

    try {
      // Upload and process the file
      const result = await processAudioFile(file, (progress: UploadProgress) => {
        setUploadProgress(progress.percentage);
        if (progress.percentage === 100) {
          setProcessingStage('transcribing');
        }
      });

      // Simulate processing stages for better UX
      setProcessingStage('analyzing');
      await new Promise(resolve => setTimeout(resolve, 500));

      setProcessingStage('fact-checking');
      await new Promise(resolve => setTimeout(resolve, 500));

      // Update state with results
      setState(prev => ({
        ...prev,
        isProcessing: false,
        transcript: result.transcript,
        topics: result.topics,
        factChecks: result.fact_checks,
        summary: result.summary,
      }));

      setProcessingStage('complete');
    } catch (error: any) {
      console.error('Error processing file:', error);
      setState(prev => ({
        ...prev,
        isProcessing: false,
        error: error.response?.data?.detail || error.message || 'An error occurred while processing the file',
      }));
      setProcessingStage('error');
    }
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
    setProcessingStage('idle');
    setUploadProgress(0);
  }, []);

  const value: AppContextType = {
    ...state,
    processingStage,
    uploadProgress,
    processFile,
    reset,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
