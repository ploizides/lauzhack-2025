/**
 * API Service - Handles all backend communication
 */

// Use relative URL in development (proxied to backend)
// In production, set via environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/stream';

class ApiService {
  /**
   * Start the podcast stream processing
   */
  async startStream() {
    try {
      const response = await fetch(`${API_BASE_URL}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('Failed to start stream:', error);
      throw error;
    }
  }

  /**
   * Stop the podcast stream processing
   */
  async stopStream() {
    try {
      const response = await fetch(`${API_BASE_URL}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to stop stream:', error);
      throw error;
    }
  }

  /**
   * Get current stream results
   */
  async getResults() {
    try {
      const response = await fetch(`${API_BASE_URL}/results`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch results:', error);
      throw error;
    }
  }

  /**
   * Check if backend is reachable
   */
  async healthCheck() {
    try {
      const response = await fetch('/', {
        method: 'GET',
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export default new ApiService();
