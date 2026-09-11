"""Authentication module for CleanDataPro"""
import bcrypt
import jwt
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request

try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None
    PYMONGO_AVAILABLE = False

# MongoDB connection (lazy-loaded)
MONGODB_URI = os.getenv("MONGODB_URI")
_client = None
_db = None
_users_collection = None

# JWT secret key. It is intentionally not given a predictable fallback.
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
MAX_PASSWORD_BYTES = 72  # bcrypt silently truncates longer passwords
logger = logging.getLogger("cleandatapro.backend.auth")


def normalize_email(email: str) -> str:
    """Return the canonical representation used for identity lookups."""
    return email.strip().lower()


def validate_password(password: str) -> None:
    """Validate passwords before bcrypt sees them."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password is required")
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be 72 bytes or fewer")


def get_users_collection():
    """Get the users collection, initializing MongoDB connection if needed"""
    global _client, _db, _users_collection
    
    if not PYMONGO_AVAILABLE or MongoClient is None:
        raise RuntimeError("pymongo is not installed")
    
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI environment variable not set")
    
    if _users_collection is None:
        try:
            _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test the connection
            _client.admin.command('ping')
            _db = _client["cleandatapro"]
            _users_collection = _db["users"]
            try:
                _users_collection.create_index("email", unique=True)
            except Exception:
                logger.exception("Unable to ensure unique user email index")
        except Exception as e:
            _client = None
            _db = None
            _users_collection = None
            raise RuntimeError(f"Failed to connect to MongoDB: {str(e)}")
    
    return _users_collection


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    validate_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        validate_password(password)
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not configured")
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"email": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return email if valid"""
    if not SECRET_KEY:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            return None
        return email
    except jwt.InvalidTokenError:
        return None


def register_user(email: str, password: str, name: str = "") -> dict:
    """Register a new user"""
    email = normalize_email(email)
    name = name.strip()[:120]
    try:
        validate_password(password)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}
    if not SECRET_KEY:
        return {"success": False, "message": "Authentication service unavailable"}
    try:
        users_collection = get_users_collection()
    except RuntimeError as e:
        logger.warning("Registration unavailable: %s", e)
        return {"success": False, "message": "Authentication service unavailable"}
    
    # Check if user exists
    try:
        if users_collection.find_one({"email": email}):
            return {"success": False, "message": "Email already registered"}
    except Exception:
        logger.exception("Unable to check existing user")
        return {"success": False, "message": "Authentication service unavailable"}
    
    # Hash password and create user
    hashed_pwd = hash_password(password)
    user_doc = {
        "email": email,
        "password": hashed_pwd,
        "name": name,
        "created_at": datetime.now(timezone.utc),
        "processing_count": 0
    }
    
    try:
        users_collection.insert_one(user_doc)
    except Exception as exc:
        # Do not expose database details. A unique index also closes the race
        # between find_one() and insert_one().
        if exc.__class__.__name__ == "DuplicateKeyError":
            return {"success": False, "message": "Email already registered"}
        logger.exception("Unable to create user")
        return {"success": False, "message": "Unable to create account"}
    token = create_access_token(email)
    
    return {
        "success": True,
        "message": "Registration successful",
        "token": token,
        "email": email,
        "name": name
    }


def login_user(email: str, password: str) -> dict:
    """Login a user"""
    email = normalize_email(email)
    if not SECRET_KEY:
        return {"success": False, "message": "Authentication service unavailable"}
    try:
        users_collection = get_users_collection()
    except RuntimeError as e:
        logger.warning("Login unavailable: %s", e)
        return {"success": False, "message": "Authentication service unavailable"}
    
    try:
        user = users_collection.find_one({"email": email})
    except Exception:
        logger.exception("Unable to look up user")
        return {"success": False, "message": "Authentication service unavailable"}
    
    if not user:
        return {"success": False, "message": "Invalid email or password"}
    
    if not verify_password(password, user.get("password", "")):
        return {"success": False, "message": "Invalid email or password"}
    
    token = create_access_token(email)
    
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "email": email,
        "name": user.get("name", "")
    }


def get_user(email: str) -> Optional[dict]:
    """Get user information"""
    email = normalize_email(email)
    try:
        users_collection = get_users_collection()
    except RuntimeError:
        return None
    
    user = users_collection.find_one({"email": email})
    if user:
        return {
            "email": user["email"],
            "name": user.get("name", ""),
            "processing_count": user.get("processing_count", 0),
            "created_at": user.get("created_at")
        }
    return None


def get_current_user(request: Request) -> dict:
    """Resolve and require the authenticated user for protected API routes."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = verify_token(auth_header.split(" ", 1)[1].strip())
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="User account not found")
    return user
