from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .routes import process as process_router
from .routes import files as files_router
from .routes import runs as runs_router
from .routes import auth as auth_router
from utils.logger import get_logger
from . import config as cfg

app = FastAPI(title="CleanDataPro Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process_router.router, prefix="/api")
app.include_router(files_router.router, prefix="/api")
app.include_router(runs_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")

logger = get_logger("cleandatapro.backend")


@app.on_event("startup")
def startup_event():
    """Initialize MongoDB connection if available.

    MongoDB is optional - the backend works without it, just won't save history.
    """
    try:
        mongo_uri = cfg.MONGODB_URI
        logger.info(f"MongoDB URI configured: {bool(mongo_uri)} (length: {len(mongo_uri) if mongo_uri else 0})")
        
        if mongo_uri:
            logger.info("Attempting MongoDB connection...")
            ok = cfg.test_mongo_connection()
            if ok:
                logger.info("✅ MongoDB connection established - processing history enabled")
            else:
                logger.warning("⚠️ MongoDB connection test failed - processing history disabled (optional)")
        else:
            logger.warning("⚠️ MongoDB not configured - processing history disabled (optional)")
    except Exception as e:
        logger.error(f"⚠️ MongoDB connection error: {type(e).__name__}: {str(e)}", exc_info=True)


@app.on_event("shutdown")
def shutdown_event():
    """Cleanly close any cached MongoDB client on shutdown."""
    try:
        client = cfg.get_mongo_client()
        if client:
            client.close()
            logger.info("Closed MongoDB client on shutdown")
    except Exception as e:
        logger.warning("Error while closing MongoDB client: %s", e)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
