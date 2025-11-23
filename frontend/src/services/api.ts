/**
 * API Service Layer
 * Handles all communication with the backend
 */

import axios, { AxiosProgressEvent } from 'axios';
import { ProcessAudioResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

/**
 * Process an audio file through the complete pipeline
 * @param file Audio file to process
 * @param onProgress Callback for upload progress
 * @returns Processing results
 */
export const processAudioFile = async (
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<ProcessAudioResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<ProcessAudioResponse>('/process-audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent: AxiosProgressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress: UploadProgress = {
          loaded: progressEvent.loaded,
          total: progressEvent.total,
          percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
        };
        onProgress(progress);
      }
    },
  });

  return response.data;
};

/**
 * Get current server statistics
 */
export const getStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

// TODO: Future WebSocket support for streaming
export class AudioStreamClient {
  private ws: WebSocket | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();

  constructor(private url: string = 'ws://localhost:8000/listen') {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const handler = this.messageHandlers.get(message.type);
          if (handler) {
            handler(message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
    });
  }

  on(eventType: string, handler: (data: any) => void) {
    this.messageHandlers.set(eventType, handler);
  }

  send(data: ArrayBuffer | string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default apiClient;
