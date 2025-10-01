import { useState, useEffect, useCallback } from 'react';
import { ApiService } from '../utils/api';
import { EventsResponse, DiscoverEventsRequest, Platform } from '../types';
import toast from 'react-hot-toast';

export const useEvents = (initialMonth?: number, initialYear?: number) => {
  const [events, setEvents] = useState<EventsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);

  const loadEvents = useCallback(async (
    month?: number, 
    year?: number,
    filters?: { location?: string; category?: string; min_relevance_score?: number }
  ) => {
    if (!month || !year) {
      const now = new Date();
      month = month || now.getMonth() + 1;
      year = year || now.getFullYear();
    }

    setLoading(true);
    setError(null);

    try {
      const eventsData = await ApiService.getEventsForMonth(month, year, filters);
      setEvents(eventsData);
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Failed to load events';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const discoverEvents = useCallback(async (request: DiscoverEventsRequest) => {
    setDiscovering(true);
    setError(null);

    try {
      const result = await ApiService.discoverEvents(request);
      toast.success(result.message || 'Events discovered successfully!');
      
      // Refresh events after discovery
      await loadEvents(request.month, request.year);
      
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Failed to discover events';
      setError(errorMessage);
      toast.error(errorMessage);
      throw err;
    } finally {
      setDiscovering(false);
    }
  }, [loadEvents]);

  const toggleEventWatch = useCallback(async (eventId: string, currentWatchStatus: boolean) => {
    try {
      const newWatchStatus = !currentWatchStatus;
      await ApiService.toggleEventWatchStatus(eventId, newWatchStatus);
      
      // Update local state
      if (events) {
        const updatedEvents = events.events.map(event => 
          event.id === eventId ? { ...event, isWatched: newWatchStatus } : event
        );
        
        const updatedEventsByCategory = Object.keys(events.eventsByCategory).reduce((acc, category) => {
          acc[category] = events.eventsByCategory[category].map(event =>
            event.id === eventId ? { ...event, isWatched: newWatchStatus } : event
          );
          return acc;
        }, {} as Record<string, any>);

        setEvents({
          ...events,
          events: updatedEvents,
          eventsByCategory: updatedEventsByCategory,
          watchedCount: newWatchStatus 
            ? events.watchedCount + 1 
            : events.watchedCount - 1
        });
      }

      toast.success(newWatchStatus ? 'Event marked as watched' : 'Event unmarked as watched');
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Failed to update watch status';
      toast.error(errorMessage);
    }
  }, [events]);

  // Load initial events
  useEffect(() => {
    if (initialMonth && initialYear) {
      loadEvents(initialMonth, initialYear);
    }
  }, [initialMonth, initialYear, loadEvents]);

  return {
    events,
    loading,
    error,
    discovering,
    loadEvents,
    discoverEvents,
    toggleEventWatch,
    refresh: () => loadEvents(events?.month, events?.year)
  };
};