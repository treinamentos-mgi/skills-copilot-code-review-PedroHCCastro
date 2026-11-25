"""
Authentication endpoints for the High School Management System API
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Header, HTTPException

from ..database import teachers_collection, auth_sessions_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SESSION_TTL = timedelta(hours=8)


def _utc_now() -> datetime:
    """Naive UTC timestamp, matching what pymongo returns on read."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(token: str) -> str:
    """Only the hash of a session token is stored, never the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account and issue a bearer session token"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    now = _utc_now()
    auth_sessions_collection.insert_one({
        "_id": _hash_token(token),
        "username": teacher["username"],
        "created_at": now,
        "expires_at": now + SESSION_TTL
    })

    # Return teacher information (excluding password) plus the session token
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "token": token
    }


@router.post("/logout")
def logout(authorization: Optional[str] = Header(default=None)) -> Dict[str, str]:
    """Revoke the bearer session token, if one is provided"""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() == "bearer" and token:
        auth_sessions_collection.delete_one({"_id": _hash_token(token)})
    return {"message": "Logged out"}


def get_current_teacher(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """FastAPI dependency: require a valid bearer token from a logged-in teacher"""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    session = auth_sessions_collection.find_one({"_id": _hash_token(token)})
    if not session or session["expires_at"] < _utc_now():
        raise HTTPException(
            status_code=401, detail="Session expired or invalid")

    teacher = teachers_collection.find_one({"_id": session["username"]})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Session expired or invalid")

    return teacher


@router.get("/check-session")
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.find_one({"_id": username})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }
