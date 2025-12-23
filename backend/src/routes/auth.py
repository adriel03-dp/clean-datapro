"""Authentication routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ..auth import register_user, login_user, verify_token, get_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenVerifyRequest(BaseModel):
    token: str


@router.post("/auth/register")
def register(req: RegisterRequest):
    """Register a new user"""
    result = register_user(req.email, req.password, req.name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/auth/login")
def login(req: LoginRequest):
    """Login a user"""
    result = login_user(req.email, req.password)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
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
def get_user_info(email: str):
    """Get user information"""
    user = get_user(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
