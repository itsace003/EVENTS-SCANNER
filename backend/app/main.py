from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import structlog
import os

from .database import DatabaseManager
from .session_manager import SessionManager
from .api.events import router as events_router
from .api.users import router as users_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting AI Event Scanner v2.0")
    
    # Initialize database
    await DatabaseManager.init_db()
    logger.info("Database initialized")
    
    # Initialize session manager for cleanup
    session_manager = SessionManager()
    
    # Clean up expired sessions on startup
    cleaned = await session_manager.cleanup_expired_sessions()
    logger.info(f"Cleaned up {cleaned} expired sessions on startup")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down AI Event Scanner v2.0")
    await DatabaseManager.close_db()

# Create FastAPI application
app = FastAPI(
    title="AI Event Scanner v2.0",
    description="Intelligent AI event discovery using Perplexity AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(events_router, prefix="/api/events", tags=["Events"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "AI Event Scanner"
    }

# Root endpoint
@app.get("/")
async def read_root():
    """Root endpoint with API information."""
    return {
        "message": "AI Event Scanner v2.0 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging."""
    logger.warning("HTTP exception occurred", 
                   status_code=exc.status_code,
                   detail=exc.detail,
                   path=request.url.path,
                   method=request.method)
    
    return {
        "error": True,
        "status_code": exc.status_code,
        "message": exc.detail,
        "path": request.url.path
    }

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Internal server error handler with logging."""
    logger.error("Internal server error occurred",
                 error=str(exc),
                 path=request.url.path,
                 method=request.method)
    
    return {
        "error": True,
        "status_code": 500,
        "message": "Internal server error",
        "path": request.url.path
    }

# Serve static files in production
if os.getenv("SERVE_STATIC", "false").lower() == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use structlog configuration
    )