"""Track listing and detail endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class TrackInfo(BaseModel):
    name: str
    instrument: str
    channel: int
    event_count: int
    program: int


@router.get("/{session_id}", response_model=list[TrackInfo])
def list_tracks(session_id: str):
    """List all tracks for a session."""
    from audio_engineer.api.routes.sessions import _sessions

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]["session"]
    results = []
    for name, track in session.tracks.items():
        results.append(TrackInfo(
            name=track.name,
            instrument=track.instrument.value,
            channel=track.channel,
            event_count=len(track.events),
            program=track.program,
        ))
    return results


@router.get("/{session_id}/{track_name}", response_model=TrackInfo)
def get_track(session_id: str, track_name: str):
    """Get details for a specific track."""
    from audio_engineer.api.routes.sessions import _sessions

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]["session"]
    if track_name not in session.tracks:
        raise HTTPException(status_code=404, detail="Track not found")

    track = session.tracks[track_name]
    return TrackInfo(
        name=track.name,
        instrument=track.instrument.value,
        channel=track.channel,
        event_count=len(track.events),
        program=track.program,
    )
