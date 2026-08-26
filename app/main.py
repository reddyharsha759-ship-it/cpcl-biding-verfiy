from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize database tables on startup
    try:
        from app.core.database import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Database initialization: {e}")
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.APP_NAME,
    description="Automated AI-powered multi-pillar compliance verification platform for Government e-Marketplace (GeM) tenders.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Dashboard"], include_in_schema=False)
async def serve_root(request: Request):
    """Serves the Dashboard UI for browser requests (text/html), or API metadata by default."""
    accept = request.headers.get("accept", "")
    dashboard_file = STATIC_DIR / "dashboard.html"

    if "text/html" in accept and dashboard_file.exists():
        return FileResponse(dashboard_file)

    return JSONResponse({
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    })


@app.get("/login", tags=["Auth"], include_in_schema=False)
async def serve_login():
    """Serves the Single Sign-On Authentication Portal."""
    login_file = STATIC_DIR / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/dashboard", tags=["Dashboard"], include_in_schema=False)
async def serve_dashboard():
    """Serves the Procurement Officer Decision Support Dashboard."""
    dashboard_file = STATIC_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
