"""Session management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from audio_engineer.core.models import (
    Genre, SessionConfig, NoteName, Mode, KeySignature,
    SectionDef, BandConfig, BandMemberConfig, Instrument,
)
from audio_engineer.agents.orchestrator import SessionOrchestrator

router = APIRouter()

# In-memory session store (MVP)
_sessions: dict[str, dict] = {}
_orchestrator = SessionOrchestrator(output_dir="./output")


class CreateSessionRequest(BaseModel):
    genre: str = "classic_rock"
    key_root: str = "E"
    key_mode: str = "minor"
    tempo: int = Field(default=120, ge=40, le=300)
    with_keys: bool = False
    structure: list[dict] | None = None


class SessionResponse(BaseModel):
    id: str
    status: str
    genre: str
    key: str
    tempo: int
    tracks: list[str] = []
    output_files: list[str] = []


@router.post("/", response_model=SessionResponse)
def create_session(req: CreateSessionRequest):
    """Create a new session and generate backing tracks."""
    key_map = {n.value: n for n in NoteName}
    key_root = key_map.get(req.key_root, NoteName.E)
    mode_map = {m.value: m for m in Mode}
    key_mode = mode_map.get(req.key_mode, Mode.MINOR)

    members = [
        BandMemberConfig(instrument=Instrument.DRUMS),
        BandMemberConfig(instrument=Instrument.BASS),
        BandMemberConfig(instrument=Instrument.ELECTRIC_GUITAR),
    ]
    if req.with_keys:
        members.append(BandMemberConfig(instrument=Instrument.KEYS))

    structure = None
    if req.structure:
        structure = [SectionDef(**s) for s in req.structure]

    config = SessionConfig(
        genre=Genre(req.genre),
        tempo=req.tempo,
        key=KeySignature(root=key_root, mode=key_mode),
        band=BandConfig(members=members),
    )
    if structure:
        config.structure = structure

    session = _orchestrator.create_session(config)
    session = _orchestrator.run_session(session)

    _sessions[session.id] = {
        "session": session,
        "config": config,
    }

    return SessionResponse(
        id=session.id,
        status=session.status.value,
        genre=config.genre.value,
        key=f"{config.key.root.value} {config.key.mode.value}",
        tempo=config.tempo,
        tracks=list(session.tracks.keys()),
        output_files=session.output_files,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    data = _sessions[session_id]
    session = data["session"]
    config = data["config"]
    return SessionResponse(
        id=session.id,
        status=session.status.value,
        genre=config.genre.value,
        key=f"{config.key.root.value} {config.key.mode.value}",
        tempo=config.tempo,
        tracks=list(session.tracks.keys()),
        output_files=session.output_files,
    )


@router.get("/", response_model=list[SessionResponse])
def list_sessions():
    results = []
    for data in _sessions.values():
        session = data["session"]
        config = data["config"]
        results.append(SessionResponse(
            id=session.id,
            status=session.status.value,
            genre=config.genre.value,
            key=f"{config.key.root.value} {config.key.mode.value}",
            tempo=config.tempo,
            tracks=list(session.tracks.keys()),
            output_files=session.output_files,
        ))
    return results
