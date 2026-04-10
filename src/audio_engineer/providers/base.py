"""Base classes for audio generation providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from audio_engineer.core.audio_track import AudioTrack


class ProviderCapability(str, Enum):
    """What a provider can do."""
    MIDI_GENERATION = "midi_generation"
    AUDIO_GENERATION = "audio_generation"
    VOCALS = "vocals"
    SOUND_DESIGN = "sound_design"
    AUDIO_ANALYSIS = "audio_analysis"
    SOURCE_SEPARATION = "source_separation"
    EFFECTS_PROCESSING = "effects_processing"
    TEXT_TO_SPEECH = "text_to_speech"


class TrackRequest(BaseModel):
    """A request to generate a single track."""
    track_name: str
    description: str
    preferred_provider: Optional[str] = None
    required_capabilities: list[ProviderCapability] = Field(default_factory=list)

    # Musical context (optional — providers use what they can)
    genre: Optional[str] = None
    key: Optional[str] = None
    tempo: Optional[int] = None
    time_signature: Optional[str] = None
    duration_seconds: Optional[float] = None
    instrument: Optional[str] = None
    style_hints: list[str] = Field(default_factory=list)

    # For layering: reference tracks this one should complement
    reference_track_names: list[str] = Field(default_factory=list)


class TrackResult(BaseModel):
    """Result of a track generation attempt."""
    track: Optional[AudioTrack] = None
    success: bool
    provider_used: str
    error: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class AudioProvider(ABC):
    """Interface for any audio generation backend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier."""

    @property
    @abstractmethod
    def capabilities(self) -> list[ProviderCapability]:
        """What this provider can do."""

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider is currently usable."""

    @abstractmethod
    def generate_track(self, request: TrackRequest) -> TrackResult:
        """Generate a single track from the request."""

    def supports(self, capability: ProviderCapability) -> bool:
        """Check if this provider supports a given capability."""
        return capability in self.capabilities
