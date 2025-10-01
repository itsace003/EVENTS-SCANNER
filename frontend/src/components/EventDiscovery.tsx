import React, { useState } from 'react';
import { Search, MapPin, Calendar, Loader2 } from 'lucide-react';
import { DiscoverEventsRequest, Platform } from '../types';
import { clsx } from 'clsx';

interface EventDiscoveryProps {
  onDiscover: (request: DiscoverEventsRequest) => Promise<void>;
  discovering: boolean;
  className?: string;
}

export const EventDiscovery: React.FC<EventDiscoveryProps> = ({
  onDiscover,
  discovering,
  className
}) => {
  const [location, setLocation] = useState('');
  const [platform, setPlatform] = useState<Platform>('luma');
  const [month, setMonth] = useState<number>(new Date().getMonth() + 1);
  const [year, setYear] = useState<number>(new Date().getFullYear());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!location.trim()) {
      return;
    }

    const request: DiscoverEventsRequest = {
      location: location.trim(),
      platform,
      month,
      year
    };

    await onDiscover(request);
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 3 }, (_, i) => currentYear + i);

  return (
    <div className={clsx('bg-gray-800 rounded-lg p-6 border border-gray-700', className)}>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
          <Search className="h-5 w-5 text-blue-400" />
          Discover AI Events
        </h2>
        <p className="text-gray-400 text-sm">
          Find AI-related events using intelligent search. Specify your location and target month.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Location Input */}
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-300 mb-2">
            Location
          </label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., San Francisco, New York, London, or 'Online'"
              required
              disabled={discovering}
              className="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
        </div>

        {/* Platform Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Platform
          </label>
          <div className="grid grid-cols-2 gap-3">
            {(['luma', 'meetup'] as Platform[]).map((p) => (
              <label
                key={p}
                className={clsx(
                  'flex items-center justify-center p-3 rounded-lg border-2 cursor-pointer transition-colors',
                  platform === p
                    ? 'border-blue-500 bg-blue-500/10 text-blue-300'
                    : 'border-gray-600 bg-gray-900 text-gray-300 hover:border-gray-500',
                  discovering && 'opacity-50 cursor-not-allowed'
                )}
              >
                <input
                  type="radio"
                  name="platform"
                  value={p}
                  checked={platform === p}
                  onChange={(e) => setPlatform(e.target.value as Platform)}
                  disabled={discovering}
                  className="sr-only"
                />
                <span className="capitalize font-medium">{p}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Date Selection */}
        <div className="grid grid-cols-2 gap-4">
          {/* Month */}
          <div>
            <label htmlFor="month" className="block text-sm font-medium text-gray-300 mb-2">
              Month
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                id="month"
                value={month}
                onChange={(e) => setMonth(parseInt(e.target.value))}
                disabled={discovering}
                className="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed appearance-none"
              >
                {monthNames.map((name, index) => (
                  <option key={index + 1} value={index + 1}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Year */}
          <div>
            <label htmlFor="year" className="block text-sm font-medium text-gray-300 mb-2">
              Year
            </label>
            <select
              id="year"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              disabled={discovering}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed appearance-none"
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={discovering || !location.trim()}
          className={clsx(
            'w-full py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2',
            discovering || !location.trim()
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          )}
        >
          {discovering ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Discovering Events...
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Discover Events
            </>
          )}
        </button>
      </form>

      {/* Info Text */}
      <div className="mt-4 p-3 bg-gray-900 rounded-lg border border-gray-600">
        <p className="text-xs text-gray-400">
          💡 <strong>Tip:</strong> Events are discovered using AI-powered search. 
          This process may take 30-60 seconds as we scan and classify events for relevance.
        </p>
      </div>
    </div>
  );
};