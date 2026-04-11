"""Audio generation providers — pluggable backends for track generation."""
from .base import AudioProvider, ProviderCapability, TrackRequest, TrackResult
from .registry import ProviderRegistry
from .midi_provider import MidiProvider
from .gemini_provider import GeminiLyriaProvider
from .llm_midi_provider import LLMMidiProvider

__all__ = [
    "AudioProvider",
    "GeminiLyriaProvider",
    "LLMMidiProvider",
    "MidiProvider",
    "ProviderCapability",
    "ProviderRegistry",
    "TrackRequest",
    "TrackResult",
]
