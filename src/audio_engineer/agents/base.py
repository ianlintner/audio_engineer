"""Base classes for all agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

from audio_engineer.core.models import (
    Instrument, Genre, SessionConfig, MidiTrackData,
    SectionDef, MixConfig, KeySignature,
)
from audio_engineer.core.music_theory import ChordProgression
from audio_engineer.core.midi_engine import MidiEngine


class SessionContext(BaseModel):
    """Shared context passed to all agents during a session."""
    config: SessionConfig
    arrangement: list[SectionDef] = Field(default_factory=list)
    chord_progressions: dict[str, ChordProgression] = Field(default_factory=dict)
    existing_tracks: dict[str, MidiTrackData] = Field(default_factory=dict)
    current_section: str | None = None

    model_config = {"arbitrary_types_allowed": True}


class BaseMusician(ABC):
    """Base class for musician agents."""

    def __init__(self, instrument: Instrument, channel: int, llm: Any = None):
        self.instrument = instrument
        self.channel = channel
        self.llm = llm
        self.midi_engine = MidiEngine()

    @abstractmethod
    def generate_part(self, context: SessionContext) -> MidiTrackData:
        """Generate a complete MIDI track for the session."""

    def _get_section_bars(self, context: SessionContext) -> list[tuple[str, int, int, float]]:
        """Calculate (section_name, start_bar, num_bars, intensity) for each section."""
        result = []
        current_bar = 0
        arrangement = context.arrangement or context.config.structure
        for section in arrangement:
            for _ in range(section.repeats):
                result.append((section.name, current_bar, section.bars, section.intensity))
                current_bar += section.bars
        return result


class BaseEngineer(ABC):
    """Base class for audio engineering agents."""

    def __init__(self, llm: Any = None):
        self.llm = llm

    @abstractmethod
    def process(self, tracks: list[MidiTrackData], context: SessionContext) -> Any:
        """Process tracks and return engineering output."""
