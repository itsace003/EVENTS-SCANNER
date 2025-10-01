from fastapi import APIRouter, HTTPException, Depends, Request, Response
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..session_manager import SessionManager
import structlog

logger = structlog.get_logger()
router = APIRouter()

# Initialize session manager
session_manager = SessionManager()

class UpdatePreferencesRequest(BaseModel):
    location: Optional[str] = None
    categories: Optional[list] = None
    min_relevance_score: Optional[int] = None
    platform: Optional[str] = None
    notifications: Optional[bool] = None
    theme: Optional[str] = None

async def get_session_id(request: Request) -> str:
    """Get session ID from cookies."""
    session_id = request.cookies.get(session_manager.cookie_name)
    
    if not session_id or not await session_manager.is_valid_session(session_id):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return session_id

@router.get("/preferences")
async def get_user_preferences(session_id: str = Depends(get_session_id)):
    """
    Get user preferences for the current session.
    """
    try:
        preferences = await session_manager.get_user_preferences(session_id)
        
        logger.info("User preferences retrieved", session_id=session_id[:8])
        
        return {
            "preferences": preferences,
            "sessionId": session_id[:8]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve user preferences", 
                    session_id=session_id[:8], 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve preferences")

@router.put("/preferences")
async def update_user_preferences(
    request: UpdatePreferencesRequest,
    session_id: str = Depends(get_session_id)
):
    """
    Update user preferences for the current session.
    """
    try:
        # Convert request to dict and remove None values
        preferences_update = {
            k: v for k, v in request.dict().items() 
            if v is not None
        }
        
        if not preferences_update:
            raise HTTPException(status_code=400, detail="No preferences provided")
        
        success = await session_manager.update_session_preferences(
            session_id, 
            preferences_update
        )
        
        if success:
            updated_preferences = await session_manager.get_user_preferences(session_id)
            
            logger.info("User preferences updated", 
                       session_id=session_id[:8],
                       updated_fields=list(preferences_update.keys()))
            
            return {
                "success": True,
                "message": "Preferences updated successfully",
                "preferences": updated_preferences
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update preferences")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user preferences", 
                    session_id=session_id[:8], 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@router.get("/session/stats")
async def get_session_stats(session_id: str = Depends(get_session_id)):
    """
    Get statistics and information about the current session.
    """
    try:
        stats = await session_manager.get_session_stats(session_id)
        
        logger.info("Session stats retrieved", session_id=session_id[:8])
        
        return {
            "stats": stats,
            "sessionId": session_id[:8]
        }
        
    except Exception as e:
        logger.error("Failed to retrieve session stats", 
                    session_id=session_id[:8], 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve session stats")

@router.post("/session/create")
async def create_new_session(
    location: Optional[str] = "Online",
    preferences: Optional[Dict[str, Any]] = None,
    response: Response = None
):
    """
    Create a new user session (useful for testing or manual session creation).
    """
    try:
        session_id = await session_manager.create_session(location, preferences)
        
        # Set session cookie
        if response:
            response.set_cookie(
                key=session_manager.cookie_name,
                value=session_id,
                **session_manager.cookie_settings
            )
        
        logger.info("New session created manually", session_id=session_id[:8])
        
        return {
            "success": True,
            "message": "New session created",
            "sessionId": session_id[:8],
            "location": location
        }
        
    except Exception as e:
        logger.error("Failed to create new session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.delete("/session")
async def clear_session(
    session_id: str = Depends(get_session_id),
    response: Response = None
):
    """
    Clear the current session (logout equivalent).
    """
    try:
        # Clear session cookie
        if response:
            response.delete_cookie(
                key=session_manager.cookie_name,
                **{k: v for k, v in session_manager.cookie_settings.items() if k != "max_age"}
            )
        
        logger.info("Session cleared", session_id=session_id[:8])
        
        return {
            "success": True,
            "message": "Session cleared successfully"
        }
        
    except Exception as e:
        logger.error("Failed to clear session", 
                    session_id=session_id[:8], 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear session")