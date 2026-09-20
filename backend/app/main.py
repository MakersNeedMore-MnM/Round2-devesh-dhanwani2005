from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.actions import router as actions_router
from app.api.assets import router as assets_router
from app.api.auth import router as auth_router
from app.api.dashboard import health_router, router as dashboard_router
from app.api.incidents import router as incidents_router
from app.api.investigation import router as demo_router
from app.api.logs import router as logs_router
from app.api.reports import router as reports_router
from app.api.threat_intel import router as intel_router
from app.config import get_settings
from app.database.client import DatabaseUnavailable
from app.utils.errors import AppError, app_error_handler

settings = get_settings()

app = FastAPI(
    title="CyberSentinel API",
    description=(
        "AI-powered cyber incident investigation and response platform. "
        "Observe → Detect → Investigate → Reason → Plan → Act → Verify. "
        "All response actions are simulated unless explicitly configured otherwise."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(DatabaseUnavailable)
async def db_unavailable(_, exc: DatabaseUnavailable):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"detail": str(exc), "code": "supabase_unavailable"})


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(incidents_router)
app.include_router(logs_router)
app.include_router(assets_router)
app.include_router(intel_router)
app.include_router(actions_router)
app.include_router(reports_router)
app.include_router(demo_router)


@app.exception_handler(Exception)
async def unhandled_error(_, exc: Exception):
    if isinstance(exc, (HTTPException, AppError, DatabaseUnavailable)):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "internal_error"})


@app.get("/")
def root():
    return {
        "name": "CyberSentinel",
        "docs": "/docs",
        "health": "/health",
        "response_mode": "simulated",
    }

