"""Abstract base for DAW backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from ..core.models import RenderConfig


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    AIFF = "aiff"
    OGG = "ogg"


class DAWInfo(BaseModel):
    name: str
    version: str = "unknown"
    tier: int  # 1=scripted, 2=applescript, 3=export
    platform: str = "all"
    available: bool = False


class DAWBackend(ABC):
    @abstractmethod
    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        """Render MIDI to audio."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available on this system."""

    @abstractmethod
    def supported_formats(self) -> list[AudioFormat]:
        """Return supported output formats."""

    @abstractmethod
    def get_info(self) -> DAWInfo:
        """Return backend metadata."""
