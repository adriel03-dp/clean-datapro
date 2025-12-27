import os
from pathlib import Path
from typing import Optional, Callable, Any

# load .env from backend/ (one level up from src)
load_dotenv: Optional[Callable[..., Any]] = None
try:
    from dotenv import load_dotenv  # type: ignore

    _DOTENV_AVAILABLE = True
except Exception:
    load_dotenv = None  # type: ignore
    _DOTENV_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
DOTENV_PATH = BASE_DIR / ".env"

# call load_dotenv only if it was successfully imported
if load_dotenv is not None:
    load_dotenv(dotenv_path=DOTENV_PATH)

MONGODB_URI: Optional[str] = os.environ.get("MONGODB_URI")

# optional helper to get a pymongo client if pymongo is installed and MONGODB_URI is set
try:
    from pymongo import MongoClient  # type: ignore

    try:
        # ServerApi is optional; use if available to set Stable API
        from pymongo.server_api import ServerApi  # type: ignore

        _SERVER_API_AVAILABLE = True
    except Exception:
        ServerApi = None  # type: ignore
        _SERVER_API_AVAILABLE = False
except Exception:
    MongoClient = None  # type: ignore


def get_mongo_client():
    """Return a cached pymongo.MongoClient connected to MONGODB_URI or None.

    If `python-dotenv` loaded a `MONGODB_URI`, this creates a MongoClient
    once and returns it. If pymongo is not installed but a URI is provided,
    raises RuntimeError.
    """
    # cache client to avoid reconnecting on every call
    global _CLIENT
    if "_CLIENT" not in globals():
        _CLIENT = None

    if not MONGODB_URI:
        return None

    if MongoClient is None:
        raise RuntimeError(
            "pymongo is not installed; install pymongo to use MongoDB features"
        )

    if _CLIENT is not None:
        return _CLIENT

    # create client with optional ServerApi for stable API behaviour
    try:
        import logging
        logger = logging.getLogger("cleandatapro.backend")
        logger.info(f"Creating MongoDB client with URI: {MONGODB_URI[:30]}...")
        
        if _SERVER_API_AVAILABLE and ServerApi is not None:
            _CLIENT = MongoClient(
                MONGODB_URI,
                server_api=ServerApi("1"),
                serverSelectionTimeoutMS=5000
            )
        else:
            _CLIENT = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
        logger.info("MongoDB client created successfully")
    except Exception as e:
        # if client creation fails, return None so callers handle it
        # (keeps behavior simple and non-fatal)
        import logging
        logger = logging.getLogger("cleandatapro.backend")
        logger.error(f"Failed to create MongoDB client: {type(e).__name__}: {str(e)}")
        _CLIENT = None

    return _CLIENT


def test_mongo_connection(timeout: int = 5) -> bool:
    """Try to ping the MongoDB server and return True if reachable.

    This helper is used at application startup to log connectivity.
    """
    client = None
    try:
        client = get_mongo_client()
        if client is None:
            return False
        # server selection / ping
        client.admin.command({"ping": 1}, serverSelectionTimeoutMS=timeout*1000)
        return True
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger("cleandatapro.backend")
        logger.error(f"MongoDB connection error: {type(e).__name__}: {str(e)}")
        return False
    finally:
        # do not close the cached client here; leave it open for reuse
        pass
