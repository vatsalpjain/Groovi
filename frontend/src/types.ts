// TypeScript type definitions for Groovi

// Mood analysis from API
export interface MoodAnalysis {
  category: string;
  description: string;
  summary: string;
  score: number;
  intensity: string;
}

// Song from Spotify
export interface Song {
  name: string;
  artist: string;
  uri: string;
  album_art: string;
  external_url: string;
}

// API response from /recommend
export interface RecommendationResponse {
  mood_analysis: MoodAnalysis;
  songs: Song[];
}

// API response from /transcribe
export interface TranscriptionResponse {
  transcript: string;
  filename: string;
  duration_estimate: number;
}
