// TypeScript type definitions for Groovi

// Mood analysis from API
export interface MoodAnalysis {
  category: string;      // Mood category (e.g., happy, sad, energetic)
  description: string;   // Reasoning for song selection based on mood analysis
}

// Song from Spotify
export interface Song {
  name: string;
  artist: string;
  uri: string;
  album_art: string;
  external_url: string;
  reason?: string;  // Why this track was recommended (from agent)
}

// Agent thought step
export interface ThoughtStep {
  iteration: number;
  thought?: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  error?: string;
}

// API response from /recommend
export interface RecommendationResponse {
  mood_analysis: MoodAnalysis;
  songs: Song[];
  thought_process?: ThoughtStep[];  // Agent's reasoning steps
  agent_iterations?: number;       // Number of agent iterations
}

// API response from /transcribe
export interface TranscriptionResponse {
  transcript: string;
  filename: string;
  duration_estimate: number;
}
