import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useEvents } from './hooks/useEvents';
import { EventDiscovery } from './components/EventDiscovery';
import { EventCard } from './components/EventCard';
import { 
  Brain, 
  Calendar, 
  Filter, 
  Eye,
  Grid3X3,
  Loader2
} from 'lucide-react';
import { clsx } from 'clsx';
import { EventCategory } from './types';

function App() {
  const currentDate = new Date();
  const {
    events,
    loading,
    error,
    discovering,
    discoverEvents,
    toggleEventWatch,
    loadEvents
  } = useEvents(currentDate.getMonth() + 1, currentDate.getFullYear());

  const [selectedCategory, setSelectedCategory] = useState<EventCategory | 'All'>('All');
  const [showWatchedOnly, setShowWatchedOnly] = useState(false);

  const categories: (EventCategory | 'All')[] = [
    'All', 'Conference', 'Workshop', 'Networking', 'Talk', 'Hackathon', 'Other'
  ];

  // Filter events based on selection
  const filteredEvents = events?.events.filter(event => {
    const categoryMatch = selectedCategory === 'All' || event.category === selectedCategory;
    const watchedMatch = !showWatchedOnly || event.isWatched;
    return categoryMatch && watchedMatch;
  }) || [];

  const handleCategoryChange = (category: EventCategory | 'All') => {
    setSelectedCategory(category);
  };

  useEffect(() => {
    // Load events on app start
    const now = new Date();
    loadEvents(now.getMonth() + 1, now.getFullYear());
  }, [loadEvents]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#374151',
            color: '#fff',
            border: '1px solid #4B5563'
          },
        }}
      />
      
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                AI Event Scanner v2.0
              </h1>
              <p className="text-gray-400">
                Intelligent event discovery powered by Perplexity AI
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Discovery Panel */}
          <div className="lg:col-span-1">
            <EventDiscovery
              onDiscover={discoverEvents}
              discovering={discovering}
              className="sticky top-8"
            />
          </div>

          {/* Events Display */}
          <div className="lg:col-span-2">
            {/* Controls */}
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-6">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                {/* Event Stats */}
                <div className="flex items-center gap-4 text-sm text-gray-300">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {events ? `${events.month}/${events.year}` : 'No month selected'}
                    </span>
                  </div>
                  {events && (
                    <>
                      <div className="flex items-center gap-1">
                        <Grid3X3 className="h-4 w-4" />
                        <span>{events.totalEvents} events</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="h-4 w-4" />
                        <span>{events.watchedCount} watched</span>
                      </div>
                    </>
                  )}
                </div>

                {/* Filters */}
                <div className="flex items-center gap-3">
                  {/* Watched Only Toggle */}
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showWatchedOnly}
                      onChange={(e) => setShowWatchedOnly(e.target.checked)}
                      className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-300">Watched only</span>
                  </label>

                  {/* Category Filter */}
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-gray-400" />
                    <select
                      value={selectedCategory}
                      onChange={(e) => handleCategoryChange(e.target.value as EventCategory | 'All')}
                      className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white focus:border-blue-500"
                    >
                      {categories.map(category => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center gap-3 text-gray-400">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span>Loading events...</span>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
                <p className="text-red-200">{error}</p>
              </div>
            )}

            {/* Events Grid */}
            {!loading && !error && (
              <div>
                {filteredEvents.length > 0 ? (
                  <div className="grid gap-6">
                    {filteredEvents.map(event => (
                      <EventCard
                        key={event.id}
                        event={event}
                        onToggleWatch={toggleEventWatch}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-300 mb-2">
                      {events?.totalEvents === 0 
                        ? 'No events found' 
                        : 'No events match your filters'}
                    </h3>
                    <p className="text-gray-400 mb-6">
                      {events?.totalEvents === 0 
                        ? 'Discover events for this month using the search panel on the left.'
                        : 'Try adjusting your category filter or showing all events.'}
                    </p>
                    {selectedCategory !== 'All' || showWatchedOnly ? (
                      <button
                        onClick={() => {
                          setSelectedCategory('All');
                          setShowWatchedOnly(false);
                        }}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                      >
                        Clear Filters
                      </button>
                    ) : null}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;