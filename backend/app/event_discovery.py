from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from .models import Event, UserSession, WatchedEvent, EventDiscoveryLog
from .perplexity_client import PerplexityClient
from .database import get_async_db
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import structlog
from dateutil import parser as date_parser

logger = structlog.get_logger()

class EventDiscoveryEngine:
    """
    Intelligent event discovery using Perplexity AI with comprehensive event management.
    """
    
    def __init__(self):
        self.perplexity_client = PerplexityClient()
        self.supported_platforms = ["luma", "meetup"]
        self.event_categories = ["Conference", "Workshop", "Networking", "Talk", "Hackathon", "Other"]
    
    async def discover_events(
        self, 
        location: str, 
        platform: str = "luma", 
        month: Optional[int] = None, 
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover and store AI-related events for the specified month and location.
        """
        if platform not in self.supported_platforms:
            raise ValueError(f"Platform {platform} not supported. Use one of: {self.supported_platforms}")
        
        # Set default month/year to current if not provided
        now = datetime.now()
        target_month = month or now.month
        target_year = year or now.year
        
        # Create date range for the target month
        start_date = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(target_year, target_month + 1, 1) - timedelta(days=1)
        
        date_range = f"from {start_date.strftime('%B %Y')}"
        
        logger.info("Starting event discovery", 
                   location=location, 
                   platform=platform, 
                   date_range=date_range)
        
        discovery_log = EventDiscoveryLog(
            search_query=f"{location} {platform} {date_range}",
            platform=platform,
            location=location
        )
        
        try:
            # Search for events using Perplexity
            raw_events = await self.perplexity_client.search_events(
                location=location,
                platform=platform,
                date_range=date_range
            )
            
            discovery_log.events_found = len(raw_events)
            
            # Process and store events
            processed_events = []
            async with get_async_db().__anext__() as db:
                for raw_event in raw_events:
                    try:
                        processed_event = await self._process_and_store_event(db, raw_event, platform)
                        if processed_event:
                            processed_events.append(processed_event)
                    except Exception as e:
                        logger.error("Failed to process event", event=raw_event.get("title"), error=str(e))
                        continue
                
                discovery_log.events_classified = len(processed_events)
                discovery_log.success = True
                
                # Store discovery log
                db.add(discovery_log)
                await db.commit()
            
            logger.info("Event discovery completed", 
                       events_found=len(raw_events),
                       events_stored=len(processed_events))
            
            return processed_events
            
        except Exception as e:
            discovery_log.success = False
            discovery_log.error_message = str(e)
            
            async with get_async_db().__anext__() as db:
                db.add(discovery_log)
                await db.commit()
            
            logger.error("Event discovery failed", error=str(e))
            raise
    
    async def get_events_for_month(
        self, 
        session_id: str,
        location: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        category: Optional[str] = None,
        min_relevance_score: int = 5
    ) -> Dict[str, Any]:
        """
        Get events for a specific month, with user watch status.
        """
        now = datetime.now()
        target_month = month or now.month
        target_year = year or now.year
        
        start_date = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(target_year, target_month + 1, 1) - timedelta(days=1)
        
        async with get_async_db().__anext__() as db:
            # Build query
            query = select(Event).where(
                and_(
                    Event.date_time >= start_date,
                    Event.date_time <= end_date,
                    Event.ai_relevance_score >= min_relevance_score,
                    Event.is_active == True
                )
            )
            
            # Add filters
            if location:
                query = query.where(Event.location.ilike(f"%{location}%"))
            
            if category and category in self.event_categories:
                query = query.where(Event.category == category)
            
            # Order by date and relevance score
            query = query.order_by(Event.date_time.asc(), Event.ai_relevance_score.desc())
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Get watched events for this session
            watched_query = select(WatchedEvent.event_id).where(
                WatchedEvent.session_id == session_id
            )
            watched_result = await db.execute(watched_query)
            watched_event_ids = {row[0] for row in watched_result.fetchall()}
            
            # Format events with watch status
            formatted_events = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "dateTime": event.date_time.isoformat(),
                    "location": event.location,
                    "sourceUrl": event.source_url,
                    "platform": event.platform,
                    "category": event.category,
                    "aiRelevanceScore": event.ai_relevance_score,
                    "tags": event.tags or [],
                    "organizer": event.organizer,
                    "eventType": event.event_type,
                    "price": event.price,
                    "isWatched": event.id in watched_event_ids,
                    "createdAt": event.created_at.isoformat(),
                }
                formatted_events.append(event_dict)
            
            # Group by category
            events_by_category = {}
            for category_name in self.event_categories:
                events_by_category[category_name] = [
                    event for event in formatted_events 
                    if event["category"] == category_name
                ]
            
            return {
                "events": formatted_events,
                "eventsByCategory": events_by_category,
                "totalEvents": len(formatted_events),
                "watchedCount": len([e for e in formatted_events if e["isWatched"]]),
                "month": target_month,
                "year": target_year
            }
    
    async def _process_and_store_event(
        self, 
        db: AsyncSession, 
        raw_event: Dict[str, Any], 
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a raw event from Perplexity and store it in the database.
        """
        try:
            # Parse and validate event data
            title = raw_event.get("title", "").strip()
            if not title:
                return None
            
            # Parse date
            date_str = raw_event.get("date_time") or raw_event.get("date")
            if not date_str:
                return None
            
            try:
                event_date = date_parser.parse(str(date_str))
                if event_date.tzinfo is None:
                    event_date = event_date.replace(tzinfo=None)
            except (ValueError, TypeError):
                logger.warning("Failed to parse event date", date_str=date_str)
                return None
            
            # Check if event already exists
            existing_query = select(Event).where(
                and_(
                    Event.title == title,
                    Event.date_time == event_date,
                    Event.platform == platform
                )
            )
            existing_result = await db.execute(existing_query)
            existing_event = existing_result.scalar_one_or_none()
            
            if existing_event:
                # Update existing event if needed
                existing_event.updated_at = datetime.utcnow()
                existing_event.ai_relevance_score = raw_event.get("ai_relevance_score", existing_event.ai_relevance_score)
                await db.commit()
                return None
            
            # Create new event
            event = Event(
                title=title,
                description=raw_event.get("description", "").strip(),
                date_time=event_date,
                location=raw_event.get("location", "Online").strip(),
                source_url=raw_event.get("url", "").strip() or f"https://{platform}.com",
                platform=platform,
                category=raw_event.get("category", "Other"),
                ai_relevance_score=raw_event.get("ai_relevance_score", 5),
                tags=raw_event.get("tags", []),
                organizer=raw_event.get("organizer", "").strip(),
                event_type=raw_event.get("event_type", "unknown"),
                price=float(raw_event.get("price", 0.0)) if raw_event.get("price") else 0.0,
            )
            
            db.add(event)
            await db.commit()
            await db.refresh(event)
            
            return {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "aiRelevanceScore": event.ai_relevance_score,
                "dateTime": event.date_time.isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to process event", error=str(e), raw_event=raw_event)
            await db.rollback()
            return None
    
    async def mark_event_watched(self, session_id: str, event_id: str) -> bool:
        """
        Mark an event as watched by a user session.
        """
        try:
            async with get_async_db().__anext__() as db:
                # Check if already watched
                existing_query = select(WatchedEvent).where(
                    and_(
                        WatchedEvent.session_id == session_id,
                        WatchedEvent.event_id == event_id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_watch = existing_result.scalar_one_or_none()
                
                if existing_watch:
                    return True  # Already watched
                
                # Create watched event record
                watched_event = WatchedEvent(
                    session_id=session_id,
                    event_id=event_id
                )
                
                db.add(watched_event)
                await db.commit()
                
                logger.info("Event marked as watched", 
                           session_id=session_id, 
                           event_id=event_id)
                
                return True
                
        except Exception as e:
            logger.error("Failed to mark event as watched", 
                        session_id=session_id, 
                        event_id=event_id, 
                        error=str(e))
            return False
    
    async def unmark_event_watched(self, session_id: str, event_id: str) -> bool:
        """
        Remove watched status from an event for a user session.
        """
        try:
            async with get_async_db().__anext__() as db:
                watched_query = select(WatchedEvent).where(
                    and_(
                        WatchedEvent.session_id == session_id,
                        WatchedEvent.event_id == event_id
                    )
                )
                watched_result = await db.execute(watched_query)
                watched_event = watched_result.scalar_one_or_none()
                
                if watched_event:
                    await db.delete(watched_event)
                    await db.commit()
                    
                    logger.info("Event watch status removed", 
                               session_id=session_id, 
                               event_id=event_id)
                
                return True
                
        except Exception as e:
            logger.error("Failed to remove event watch status", 
                        session_id=session_id, 
                        event_id=event_id, 
                        error=str(e))
            return False