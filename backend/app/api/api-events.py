from fastapi import APIRouter, HTTPException, Depends, Request, Response
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from ..event_discovery import EventDiscoveryEngine
from ..session_manager import SessionManager
import structlog

logger = structlog.get_logger()
router = APIRouter()

# Initialize managers
event_engine = EventDiscoveryEngine()
session_manager = SessionManager()

# Pydantic models for request/response
class DiscoverEventsRequest(BaseModel):
    location: str
    platform: Optional[str] = "luma"
    month: Optional[int] = None
    year: Optional[int] = None

class EventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    dateTime: str
    location: str
    sourceUrl: str
    platform: str
    category: str
    aiRelevanceScore: int
    tags: List[str]
    organizer: Optional[str] = None
    eventType: Optional[str] = None
    price: Optional[float] = None
    isWatched: bool
    createdAt: str

class EventsResponse(BaseModel):
    events: List[EventResponse]
    eventsByCategory: Dict[str, List[EventResponse]]
    totalEvents: int
    watchedCount: int
    month: int
    year: int

class WatchEventRequest(BaseModel):
    event_id: str
    watch_status: bool  # True to mark as watched, False to unmark

# Dependency to get session ID from cookies
async def get_session_id(request: Request) -> str:
    """Get or create session ID from cookies."""
    session_id = request.cookies.get(session_manager.cookie_name)
    
    if not session_id or not await session_manager.is_valid_session(session_id):
        # Create new session
        user_location = request.headers.get("CF-IPCountry") or "Online"  # Cloudflare header
        session_id = await session_manager.create_session(location=user_location)
    
    return session_id

@router.post("/discover-events")
async def discover_events(
    request: DiscoverEventsRequest,
    session_id: str = Depends(get_session_id),
    response: Response = None
):
    """
    Discover AI-related events for a specific location and month using Perplexity AI.
    """
    try:
        logger.info("Event discovery requested", 
                   location=request.location,
                   platform=request.platform,
                   session_id=session_id[:8])
        
        # Update session preferences with location
        await session_manager.update_session_preferences(
            session_id, 
            {"location": request.location, "platform": request.platform}
        )
        
        # Discover events
        events = await event_engine.discover_events(
            location=request.location,
            platform=request.platform,
            month=request.month,
            year=request.year
        )
        
        # Set session cookie
        if response:
            response.set_cookie(
                key=session_manager.cookie_name,
                value=session_id,
                **session_manager.cookie_settings
            )
        
        return {
            "success": True,
            "message": f"Discovered {len(events)} AI-related events",
            "events": events,
            "sessionId": session_id[:8]  # Truncated for privacy
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Event discovery failed", error=str(e), session_id=session_id[:8])
        raise HTTPException(status_code=500, detail="Failed to discover events")

@router.get("/events/{month}/{year}", response_model=EventsResponse)
async def get_events_for_month(
    month: int,
    year: int,
    location: Optional[str] = None,
    category: Optional[str] = None,
    min_relevance_score: Optional[int] = 5,
    session_id: str = Depends(get_session_id)
):
    """
    Get events for a specific month with user watch status.
    """
    try:
        if not (1 <= month <= 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        if year < 2024 or year > 2030:
            raise HTTPException(status_code=400, detail="Year must be between 2024 and 2030")
        
        events_data = await event_engine.get_events_for_month(
            session_id=session_id,
            location=location,
            month=month,
            year=year,
            category=category,
            min_relevance_score=min_relevance_score or 5
        )
        
        logger.info("Events retrieved", 
                   month=month, 
                   year=year,
                   total_events=events_data["totalEvents"],
                   session_id=session_id[:8])
        
        return events_data
        
    except Exception as e:
        logger.error("Failed to retrieve events", 
                    month=month, 
                    year=year, 
                    error=str(e),
                    session_id=session_id[:8])
        raise HTTPException(status_code=500, detail="Failed to retrieve events")

@router.post("/events/watch")
async def toggle_event_watch_status(
    request: WatchEventRequest,
    session_id: str = Depends(get_session_id)
):
    """
    Toggle watch status for an event.
    """
    try:
        if request.watch_status:
            # Mark as watched
            success = await event_engine.mark_event_watched(session_id, request.event_id)
            action = "marked as watched"
        else:
            # Unmark as watched
            success = await event_engine.unmark_event_watched(session_id, request.event_id)
            action = "unmarked as watched"
        
        if success:
            logger.info("Event watch status updated", 
                       event_id=request.event_id,
                       action=action,
                       session_id=session_id[:8])
            
            return {
                "success": True,
                "message": f"Event {action}",
                "eventId": request.event_id,
                "isWatched": request.watch_status
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update watch status")
            
    except Exception as e:
        logger.error("Failed to update event watch status", 
                    event_id=request.event_id,
                    error=str(e),
                    session_id=session_id[:8])
        raise HTTPException(status_code=500, detail="Failed to update watch status")

@router.get("/events/current")
async def get_current_month_events(
    location: Optional[str] = None,
    category: Optional[str] = None,
    session_id: str = Depends(get_session_id)
):
    """
    Get events for the current month.
    """
    now = datetime.now()
    return await get_events_for_month(
        month=now.month,
        year=now.year,
        location=location,
        category=category,
        session_id=session_id
    )

@router.get("/events/categories")
async def get_event_categories():
    """
    Get available event categories.
    """
    return {
        "categories": event_engine.event_categories,
        "platforms": event_engine.supported_platforms
    }