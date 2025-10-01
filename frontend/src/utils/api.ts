import axios from 'axios';
import { 
  Event, 
  EventsResponse, 
  UserPreferences, 
  DiscoverEventsRequest, 
  WatchEventRequest,
  SessionStats 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for cookies
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ApiService {
  // Event Discovery
  static async discoverEvents(request: DiscoverEventsRequest) {
    const response = await apiClient.post('/api/events/discover-events', request);
    return response.data;
  }

  // Get events for a specific month
  static async getEventsForMonth(
    month: number, 
    year: number, 
    filters?: {
      location?: string;
      category?: string;
      min_relevance_score?: number;
    }
  ): Promise<EventsResponse> {
    const params = new URLSearchParams();
    if (filters?.location) params.append('location', filters.location);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.min_relevance_score) params.append('min_relevance_score', filters.min_relevance_score.toString());

    const response = await apiClient.get(`/api/events/${month}/${year}?${params}`);
    return response.data;
  }

  // Get current month events
  static async getCurrentMonthEvents(filters?: {
    location?: string;
    category?: string;
  }): Promise<EventsResponse> {
    const params = new URLSearchParams();
    if (filters?.location) params.append('location', filters.location);
    if (filters?.category) params.append('category', filters.category);

    const response = await apiClient.get(`/api/events/current?${params}`);
    return response.data;
  }

  // Toggle event watch status
  static async toggleEventWatchStatus(eventId: string, watchStatus: boolean) {
    const request: WatchEventRequest = {
      event_id: eventId,
      watch_status: watchStatus,
    };
    const response = await apiClient.post('/api/events/watch', request);
    return response.data;
  }

  // Get event categories and platforms
  static async getEventCategories() {
    const response = await apiClient.get('/api/events/categories');
    return response.data;
  }

  // User Preferences
  static async getUserPreferences(): Promise<{ preferences: UserPreferences }> {
    const response = await apiClient.get('/api/users/preferences');
    return response.data;
  }

  static async updateUserPreferences(preferences: Partial<UserPreferences>) {
    const response = await apiClient.put('/api/users/preferences', preferences);
    return response.data;
  }

  // Session Management
  static async getSessionStats(): Promise<{ stats: SessionStats }> {
    const response = await apiClient.get('/api/users/session/stats');
    return response.data;
  }

  static async createNewSession(location?: string, preferences?: Partial<UserPreferences>) {
    const response = await apiClient.post('/api/users/session/create', {
      location,
      preferences,
    });
    return response.data;
  }

  static async clearSession() {
    const response = await apiClient.delete('/api/users/session');
    return response.data;
  }

  // Health Check
  static async healthCheck() {
    const response = await apiClient.get('/health');
    return response.data;
  }
}

export default ApiService;