"""Export and download endpoints for MIDI files."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/{session_id}/midi")
def download_combined_midi(session_id: str):
    """Download the combined MIDI file for a session."""
    from audio_engineer.api.routes.sessions import _sessions

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]["session"]

    # Find the combined MIDI file
    for f in session.output_files:
        if f.endswith("combined.mid"):
            path = Path(f)
            if path.exists():
                return FileResponse(
                    path=str(path),
                    media_type="audio/midi",
                    filename=f"session_{session_id}_combined.mid",
                )

    raise HTTPException(status_code=404, detail="Combined MIDI file not found")


@router.get("/{session_id}/midi/{track_name}")
def download_track_midi(session_id: str, track_name: str):
    """Download an individual track MIDI file."""
    from audio_engineer.api.routes.sessions import _sessions

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]["session"]

    # Find the track MIDI file
    for f in session.output_files:
        if f.endswith(f"{track_name}.mid"):
            path = Path(f)
            if path.exists():
                return FileResponse(
                    path=str(path),
                    media_type="audio/midi",
                    filename=f"session_{session_id}_{track_name}.mid",
                )

    raise HTTPException(status_code=404, detail="Track MIDI file not found")
