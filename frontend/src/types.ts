// FIXED types.ts - TypeScript Definitions

export interface Event {
  id: string;
  title: string;
  description?: string;
  dateTime: string;
  location: string;
  sourceUrl: string;
  platform: string;
  category: string;
  aiRelevanceScore: number;
  tags: string[];
  organizer?: string;
  eventType?: string;
  price?: number;
  isWatched: boolean;
  createdAt: string;
}

export interface EventsResponse {
  events: Event[];
  eventsByCategory: Record<string, Event[]>;  // ✅ FIXED: Added proper generic type
  totalEvents: number;
  watchedCount: number;
  month: number;
  year: number;
}

export interface UserPreferences {
  location: string;
  categories: string[];
  min_relevance_score: number;
  platform: string;
  notifications: boolean;
  theme: string;
}

export interface DiscoverEventsRequest {
  location: string;
  platform?: string;
  month?: number;
  year?: number;
}

export interface WatchEventRequest {
  event_id: string;
  watch_status: boolean;
}

export interface SessionStats {
  session_id: string;
  created_at: string;
  last_active: string;
  session_age_days: number;
  watched_events_count: number;
  location: string;
  preferences: UserPreferences;
}

// ✅ FIXED: Added proper generic parameter
export interface ApiResponse<T = any> {
  success?: boolean;
  message?: string;
  error?: boolean;
  status_code?: number;
  data?: T;
}

export type Platform = 'luma' | 'meetup';
export type EventCategory = 'Conference' | 'Workshop' | 'Networking' | 'Talk' | 'Hackathon' | 'Other';
export type Theme = 'light' | 'dark';