from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import process as process_router
from .routes import files as files_router
from .routes import runs as runs_router
from ..utils.logger import get_logger
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

logger = get_logger("cleandatapro.backend")


@app.on_event("startup")
def startup_event():
    """Try to establish a MongoDB connection at startup and log the result.

    This is best-effort: the app continues if MongoDB is unavailable.
    """
    try:
        ok = cfg.test_mongo_connection()
        if ok:
            logger.info("MongoDB connection OK")
        else:
            logger.warning(
                "MongoDB not available or MONGODB_URI not set; continuing"
            )
    except Exception as e:
        logger.warning("Error while testing MongoDB connection: %s", e)


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
