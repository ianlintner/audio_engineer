"""Mastering agent - adjusts master volume and returns metadata."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from audio_engineer.core.models import MidiTrackData

from audio_engineer.agents.base import BaseEngineer, SessionContext


class MasteringResult(BaseModel):
    """Output of the mastering stage."""
    master_volume: float = Field(ge=0.0, le=1.0)
    peak_instrument: str = ""
    total_events: int = 0
    notes: str = ""


class MasteringAgent(BaseEngineer):
    """Simple mastering agent that analyzes tracks and adjusts master level."""

    def __init__(self, llm: Any = None):
        super().__init__(llm=llm)

    def process(
        self, tracks: list[MidiTrackData], context: SessionContext
    ) -> MasteringResult:
        total_events = sum(len(t.events) for t in tracks)

        # Find instrument with most events (likely needs headroom)
        peak_instrument = ""
        max_events = 0
        for track in tracks:
            if len(track.events) > max_events:
                max_events = len(track.events)
                peak_instrument = track.instrument.value

        # Simple heuristic: if lots of events, lower master slightly
        if total_events > 5000:
            master_vol = 0.82
        elif total_events > 2000:
            master_vol = 0.87
        else:
            master_vol = 0.92

        return MasteringResult(
            master_volume=master_vol,
            peak_instrument=peak_instrument,
            total_events=total_events,
            notes=f"Mastered {len(tracks)} tracks with {total_events} total events.",
        )
