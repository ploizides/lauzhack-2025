/**
 * Type definitions for the Podcast AI Assistant
 * Matches backend API response structures
 */

export interface Topic {
  topic: string;
  keywords: string[];
  text_sample: string;
  timestamp?: string;
}

export interface FactCheck {
  claim: string;
  verdict: 'SUPPORTED' | 'REFUTED' | 'UNCERTAIN';
  confidence: number;
  explanation: string;
  key_facts: string[];
  sources: string[];
}

export interface Transcript {
  full_text: string;
  word_count: number;
  paragraph_count: number;
}

export interface ProcessAudioResponse {
  status: string;
  filename: string;
  transcript: Transcript;
  topics: Topic[];
  fact_checks: FactCheck[];
  summary: {
    total_topics: number;
    total_fact_checks: number;
    verified_claims: number;
    false_claims: number;
  };
}

// For future streaming support
export interface StreamMessage {
  type: 'transcript' | 'topic_update' | 'fact_queued' | 'fact_result' | 'error';
  data: any;
  timestamp: string;
}

export interface AppState {
  isProcessing: boolean;
  currentFile: File | null;
  transcript: Transcript | null;
  topics: Topic[];
  factChecks: FactCheck[];
  summary: ProcessAudioResponse['summary'] | null;
  error: string | null;
}

export type ProcessingStage = 'idle' | 'uploading' | 'transcribing' | 'analyzing' | 'fact-checking' | 'complete' | 'error';
