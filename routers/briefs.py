"""
Briefs router — Strategy Studio endpoints.

Two surfaces:
  /api/briefs/*          — Internal (consultant + War Room)
  /api/portal/{brief_id} — Client-facing (read-only, gated)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from schemas.models import (
    Brief,
    BriefStageContent,
    BriefStageType,
    ClientPortalView,
    OpeningBriefingRequest,
    StageReleaseRequest,
    WarRoomTurn,
    WarRoomResponse,
    WarRoomMessage,
)
from agents.war_room import (
    generate_opening_briefing,
    war_room_turn,
    release_stage,
    get_client_portal_view,
)
from db.client import get_supabase

router = APIRouter()


# ── Brief lifecycle ────────────────────────────────────────────────────────────

@router.post("/briefs", response_model=Brief, status_code=201)
async def create_brief(brief: Brief) -> Brief:
    """
    Create a new brief. Called when the client submits the intake form.
    Generates a brief_id, saves to DB, status = intake_received.
    """
    db = get_supabase()
    brief.brief_id = brief.brief_id or str(uuid.uuid4())
    brief.status = "intake_received"
    brief.created_at = datetime.utcnow().isoformat()
    brief.updated_at = brief.created_at

    try:
        db.table("briefs").insert(brief.model_dump()).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return brief


@router.get("/briefs", response_model=list[Brief])
async def list_briefs(status: str | None = None) -> list[Brief]:
    """List all briefs. Optionally filter by status."""
    db = get_supabase()
    try:
        q = db.table("briefs").select("*").order("created_at", desc=True)
        if status:
            q = q.eq("status", status)
        result = q.execute()
        return [Brief(**r) for r in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/briefs/{brief_id}", response_model=Brief)
async def get_brief(brief_id: str) -> Brief:
    """Get a single brief by ID."""
    db = get_supabase()
    try:
        result = db.table("briefs").select("*").eq("brief_id", brief_id).single().execute()
        return Brief(**result.data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Brief not found: {e}")


@router.patch("/briefs/{brief_id}/confirm", response_model=Brief)
async def client_confirms_brief(brief_id: str) -> Brief:
    """
    Client has confirmed the debrief. Moves status → client_confirmed.
    Triggers the internal read phase.
    """
    db = get_supabase()
    try:
        db.table("briefs").update({
            "status": "client_confirmed",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("brief_id", brief_id).execute()
        result = db.table("briefs").select("*").eq("brief_id", brief_id).single().execute()
        return Brief(**result.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── War Room — internal consultant + AI workspace ─────────────────────────────

@router.post("/briefs/{brief_id}/war-room/open", response_model=WarRoomResponse)
async def open_war_room(brief_id: str) -> WarRoomResponse:
    """
    Consultant opens the War Room for a brief.
    Triggers the AI to generate its opening structured briefing.
    This is the AI's first act — not a report, a briefing for the consultant.
    """
    try:
        return await generate_opening_briefing(OpeningBriefingRequest(brief_id=brief_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/briefs/{brief_id}/war-room/message", response_model=WarRoomResponse)
async def send_war_room_message(brief_id: str, turn: WarRoomTurn) -> WarRoomResponse:
    """
    Consultant sends a message in the War Room.
    The AI responds — it may explore an angle, surface corpus patterns,
    draft client-facing content, or continue deliberating.
    Nothing from this conversation reaches the client without a release.
    """
    if turn.brief_id != brief_id:
        turn.brief_id = brief_id
    try:
        return await war_room_turn(turn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/briefs/{brief_id}/war-room/messages", response_model=list[WarRoomMessage])
async def get_war_room_messages(brief_id: str, limit: int = 50) -> list[WarRoomMessage]:
    """Fetch the full War Room conversation history for a brief."""
    db = get_supabase()
    try:
        result = (
            db.table("war_room_messages")
            .select("*")
            .eq("brief_id", brief_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return [WarRoomMessage(**m) for m in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/briefs/{brief_id}/war-room/messages/{message_id}/pin")
async def pin_war_room_message(brief_id: str, message_id: str) -> dict:
    """Consultant pins a key AI insight in the War Room."""
    db = get_supabase()
    try:
        db.table("war_room_messages").update({"pinned": True}).eq(
            "brief_id", brief_id
        ).eq("message_id", message_id).execute()
        return {"pinned": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Stage drafts ───────────────────────────────────────────────────────────────

@router.get("/briefs/{brief_id}/stages", response_model=list[BriefStageContent])
async def get_brief_stages(brief_id: str) -> list[BriefStageContent]:
    """Get all stage drafts for a brief (internal view — includes unreleased)."""
    db = get_supabase()
    try:
        result = (
            db.table("brief_stages")
            .select("*")
            .eq("brief_id", brief_id)
            .order("created_at", desc=False)
            .execute()
        )
        return [BriefStageContent(**s) for s in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/briefs/{brief_id}/stages/{stage}", response_model=BriefStageContent)
async def update_stage_draft(
    brief_id: str,
    stage: BriefStageType,
    update: dict,
) -> BriefStageContent:
    """Consultant edits a stage draft before releasing."""
    db = get_supabase()
    try:
        db.table("brief_stages").update({
            **update,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("brief_id", brief_id).eq("stage", stage).execute()
        result = (
            db.table("brief_stages")
            .select("*")
            .eq("brief_id", brief_id)
            .eq("stage", stage)
            .single()
            .execute()
        )
        return BriefStageContent(**result.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Release gate — consultant explicitly releases a stage to client ────────────

@router.post("/briefs/{brief_id}/release", response_model=ClientPortalView)
async def release_stage_to_client(
    brief_id: str,
    request: StageReleaseRequest,
) -> ClientPortalView:
    """
    THE GATE. Consultant explicitly releases a stage to the client portal.
    This triggers a client notification. Nothing reaches the client without
    passing through this endpoint.
    """
    if request.brief_id != brief_id:
        request.brief_id = brief_id
    try:
        return await release_stage(
            brief_id=brief_id,
            stage=request.stage,
            headline=request.headline,
            body=request.body,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Client Portal — read-only, gated ──────────────────────────────────────────

@router.get("/portal/{brief_id}", response_model=ClientPortalView)
async def get_client_portal(brief_id: str) -> ClientPortalView:
    """
    CLIENT-FACING endpoint. Returns only what has been released.
    No internal notes. No unreleased stages. No War Room content.
    The client accesses this via a link sent by Markivio.
    """
    try:
        return await get_client_portal_view(brief_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Brief not found: {e}")
