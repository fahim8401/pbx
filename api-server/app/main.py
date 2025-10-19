"""
HPLink PBX API Server - FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    admin,
    auth,
    dids,
    health,
    ivr,
    plans,
    recordings,
    tenants,
    trunks,
    usage,
)
from app.settings import settings

app = FastAPI(
    title="HPLink PBX API",
    description="Multi-tenant Cloud PBX API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Plan Templates"])
app.include_router(ivr.router, prefix="/api/v1/ivr", tags=["IVR"])
app.include_router(dids.router, prefix="/api/v1/dids", tags=["DIDs"])
app.include_router(trunks.router, prefix="/api/v1/trunks", tags=["Trunks"])
app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage"])
app.include_router(recordings.router, prefix="/api/v1/recordings", tags=["Recordings"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    pass
