"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.middleware.logging import LoggingMiddleware

# Initialize structured logging
setup_logging(log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO")
logger = get_logger(__name__)

app = FastAPI(
    title="Email Agent API",
    description="AI-powered email assistant for business brokers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Logging middleware (add first to log all requests)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Email Agent API starting up")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Email Agent API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    # Log the exception with full context
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.ENVIRONMENT == "development" else None,
        },
    )
