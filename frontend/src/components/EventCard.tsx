import React from 'react';
import { Event } from '../types';
import { format } from 'date-fns';
import { 
  Calendar, 
  MapPin, 
  ExternalLink, 
  Eye, 
  EyeOff, 
  Star,
  Clock,
  Tag,
  DollarSign
} from 'lucide-react';
import { clsx } from 'clsx';

interface EventCardProps {
  event: Event;
  onToggleWatch: (eventId: string, currentStatus: boolean) => void;
  className?: string;
}

export const EventCard: React.FC<EventCardProps> = ({ 
  event, 
  onToggleWatch, 
  className 
}) => {
  const eventDate = new Date(event.dateTime);
  const isUpcoming = eventDate > new Date();
  
  const relevanceColor = event.aiRelevanceScore >= 8 
    ? 'text-green-400' 
    : event.aiRelevanceScore >= 6 
    ? 'text-yellow-400' 
    : 'text-gray-400';

  const handleWatchToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleWatch(event.id, event.isWatched);
  };

  const handleCardClick = () => {
    window.open(event.sourceUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div
      className={clsx(
        'bg-gray-800 border border-gray-700 rounded-lg p-6 hover:bg-gray-750 transition-colors cursor-pointer group relative',
        event.isWatched && 'ring-2 ring-blue-500/30 bg-gray-800/50',
        !isUpcoming && 'opacity-75',
        className
      )}
      onClick={handleCardClick}
    >
      {/* Watch Status Indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          onClick={handleWatchToggle}
          className={clsx(
            'p-1.5 rounded-full transition-colors',
            event.isWatched
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
          )}
          title={event.isWatched ? 'Mark as unwatched' : 'Mark as watched'}
        >
          {event.isWatched ? (
            <Eye className="h-4 w-4" />
          ) : (
            <EyeOff className="h-4 w-4" />
          )}
        </button>

        {/* AI Relevance Score */}
        <div className="flex items-center gap-1 bg-gray-700 px-2 py-1 rounded-full text-xs">
          <Star className={clsx('h-3 w-3', relevanceColor)} />
          <span className="text-gray-300">{event.aiRelevanceScore}</span>
        </div>
      </div>

      {/* Event Title */}
      <h3 className="text-lg font-semibold text-white mb-3 pr-20 group-hover:text-blue-400 transition-colors">
        {event.title}
      </h3>

      {/* Event Details */}
      <div className="space-y-2 mb-4">
        {/* Date & Time */}
        <div className="flex items-center gap-2 text-gray-300">
          <Calendar className="h-4 w-4 text-gray-400" />
          <time dateTime={event.dateTime} className="text-sm">
            {format(eventDate, 'MMM dd, yyyy • h:mm a')}
          </time>
          {!isUpcoming && (
            <span className="text-xs bg-gray-600 px-2 py-0.5 rounded-full">Past</span>
          )}
        </div>

        {/* Location */}
        <div className="flex items-center gap-2 text-gray-300">
          <MapPin className="h-4 w-4 text-gray-400" />
          <span className="text-sm">{event.location}</span>
        </div>

        {/* Platform */}
        <div className="flex items-center gap-2 text-gray-300">
          <ExternalLink className="h-4 w-4 text-gray-400" />
          <span className="text-sm capitalize">{event.platform}</span>
          {event.organizer && (
            <>
              <span className="text-gray-500">•</span>
              <span className="text-sm">{event.organizer}</span>
            </>
          )}
        </div>

        {/* Price (if available) */}
        {event.price !== undefined && event.price > 0 && (
          <div className="flex items-center gap-2 text-gray-300">
            <DollarSign className="h-4 w-4 text-gray-400" />
            <span className="text-sm">${event.price}</span>
          </div>
        )}
      </div>

      {/* Category Badge */}
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-900 text-blue-300">
          {event.category}
        </span>
        
        {event.eventType && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-700 text-gray-300 capitalize">
            {event.eventType}
          </span>
        )}
      </div>

      {/* Tags */}
      {event.tags && event.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {event.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-700 text-gray-300"
            >
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
          {event.tags.length > 3 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-700 text-gray-400">
              +{event.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Description */}
      {event.description && (
        <p className="text-gray-400 text-sm line-clamp-3 mb-4">
          {event.description.length > 150
            ? `${event.description.slice(0, 150)}...`
            : event.description}
        </p>
      )}

      {/* Hover Indicator */}
      <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <ExternalLink className="h-4 w-4 text-blue-400" />
      </div>
    </div>
  );
};