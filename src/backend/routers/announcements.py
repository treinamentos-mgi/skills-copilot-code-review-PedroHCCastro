"""
Announcement endpoints for the High School Management System API

Dates are stored and compared as ISO strings (YYYY-MM-DD) in the server's local date.
An announcement is "active" from its start date (or immediately, when none is set)
through its expiration date, inclusive. Messages are plain text; clients must render them
as text, not HTML.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, StringConstraints

from ..database import announcements_collection
from .auth import get_current_teacher

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

STATUS_ORDER = {"active": 0, "scheduled": 1, "expired": 2}

AnnouncementMessage = Annotated[str, StringConstraints(
    strip_whitespace=True, min_length=1, max_length=500)]


class AnnouncementIn(BaseModel):
    """Payload to create or replace an announcement"""
    message: AnnouncementMessage
    start_date: Optional[date] = None
    expires_at: date


def _today() -> str:
    return date.today().isoformat()


def _status(doc: Dict[str, Any], today: str) -> str:
    if doc["expires_at"] < today:
        return "expired"
    if doc.get("start_date") and doc["start_date"] > today:
        return "scheduled"
    return "active"


def _serialize(doc: Dict[str, Any], today: str) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "message": doc["message"],
        "start_date": doc.get("start_date"),
        "expires_at": doc["expires_at"],
        "status": _status(doc, today)
    }


def _parse_id(announcement_id: str) -> ObjectId:
    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ObjectId(announcement_id)


def _to_document(payload: AnnouncementIn) -> Dict[str, Any]:
    if payload.start_date and payload.expires_at < payload.start_date:
        raise HTTPException(
            status_code=400,
            detail="A data de expiração deve ser igual ou posterior à data de início.")

    return {
        "message": payload.message,
        "start_date": payload.start_date.isoformat() if payload.start_date else None,
        "expires_at": payload.expires_at.isoformat()
    }


@router.get("", response_model=List[Dict[str, Any]])
def get_announcements(active_only: bool = Query(False)) -> List[Dict[str, Any]]:
    """
    List announcements, sorted with active ones first, then by expiration date.

    - active_only: return only announcements active today (used by the banner)
    """
    today = _today()
    query: Dict[str, Any] = {}
    if active_only:
        query = {
            "expires_at": {"$gte": today},
            "$or": [{"start_date": None}, {"start_date": {"$lte": today}}]
        }

    announcements = [_serialize(doc, today)
                     for doc in announcements_collection.find(query)]
    announcements.sort(key=lambda a: (
        STATUS_ORDER[a["status"]], a["expires_at"], a["id"]))
    return announcements


@router.post("", status_code=201, response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementIn,
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Create an announcement - requires a logged-in teacher"""
    document = _to_document(payload)
    document["created_by"] = teacher["username"]
    result = announcements_collection.insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize(document, _today())


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementIn,
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Replace an announcement's content and dates - requires a logged-in teacher"""
    object_id = _parse_id(announcement_id)
    document = _to_document(payload)

    result = announcements_collection.update_one(
        {"_id": object_id}, {"$set": document})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    return _serialize(updated, _today())


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, str]:
    """Delete an announcement - requires a logged-in teacher"""
    result = announcements_collection.delete_one(
        {"_id": _parse_id(announcement_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
