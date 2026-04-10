"""Unified track model supporting both MIDI and raw audio data."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from audio_engineer.core.models import MidiTrackData, TrackType


class AudioTrack(BaseModel):
    """A single track in a session — either MIDI data or raw audio bytes.

    This is the common currency between providers. The MIDI engine produces
    tracks with ``midi_data`` set; AI audio providers produce tracks with
    ``audio_data`` set. Both can coexist in a session and be layered by
    the TrackComposer.
    """

    name: str
    track_type: TrackType
    provider: str

    # MIDI payload (set when track_type == MIDI)
    midi_data: Optional[MidiTrackData] = None

    # Audio payload (set when track_type == AUDIO)
    audio_data: Optional[bytes] = None
    mime_type: str = "audio/wav"
    sample_rate: Optional[int] = None

    # Metadata
    duration_seconds: Optional[float] = None
    tags: list[str] = Field(default_factory=list)

    @property
    def has_audio(self) -> bool:
        return self.audio_data is not None and len(self.audio_data) > 0

    @property
    def has_midi(self) -> bool:
        return self.midi_data is not None

    def save_audio(self, path: str | Path) -> Path:
        """Write raw audio bytes to disk.

        Callers are responsible for sanitising *path* — this method does not
        guard against path-traversal or writes outside an expected directory.
        """
        if not self.has_audio:
            raise ValueError(f"Track '{self.name}' has no audio data to save")
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self.audio_data)  # type: ignore[arg-type]
        return out
