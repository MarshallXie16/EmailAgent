"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, brokers, settings, listings, leads, threads

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["Brokers"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(threads.router, prefix="/email-threads", tags=["Email Threads"])
