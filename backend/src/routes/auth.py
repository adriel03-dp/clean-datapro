"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from ..auth import (
    get_current_user,
    get_user,
    login_user,
    normalize_email,
    register_user,
    verify_token,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenVerifyRequest(BaseModel):
    token: str = Field(min_length=1, max_length=4096)


@router.post("/auth/register")
def register(req: RegisterRequest):
    """Register a new user"""
    result = register_user(req.email, req.password, req.name)
    
    if not result["success"]:
        status = 503 if result["message"] == "Authentication service unavailable" else 400
        raise HTTPException(status_code=status, detail=result["message"])
    
    return result


@router.post("/auth/login")
def login(req: LoginRequest):
    """Login a user"""
    result = login_user(req.email, req.password)
    
    if not result["success"]:
        status = 503 if result["message"] == "Authentication service unavailable" else 401
        raise HTTPException(status_code=status, detail=result["message"])
    
    return result


@router.post("/auth/verify")
def verify(req: TokenVerifyRequest):
    """Verify a token"""
    email = verify_token(req.token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"valid": True, "user": user}


@router.get("/auth/user/{email}")
def get_user_info(email: str, current_user: dict = Depends(get_current_user)):
    """Get only the authenticated user's own profile."""
    if normalize_email(email) != current_user["email"]:
        raise HTTPException(status_code=403, detail="Cannot access another user")
    return current_user
