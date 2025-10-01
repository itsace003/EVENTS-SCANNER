import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import UserSession
from .database import get_async_db
import structlog

logger = structlog.get_logger()

class SessionManager:
    """
    Lightweight session management using secure cookies for user preferences and tracking.
    """
    
    def __init__(self):
        self.cookie_name = "ai_events_session"
        self.session_lifetime = timedelta(days=30)  # 30 days
        self.cookie_settings = {
            "httponly": True,
            "secure": True,  # Set to False in development
            "samesite": "lax",
            "max_age": int(self.session_lifetime.total_seconds())
        }
    
    def create_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    async def create_session(self, location: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user session and store it in the database.
        """
        session_id = self.create_session_id()
        
        default_preferences = {
            "location": location or "Online",
            "categories": ["Conference", "Workshop", "Networking", "Talk", "Hackathon"],
            "min_relevance_score": 5,
            "platform": "luma",
            "notifications": True,
            "theme": "dark"
        }
        
        if preferences:
            default_preferences.update(preferences)
        
        try:
            async with get_async_db().__anext__() as db:
                session = UserSession(
                    session_id=session_id,
                    location=default_preferences["location"],
                    preferences=default_preferences
                )
                
                db.add(session)
                await db.commit()
                
                logger.info("New session created", session_id=session_id[:8])
                return session_id
                
        except Exception as e:
            logger.error("Failed to create session", error=str(e))
            raise
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Retrieve a user session from the database.
        """
        try:
            async with get_async_db().__anext__() as db:
                query = select(UserSession).where(UserSession.session_id == session_id)
                result = await db.execute(query)
                session = result.scalar_one_or_none()
                
                if session:
                    # Update last active timestamp
                    await self._update_last_active(db, session_id)
                    await db.commit()
                
                return session
                
        except Exception as e:
            logger.error("Failed to retrieve session", session_id=session_id[:8], error=str(e))
            return None
    
    async def update_session_preferences(self, session_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences for a session.
        """
        try:
            async with get_async_db().__anext__() as db:
                # Get current session
                query = select(UserSession).where(UserSession.session_id == session_id)
                result = await db.execute(query)
                session = result.scalar_one_or_none()
                
                if not session:
                    logger.warning("Session not found for preference update", session_id=session_id[:8])
                    return False
                
                # Update preferences
                current_prefs = session.preferences or {}
                current_prefs.update(preferences)
                
                # Update location if provided in preferences
                if "location" in preferences:
                    session.location = preferences["location"]
                
                session.preferences = current_prefs
                await self._update_last_active(db, session_id)
                await db.commit()
                
                logger.info("Session preferences updated", 
                           session_id=session_id[:8],
                           updated_keys=list(preferences.keys()))
                
                return True
                
        except Exception as e:
            logger.error("Failed to update session preferences", 
                        session_id=session_id[:8], 
                        error=str(e))
            return False
    
    async def is_valid_session(self, session_id: str) -> bool:
        """
        Check if a session ID is valid and not expired.
        """
        if not session_id:
            return False
        
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Check if session has expired
        expiry_date = session.created_at + self.session_lifetime
        if datetime.utcnow() > expiry_date:
            await self._cleanup_expired_session(session_id)
            return False
        
        return True
    
    async def get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """
        Get user preferences for a session with defaults.
        """
        session = await self.get_session(session_id)
        
        if session and session.preferences:
            return session.preferences
        
        # Return default preferences
        return {
            "location": "Online",
            "categories": ["Conference", "Workshop", "Networking", "Talk", "Hackathon"],
            "min_relevance_score": 5,
            "platform": "luma",
            "notifications": True,
            "theme": "dark"
        }
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.
        """
        try:
            cutoff_date = datetime.utcnow() - self.session_lifetime
            
            async with get_async_db().__anext__() as db:
                # Get expired sessions
                query = select(UserSession).where(UserSession.created_at < cutoff_date)
                result = await db.execute(query)
                expired_sessions = result.scalars().all()
                
                count = len(expired_sessions)
                
                if count > 0:
                    # Delete expired sessions (cascade will handle watched_events)
                    for session in expired_sessions:
                        await db.delete(session)
                    
                    await db.commit()
                    logger.info(f"Cleaned up {count} expired sessions")
                
                return count
                
        except Exception as e:
            logger.error("Failed to cleanup expired sessions", error=str(e))
            return 0
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user session.
        """
        try:
            async with get_async_db().__anext__() as db:
                from .models import WatchedEvent
                
                session = await self.get_session(session_id)
                if not session:
                    return {}
                
                # Count watched events
                watched_query = select(WatchedEvent).where(WatchedEvent.session_id == session_id)
                watched_result = await db.execute(watched_query)
                watched_events = watched_result.scalars().all()
                
                # Calculate session age
                session_age = datetime.utcnow() - session.created_at
                
                stats = {
                    "session_id": session_id[:8],  # Truncated for privacy
                    "created_at": session.created_at.isoformat(),
                    "last_active": session.last_active.isoformat(),
                    "session_age_days": session_age.days,
                    "watched_events_count": len(watched_events),
                    "location": session.location,
                    "preferences": session.preferences or {}
                }
                
                return stats
                
        except Exception as e:
            logger.error("Failed to get session stats", session_id=session_id[:8], error=str(e))
            return {}
    
    async def _update_last_active(self, db: AsyncSession, session_id: str):
        """
        Update the last_active timestamp for a session.
        """
        update_query = (
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(last_active=datetime.utcnow())
        )
        await db.execute(update_query)
    
    async def _cleanup_expired_session(self, session_id: str):
        """
        Remove a specific expired session.
        """
        try:
            async with get_async_db().__anext__() as db:
                query = select(UserSession).where(UserSession.session_id == session_id)
                result = await db.execute(query)
                session = result.scalar_one_or_none()
                
                if session:
                    await db.delete(session)
                    await db.commit()
                    logger.info("Expired session cleaned up", session_id=session_id[:8])
                    
        except Exception as e:
            logger.error("Failed to cleanup expired session", session_id=session_id[:8], error=str(e))