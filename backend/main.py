"""
MEDIQR MLOPS — FastAPI Application Entry Point
AI-Powered Pharmacy Inventory, Billing, Patient Guidance & Analytics Platform
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
from database.base import init_db
from middleware.metrics import MetricsMiddleware
from utils.exceptions import (
    MediqrException,
    mediqr_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mediqr")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("🚀 MEDIQR MLOPS starting up...")
    init_db()
    logger.info("✅ Database tables initialized")

    # Pre-load ML models
    try:
        from ml.serve import _get_demand_model, _get_expiry_model
        dm = _get_demand_model()
        em = _get_expiry_model()
        
        if not dm or not em:
            logger.warning("⚠️ ML models not found — running training pipeline...")
            from ml.train_pipeline import run_pipeline
            run_pipeline()
            # The models are now on disk. Next time _get_... is called, it will load if globals are None.
            # We don't strictly need to force load here, but it's good practice to ensure they are in memory.
            # ml.serve caches models in globals, so if they were None, _get_... will load them.
            dm = _get_demand_model()
            em = _get_expiry_model()

        if dm:
            logger.info("✅ Demand prediction model loaded")
        else:
            logger.error("❌ Failed to load demand prediction model")
            
        if em:
            logger.info("✅ Expiry risk model loaded")
        else:
            logger.error("❌ Failed to load expiry risk model")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not pre-load ML models: {e}")

    yield

    # Shutdown
    logger.info("👋 MEDIQR MLOPS shutting down...")


# ── Create Application ──────────────────────────────────────────────────────

app = FastAPI(
    title="MEDIQR MLOPS",
    description="AI-Powered Pharmacy Inventory, Billing, Patient Guidance & Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(MetricsMiddleware)

# ── Exception Handlers ──────────────────────────────────────────────────────

app.add_exception_handler(MediqrException, mediqr_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Static Files ─────────────────────────────────────────────────────────────

app.mount("/static/qr", StaticFiles(directory=str(config.QR_DIR)), name="qr_codes")

# ── Register Routers ────────────────────────────────────────────────────────

from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.inventory import router as inventory_router
from routes.billing import router as billing_router
from routes.patient import router as patient_router
from routes.ml import router as ml_router
from routes.monitoring import router as monitoring_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(inventory_router)
app.include_router(billing_router)
app.include_router(patient_router)
app.include_router(ml_router)
app.include_router(monitoring_router)


# ── Root Endpoint ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "MEDIQR MLOPS",
        "version": "1.0.0",
        "description": "AI-Powered Pharmacy Inventory, Billing, Patient Guidance & Analytics Platform",
        "docs": "/docs",
        "health": "/health",
    }


# ── Run with Uvicorn ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
