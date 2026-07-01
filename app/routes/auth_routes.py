# app/routes/auth_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
from app.database import get_db, User
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, get_current_user
)

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # Generate unique ntfy topic for this user
    ntfy_topic = f"financegpt-{secrets.token_hex(8)}"

    user = User(
        name=body.name.strip(),
        email=email,
        hashed_password=hash_password(body.password),
        phone=body.phone,
        ntfy_topic=ntfy_topic,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})

    return {
        "message": "Account created successfully.",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "ntfy_topic": user.ntfy_topic,
        }
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": str(user.id)})

    return {
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "ntfy_topic": user.ntfy_topic,
        }
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "ntfy_topic": current_user.ntfy_topic,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/logout")
def logout():
    # JWT is stateless — client just deletes the token
    return {"message": "Logged out successfully."}