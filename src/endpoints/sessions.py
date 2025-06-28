"""
Session management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import optional_auth, verify_auth
from .chat import get_session_manager

router = APIRouter()


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    expires_at: str | None = None
    data: dict
    message_count: int


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class CreateSessionRequest(BaseModel):
    session_id: str | None = None
    data: dict | None = None
    ttl: int | None = None  # Custom TTL in seconds


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    auth: dict = Depends(verify_auth)
) -> SessionResponse:
    """Create a new session"""
    sm = await get_session_manager()

    session_id = request.session_id or None
    session = await sm.create_session(
        session_id=session_id,
        data=request.data or {},
        ttl=request.ttl
    )

    messages = await sm.get_messages(session.session_id)

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        expires_at=session.expires_at.isoformat() if session.expires_at else None,
        data=session.data,
        message_count=len(messages)
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    auth: dict = Depends(optional_auth)
) -> SessionResponse:
    """Get session details"""
    sm = await get_session_manager()

    session = await sm.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    messages = await sm.get_messages(session_id)

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        expires_at=session.expires_at.isoformat() if session.expires_at else None,
        data=session.data,
        message_count=len(messages)
    )


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    auth: dict = Depends(optional_auth)
):
    """Get messages from a session"""
    sm = await get_session_manager()

    session = await sm.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    messages = await sm.get_messages(session_id, limit=limit)

    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages)
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    auth: dict = Depends(verify_auth)
):
    """Delete a session"""
    sm = await get_session_manager()

    success = await sm.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session deleted successfully"}


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    auth: dict = Depends(verify_auth)
) -> SessionListResponse:
    """List all active sessions"""
    # Note: ChukSessions doesn't have a built-in list method,
    # so this would need to be implemented based on your storage backend
    # For now, return empty list

    return SessionListResponse(
        sessions=[],
        total=0
    )
