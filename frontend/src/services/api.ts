/**
 * Groovi API Service
 * Production-ready API client with proper error handling
 */

import type { RecommendationResponse, TranscriptionResponse } from '../types';

// API base URL from environment variable
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

// WebSocket URL for voice connection
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:5000/ws/voice';

// Request timeout (10 seconds)
const REQUEST_TIMEOUT = 10000;

/**
 * Custom API error class for structured error handling
 */
export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout = REQUEST_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Handle API response and throw on errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Try to get error detail from response body
    let detail: string | undefined;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || errorBody.message || errorBody.error;
    } catch {
      // Response body is not JSON
    }

    throw new ApiError(
      `API request failed: ${response.status}`,
      response.status,
      detail
    );
  }

  return response.json();
}

/**
 * Get song recommendations based on mood text
 * POST /recommend
 * Note: Uses longer timeout (30s) as this calls Groq AI + Spotify
 */
export async function getRecommendations(text: string): Promise<RecommendationResponse> {
  // Validate input
  if (!text.trim()) {
    throw new ApiError('Mood text is required', 400, 'Please describe your mood');
  }

  const response = await fetchWithTimeout(
    `${API_URL}/recommend`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: text.trim() }),
    },
    30000 // 30 second timeout for AI + Spotify calls
  );

  return handleResponse<RecommendationResponse>(response);
}

/**
 * Transcribe audio file to text
 * POST /transcribe
 */
export async function transcribeAudio(audioBlob: Blob, filename = 'recording.webm'): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);

  const response = await fetchWithTimeout(
    `${API_URL}/transcribe`,
    {
      method: 'POST',
      body: formData,
      // Note: Don't set Content-Type header, browser will set it with boundary
    },
    30000 // 30 second timeout for audio processing
  );

  return handleResponse<TranscriptionResponse>(response);
}

/**
 * Convert text to speech
 * POST /synthesize
 * Returns audio blob (WAV file)
 */
export async function synthesizeSpeech(text: string): Promise<Blob> {
  if (!text.trim()) {
    throw new ApiError('Text is required for speech synthesis', 400);
  }

  const response = await fetchWithTimeout(`${API_URL}/synthesize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: text.trim() }),
  });

  if (!response.ok) {
    throw new ApiError(
      'Speech synthesis failed',
      response.status,
      'Could not generate audio'
    );
  }

  // Return as blob for audio playback
  return response.blob();
}

/**
 * Health check - verify API is running
 * GET /
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(`${API_URL}/`, {
      method: 'GET',
    }, 5000); // 5 second timeout for health check
    
    return response.ok;
  } catch {
    return false;
  }
}
