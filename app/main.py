import os
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.routes import demand, inventory, logistics, scenarios, reports
from app.utils.config import get_config
from app.utils.db import init_database

# Load environment variables
load_dotenv()

# Configuration
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    # Startup
    init_database()
    print("✅ Database initialized")

    # Expose AI availability flag
    try:
        _cfg = get_config()
        app.state.gemini_available = bool(_cfg.gemini_api_key)
    except Exception:
        app.state.gemini_available = False

    yield

    # Shutdown
    print("🛑 Shutting down gracefully")


# Create FastAPI app
app = FastAPI(
    title="AI Supply Chain Management Platform",
    description="AI-powered supply chain management for Indian retail businesses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Default AI availability flag
app.state.gemini_available = False

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CLIENT_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (e.g., favicon)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon if available."""
    path = os.path.join(static_dir, "favicon.svg")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/svg+xml")
    return {"detail": "favicon not found"}


# Include routers
app.include_router(demand.router, prefix="/api/demand", tags=["demand"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(logistics.router, prefix="/api/logistics", tags=["logistics"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "AI Supply Chain Management Platform",
        "version": "1.0.0",
        "description": "AI-powered supply chain management for Indian retail businesses",
        "ai_model": "Gemini 2.5 Pro",
        "market_focus": "Indian Retail MSME",
        "endpoints": {
            "demand_forecasting": "/api/demand/forecast",
            "inventory_management": "/api/inventory/",
            "logistics_tracking": "/api/logistics/shipments",
            "scenario_analysis": "/api/scenarios/analyze",
            "reports": "/api/reports/",
        },
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "ai_status": "operational" if app.state.gemini_available else "unavailable",
        "database": "connected",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "Something went wrong. Please try again.",
        },
    )


# Local development entrypoint
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",  # important: use "app.main:app" since main.py is inside `app/`
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
