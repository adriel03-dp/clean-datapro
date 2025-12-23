"""Authentication module for CleanDataPro"""
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional
import pymongo
from pymongo import MongoClient

# Get MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/cleandatapro")
client = MongoClient(MONGODB_URI)
db = client["cleandatapro"]
users_collection = db["users"]

# JWT secret key
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {"email": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return email if valid"""
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
    # Check if user exists
    if users_collection.find_one({"email": email}):
        return {"success": False, "message": "Email already registered"}
    
    # Hash password and create user
    hashed_pwd = hash_password(password)
    user_doc = {
        "email": email,
        "password": hashed_pwd,
        "name": name,
        "created_at": datetime.utcnow(),
        "processing_count": 0
    }
    
    users_collection.insert_one(user_doc)
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
    user = users_collection.find_one({"email": email})
    
    if not user:
        return {"success": False, "message": "Invalid email or password"}
    
    if not verify_password(password, user["password"]):
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
    user = users_collection.find_one({"email": email})
    if user:
        return {
            "email": user["email"],
            "name": user.get("name", ""),
            "processing_count": user.get("processing_count", 0),
            "created_at": user.get("created_at")
        }
    return None
