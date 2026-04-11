# Multi-Provider Audio Generation Platform

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Audio Engineer from a rock-band MIDI generator into a genre-agnostic, multi-provider audio production platform where any musical style a user can describe gets produced as layered, mixable tracks.

**Architecture:** A provider abstraction layer sits between the orchestrator and generation backends (MIDI engine, Gemini Lyria, future: MusicGen, Stable Audio). A new `AudioTrack` model unifies MIDI and raw audio stems. A capability-based router selects the best provider per track based on what it needs (precision MIDI vs. AI-generated audio). An LLM prompt composer translates free-text descriptions into structured generation requests. A track composer merges heterogeneous stems into layered output.

**Tech Stack:** Python 3.11+, Pydantic v2, mido, google-genai (Lyria 3), pydub (audio merging), FastMCP, pytest

---

## Phase Overview

This plan covers **Phase 1: Provider Abstraction & Track Layer Model** — the foundation everything else builds on. Future phases are outlined at the end for context.

| Phase | Focus | Depends On |
|-------|-------|------------|
| **1 (this plan)** | Provider abstraction, AudioTrack model, capability routing, track composer | — |
| 2 | LLM-driven composition (natural language → arrangement) | Phase 1 |
| 3 | Vocal tracks, sound design, additional providers | Phase 1 |
| 4 | Post-production (source separation, effects, mastering chain) | Phase 1+3 |
| 5 | Analysis feedback loop, iterative refinement | Phase 1+2+4 |

---

## File Structure

### New files

| File | Responsibility |
|------|----------------|
| `src/audio_engineer/providers/__init__.py` | Package init, re-exports |
| `src/audio_engineer/providers/base.py` | `AudioProvider` ABC, `ProviderCapability` enum, `TrackRequest`/`TrackResult` models |
| `src/audio_engineer/providers/registry.py` | `ProviderRegistry` — registers providers, routes requests by capability |
| `src/audio_engineer/providers/midi_provider.py` | Wraps existing MIDI engine + musician agents as a provider |
| `src/audio_engineer/providers/gemini_provider.py` | Wraps Gemini Lyria as a provider |
| `src/audio_engineer/core/audio_track.py` | `AudioTrack` model — unified representation for MIDI and audio stems |
| `src/audio_engineer/core/track_composer.py` | `TrackComposer` — layers multiple AudioTracks into combined output |
| `tests/providers/__init__.py` | Test package |
| `tests/providers/test_base.py` | Tests for provider ABC and models |
| `tests/providers/test_registry.py` | Tests for registry routing logic |
| `tests/providers/test_midi_provider.py` | Tests for MIDI provider wrapper |
| `tests/providers/test_gemini_provider.py` | Tests for Gemini provider wrapper |
| `tests/core/test_audio_track.py` | Tests for AudioTrack model |
| `tests/core/test_track_composer.py` | Tests for TrackComposer |

### Modified files

| File | Changes |
|------|---------|
| `src/audio_engineer/core/models.py` | Add `TrackType` enum, `AudioFormat` enum to core models |
| `src/audio_engineer/agents/orchestrator.py` | Use provider registry instead of hardcoded agents |
| `src/audio_engineer/mcp_server.py` | Add `generate_audio_track` and `list_providers` tools |
| `src/audio_engineer/config/settings.py` | Add provider-related settings |

---

## Task 1: Core Enums and AudioTrack Model

**Files:**
- Modify: `src/audio_engineer/core/models.py:65-71`
- Create: `src/audio_engineer/core/audio_track.py`
- Create: `tests/core/test_audio_track.py`

- [ ] **Step 1: Write failing tests for AudioTrack**

```python
# tests/core/test_audio_track.py
"""Tests for AudioTrack unified track model."""
import pytest
from audio_engineer.core.audio_track import AudioTrack, TrackType


class TestAudioTrack:
    def test_create_midi_track(self):
        track = AudioTrack(
            name="drums",
            track_type=TrackType.MIDI,
            provider="midi_engine",
        )
        assert track.track_type == TrackType.MIDI
        assert track.provider == "midi_engine"
        assert track.audio_data is None
        assert track.midi_data is None
        assert track.sample_rate is None

    def test_create_audio_track(self):
        track = AudioTrack(
            name="synth_pad",
            track_type=TrackType.AUDIO,
            provider="gemini_lyria",
            audio_data=b"\x00\x01\x02",
            mime_type="audio/mp3",
            sample_rate=44100,
        )
        assert track.track_type == TrackType.AUDIO
        assert track.audio_data == b"\x00\x01\x02"
        assert track.mime_type == "audio/mp3"
        assert track.sample_rate == 44100

    def test_has_audio_data(self):
        empty = AudioTrack(name="empty", track_type=TrackType.AUDIO, provider="test")
        assert not empty.has_audio

        with_data = AudioTrack(
            name="full",
            track_type=TrackType.AUDIO,
            provider="test",
            audio_data=b"\xff",
        )
        assert with_data.has_audio

    def test_has_midi_data(self):
        from audio_engineer.core.models import MidiTrackData, Instrument

        midi = MidiTrackData(
            name="bass", instrument=Instrument.BASS, channel=1, events=[]
        )
        track = AudioTrack(
            name="bass",
            track_type=TrackType.MIDI,
            provider="midi_engine",
            midi_data=midi,
        )
        assert track.has_midi

    def test_duration_seconds_from_audio_metadata(self):
        track = AudioTrack(
            name="clip",
            track_type=TrackType.AUDIO,
            provider="test",
            duration_seconds=30.0,
        )
        assert track.duration_seconds == 30.0

    def test_tags_for_categorization(self):
        track = AudioTrack(
            name="ambient_pad",
            track_type=TrackType.AUDIO,
            provider="gemini_lyria",
            tags=["ambient", "pad", "atmospheric"],
        )
        assert "ambient" in track.tags

    def test_track_type_enum_values(self):
        assert TrackType.MIDI.value == "midi"
        assert TrackType.AUDIO.value == "audio"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_audio_track.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'audio_engineer.core.audio_track'`

- [ ] **Step 3: Add TrackType enum to models.py**

Add after the `SessionStatus` enum (around line 71):

```python
class TrackType(str, Enum):
    """Type of audio track data."""
    MIDI = "midi"
    AUDIO = "audio"
```

- [ ] **Step 4: Create AudioTrack model**

```python
# src/audio_engineer/core/audio_track.py
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
        """Write raw audio bytes to disk."""
        if not self.has_audio:
            raise ValueError(f"Track '{self.name}' has no audio data to save")
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self.audio_data)  # type: ignore[arg-type]
        return out
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/core/test_audio_track.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Lint check**

Run: `ruff check src/audio_engineer/core/audio_track.py tests/core/test_audio_track.py`
Expected: Clean

- [ ] **Step 7: Commit**

```bash
git add src/audio_engineer/core/audio_track.py src/audio_engineer/core/models.py tests/core/test_audio_track.py
git commit -m "feat: add AudioTrack unified model and TrackType enum"
```

---

## Task 2: Provider Base Classes and Request/Result Models

**Files:**
- Create: `src/audio_engineer/providers/__init__.py`
- Create: `src/audio_engineer/providers/base.py`
- Create: `tests/providers/__init__.py`
- Create: `tests/providers/test_base.py`

- [ ] **Step 1: Write failing tests for provider base**

```python
# tests/providers/__init__.py
```

```python
# tests/providers/test_base.py
"""Tests for audio provider base classes and models."""
import pytest
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)
from audio_engineer.core.audio_track import AudioTrack, TrackType


class TestProviderCapability:
    def test_capability_values(self):
        assert ProviderCapability.MIDI_GENERATION.value == "midi_generation"
        assert ProviderCapability.AUDIO_GENERATION.value == "audio_generation"
        assert ProviderCapability.VOCALS.value == "vocals"
        assert ProviderCapability.SOUND_DESIGN.value == "sound_design"
        assert ProviderCapability.AUDIO_ANALYSIS.value == "audio_analysis"


class TestTrackRequest:
    def test_minimal_request(self):
        req = TrackRequest(
            track_name="drums",
            description="heavy rock drums at 140 BPM",
        )
        assert req.track_name == "drums"
        assert req.description == "heavy rock drums at 140 BPM"
        assert req.preferred_provider is None
        assert req.required_capabilities == []

    def test_request_with_provider_override(self):
        req = TrackRequest(
            track_name="synth_pad",
            description="atmospheric pad in C minor",
            preferred_provider="gemini_lyria",
            required_capabilities=[ProviderCapability.AUDIO_GENERATION],
        )
        assert req.preferred_provider == "gemini_lyria"
        assert ProviderCapability.AUDIO_GENERATION in req.required_capabilities

    def test_request_with_session_context(self):
        req = TrackRequest(
            track_name="bass",
            description="walking bass",
            genre="jazz",
            key="Bb major",
            tempo=120,
            duration_seconds=60.0,
        )
        assert req.genre == "jazz"
        assert req.tempo == 120


class TestTrackResult:
    def test_successful_result(self):
        track = AudioTrack(
            name="drums", track_type=TrackType.MIDI, provider="midi_engine"
        )
        result = TrackResult(track=track, success=True, provider_used="midi_engine")
        assert result.success
        assert result.error is None

    def test_failed_result(self):
        result = TrackResult(
            track=None, success=False, provider_used="gemini_lyria",
            error="API quota exceeded",
        )
        assert not result.success
        assert result.error == "API quota exceeded"


class TestAudioProviderABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            AudioProvider()  # type: ignore[abstract]

    def test_concrete_subclass(self):
        class DummyProvider(AudioProvider):
            @property
            def name(self) -> str:
                return "dummy"

            @property
            def capabilities(self) -> list[ProviderCapability]:
                return [ProviderCapability.MIDI_GENERATION]

            def is_available(self) -> bool:
                return True

            def generate_track(self, request: TrackRequest) -> TrackResult:
                track = AudioTrack(
                    name=request.track_name,
                    track_type=TrackType.MIDI,
                    provider=self.name,
                )
                return TrackResult(track=track, success=True, provider_used=self.name)

        provider = DummyProvider()
        assert provider.name == "dummy"
        assert provider.is_available()
        assert ProviderCapability.MIDI_GENERATION in provider.capabilities

        result = provider.generate_track(
            TrackRequest(track_name="test", description="test track")
        )
        assert result.success
        assert result.track is not None
        assert result.track.provider == "dummy"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/providers/test_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'audio_engineer.providers'`

- [ ] **Step 3: Create providers package and base module**

```python
# src/audio_engineer/providers/__init__.py
"""Audio generation providers — pluggable backends for track generation."""
from .base import AudioProvider, ProviderCapability, TrackRequest, TrackResult

__all__ = [
    "AudioProvider",
    "ProviderCapability",
    "TrackRequest",
    "TrackResult",
]
```

```python
# src/audio_engineer/providers/base.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/providers/test_base.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Lint check**

Run: `ruff check src/audio_engineer/providers/ tests/providers/`
Expected: Clean

- [ ] **Step 6: Commit**

```bash
git add src/audio_engineer/providers/__init__.py src/audio_engineer/providers/base.py tests/providers/__init__.py tests/providers/test_base.py
git commit -m "feat: add provider abstraction layer with ABC and request/result models"
```

---

## Task 3: Provider Registry with Capability-Based Routing

**Files:**
- Create: `src/audio_engineer/providers/registry.py`
- Create: `tests/providers/test_registry.py`

- [ ] **Step 1: Write failing tests for registry**

```python
# tests/providers/test_registry.py
"""Tests for provider registry and capability-based routing."""
import pytest
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)
from audio_engineer.providers.registry import ProviderRegistry
from audio_engineer.core.audio_track import AudioTrack, TrackType


class StubMidiProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "stub_midi"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.MIDI_GENERATION]

    def is_available(self) -> bool:
        return True

    def generate_track(self, request: TrackRequest) -> TrackResult:
        track = AudioTrack(
            name=request.track_name, track_type=TrackType.MIDI, provider=self.name
        )
        return TrackResult(track=track, success=True, provider_used=self.name)


class StubAudioProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "stub_audio"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.AUDIO_GENERATION, ProviderCapability.VOCALS]

    def is_available(self) -> bool:
        return True

    def generate_track(self, request: TrackRequest) -> TrackResult:
        track = AudioTrack(
            name=request.track_name,
            track_type=TrackType.AUDIO,
            provider=self.name,
            audio_data=b"\x00",
        )
        return TrackResult(track=track, success=True, provider_used=self.name)


class UnavailableProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "unavailable"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.AUDIO_GENERATION]

    def is_available(self) -> bool:
        return False

    def generate_track(self, request: TrackRequest) -> TrackResult:
        return TrackResult(track=None, success=False, provider_used=self.name, error="Not available")


@pytest.fixture
def registry():
    reg = ProviderRegistry()
    reg.register(StubMidiProvider())
    reg.register(StubAudioProvider())
    reg.register(UnavailableProvider())
    return reg


class TestProviderRegistry:
    def test_register_and_list(self, registry: ProviderRegistry):
        names = registry.list_providers()
        assert "stub_midi" in names
        assert "stub_audio" in names
        assert "unavailable" in names

    def test_list_available(self, registry: ProviderRegistry):
        available = registry.list_available()
        assert "stub_midi" in available
        assert "stub_audio" in available
        assert "unavailable" not in available

    def test_get_provider_by_name(self, registry: ProviderRegistry):
        p = registry.get("stub_midi")
        assert p is not None
        assert p.name == "stub_midi"

    def test_get_unknown_returns_none(self, registry: ProviderRegistry):
        assert registry.get("nonexistent") is None

    def test_find_by_capability(self, registry: ProviderRegistry):
        midi_providers = registry.find_by_capability(ProviderCapability.MIDI_GENERATION)
        assert len(midi_providers) == 1
        assert midi_providers[0].name == "stub_midi"

    def test_find_by_capability_excludes_unavailable(self, registry: ProviderRegistry):
        audio_providers = registry.find_by_capability(ProviderCapability.AUDIO_GENERATION)
        assert len(audio_providers) == 1
        assert audio_providers[0].name == "stub_audio"

    def test_route_with_preferred_provider(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="pad",
            description="ambient pad",
            preferred_provider="stub_audio",
        )
        provider = registry.route(req)
        assert provider is not None
        assert provider.name == "stub_audio"

    def test_route_preferred_unavailable_falls_back(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="pad",
            description="ambient pad",
            preferred_provider="unavailable",
            required_capabilities=[ProviderCapability.AUDIO_GENERATION],
        )
        provider = registry.route(req)
        assert provider is not None
        assert provider.name == "stub_audio"

    def test_route_by_required_capability(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="vocals",
            description="vocal track",
            required_capabilities=[ProviderCapability.VOCALS],
        )
        provider = registry.route(req)
        assert provider is not None
        assert provider.name == "stub_audio"

    def test_route_no_match_returns_none(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="fx",
            description="explosion sound",
            required_capabilities=[ProviderCapability.SOURCE_SEPARATION],
        )
        provider = registry.route(req)
        assert provider is None

    def test_route_default_to_midi(self, registry: ProviderRegistry):
        """When no capabilities required and no preference, prefer MIDI provider."""
        req = TrackRequest(track_name="bass", description="bass line")
        provider = registry.route(req)
        assert provider is not None
        # Should pick an available provider — implementation decides priority
        assert provider.name in ("stub_midi", "stub_audio")

    def test_generate_routes_and_generates(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="drums",
            description="rock drums",
            required_capabilities=[ProviderCapability.MIDI_GENERATION],
        )
        result = registry.generate(req)
        assert result.success
        assert result.track is not None
        assert result.track.name == "drums"

    def test_generate_no_provider_returns_failure(self, registry: ProviderRegistry):
        req = TrackRequest(
            track_name="fx",
            description="laser beam",
            required_capabilities=[ProviderCapability.SOURCE_SEPARATION],
        )
        result = registry.generate(req)
        assert not result.success
        assert "No provider" in result.error
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/providers/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'audio_engineer.providers.registry'`

- [ ] **Step 3: Implement ProviderRegistry**

```python
# src/audio_engineer/providers/registry.py
"""Provider registry with capability-based routing."""
from __future__ import annotations

import logging
from typing import Optional

from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Manages registered audio providers and routes requests to them.

    Routing priority:
    1. If ``preferred_provider`` is set and available, use it.
    2. If ``required_capabilities`` are set, find the first available
       provider that supports all of them.
    3. Fall back to the first available provider.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AudioProvider] = {}

    def register(self, provider: AudioProvider) -> None:
        """Register a provider. Overwrites existing with same name."""
        self._providers[provider.name] = provider
        logger.info("Registered provider: %s (capabilities: %s)",
                     provider.name, [c.value for c in provider.capabilities])

    def get(self, name: str) -> Optional[AudioProvider]:
        """Get a provider by name, or None."""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """All registered provider names."""
        return list(self._providers.keys())

    def list_available(self) -> list[str]:
        """Names of providers that are currently available."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def find_by_capability(
        self, capability: ProviderCapability
    ) -> list[AudioProvider]:
        """Return available providers that support the given capability."""
        return [
            p for p in self._providers.values()
            if p.is_available() and p.supports(capability)
        ]

    def route(self, request: TrackRequest) -> Optional[AudioProvider]:
        """Select the best provider for a request.

        Returns None if no suitable provider is found.
        """
        # 1. Preferred provider override
        if request.preferred_provider:
            preferred = self.get(request.preferred_provider)
            if preferred and preferred.is_available():
                return preferred
            logger.debug(
                "Preferred provider '%s' unavailable, falling back",
                request.preferred_provider,
            )

        # 2. Match by required capabilities
        if request.required_capabilities:
            for provider in self._providers.values():
                if not provider.is_available():
                    continue
                if all(provider.supports(c) for c in request.required_capabilities):
                    return provider
            return None

        # 3. Default: first available provider
        for provider in self._providers.values():
            if provider.is_available():
                return provider

        return None

    def generate(self, request: TrackRequest) -> TrackResult:
        """Route the request and generate the track.

        Convenience method that combines routing and generation.
        """
        provider = self.route(request)
        if provider is None:
            return TrackResult(
                track=None,
                success=False,
                provider_used="none",
                error=f"No provider found for request '{request.track_name}' "
                      f"with capabilities {[c.value for c in request.required_capabilities]}",
            )

        logger.info("Routing '%s' to provider '%s'", request.track_name, provider.name)
        return provider.generate_track(request)
```

- [ ] **Step 4: Update providers __init__.py**

```python
# src/audio_engineer/providers/__init__.py
"""Audio generation providers — pluggable backends for track generation."""
from .base import AudioProvider, ProviderCapability, TrackRequest, TrackResult
from .registry import ProviderRegistry

__all__ = [
    "AudioProvider",
    "ProviderCapability",
    "ProviderRegistry",
    "TrackRequest",
    "TrackResult",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/providers/test_registry.py -v`
Expected: All 13 tests PASS

- [ ] **Step 6: Lint check**

Run: `ruff check src/audio_engineer/providers/registry.py tests/providers/test_registry.py`
Expected: Clean

- [ ] **Step 7: Commit**

```bash
git add src/audio_engineer/providers/registry.py src/audio_engineer/providers/__init__.py tests/providers/test_registry.py
git commit -m "feat: add ProviderRegistry with capability-based routing"
```

---

## Task 4: MIDI Provider — Wrap Existing Engine

**Files:**
- Create: `src/audio_engineer/providers/midi_provider.py`
- Create: `tests/providers/test_midi_provider.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/providers/test_midi_provider.py
"""Tests for MIDI engine provider wrapper."""
import pytest
from audio_engineer.providers.midi_provider import MidiProvider
from audio_engineer.providers.base import ProviderCapability, TrackRequest
from audio_engineer.core.audio_track import TrackType


class TestMidiProvider:
    @pytest.fixture
    def provider(self):
        return MidiProvider()

    def test_name(self, provider: MidiProvider):
        assert provider.name == "midi_engine"

    def test_capabilities(self, provider: MidiProvider):
        assert ProviderCapability.MIDI_GENERATION in provider.capabilities

    def test_is_available(self, provider: MidiProvider):
        assert provider.is_available()

    def test_generate_drum_track(self, provider: MidiProvider):
        req = TrackRequest(
            track_name="drums",
            description="rock drums",
            instrument="drums",
            genre="classic_rock",
            key="C major",
            tempo=120,
        )
        result = provider.generate_track(req)
        assert result.success
        assert result.track is not None
        assert result.track.track_type == TrackType.MIDI
        assert result.track.midi_data is not None
        assert result.track.midi_data.name == "drums"
        assert len(result.track.midi_data.events) > 0

    def test_generate_bass_track(self, provider: MidiProvider):
        # Bass needs drum context, so generate drums first
        drum_req = TrackRequest(
            track_name="drums",
            description="rock drums",
            instrument="drums",
            genre="classic_rock",
            key="C major",
            tempo=120,
        )
        drum_result = provider.generate_track(drum_req)

        bass_req = TrackRequest(
            track_name="bass",
            description="rock bass",
            instrument="bass",
            genre="classic_rock",
            key="C major",
            tempo=120,
            reference_track_names=["drums"],
        )
        result = provider.generate_track(bass_req)
        assert result.success
        assert result.track is not None
        assert result.track.midi_data is not None

    def test_generate_unknown_instrument_returns_failure(self, provider: MidiProvider):
        req = TrackRequest(
            track_name="theremin",
            description="theremin solo",
            instrument="theremin",
            genre="classic_rock",
            key="C major",
            tempo=120,
        )
        result = provider.generate_track(req)
        assert not result.success
        assert result.error is not None

    def test_supported_instruments(self, provider: MidiProvider):
        instruments = provider.supported_instruments
        assert "drums" in instruments
        assert "bass" in instruments
        assert "electric_guitar" in instruments
        assert "keys" in instruments
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/providers/test_midi_provider.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement MidiProvider**

```python
# src/audio_engineer/providers/midi_provider.py
"""Provider that wraps the existing MIDI engine and musician agents."""
from __future__ import annotations

import logging
from typing import Any, Optional

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.models import (
    Genre,
    Instrument,
    KeySignature,
    Mode,
    NoteName,
    SectionDef,
    SessionConfig,
    BandConfig,
    BandMemberConfig,
)
from audio_engineer.core.music_theory import ChordProgression, ProgressionFactory
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent
from audio_engineer.agents.musician.bassist import BassistAgent
from audio_engineer.agents.musician.guitarist import GuitaristAgent
from audio_engineer.agents.musician.keyboardist import KeyboardistAgent
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Map instrument name strings to agent constructors
_INSTRUMENT_AGENTS: dict[str, type] = {
    "drums": DrummerAgent,
    "bass": BassistAgent,
    "electric_guitar": GuitaristAgent,
    "acoustic_guitar": GuitaristAgent,
    "keys": KeyboardistAgent,
}


class MidiProvider(AudioProvider):
    """Generates MIDI tracks using the built-in musician agents.

    This wraps the existing agent system as a pluggable provider so it
    can participate in the registry alongside AI audio providers.
    """

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm
        self._generated_tracks: dict[str, AudioTrack] = {}

    @property
    def name(self) -> str:
        return "midi_engine"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.MIDI_GENERATION]

    @property
    def supported_instruments(self) -> list[str]:
        return list(_INSTRUMENT_AGENTS.keys())

    def is_available(self) -> bool:
        return True

    def generate_track(self, request: TrackRequest) -> TrackResult:
        instrument = request.instrument
        if not instrument or instrument not in _INSTRUMENT_AGENTS:
            return TrackResult(
                track=None,
                success=False,
                provider_used=self.name,
                error=f"MIDI provider does not support instrument '{instrument}'. "
                      f"Supported: {self.supported_instruments}",
            )

        try:
            agent_cls = _INSTRUMENT_AGENTS[instrument]
            agent = agent_cls(llm=self._llm)
            context = self._build_context(request)
            midi_data = agent.generate_part(context)

            track = AudioTrack(
                name=request.track_name,
                track_type=TrackType.MIDI,
                provider=self.name,
                midi_data=midi_data,
                tags=[instrument, request.genre or "unknown"],
            )
            self._generated_tracks[request.track_name] = track
            return TrackResult(track=track, success=True, provider_used=self.name)

        except Exception as e:
            logger.error("MIDI generation failed for '%s': %s", request.track_name, e)
            return TrackResult(
                track=None, success=False, provider_used=self.name, error=str(e)
            )

    def _build_context(self, request: TrackRequest) -> SessionContext:
        """Build a SessionContext from a TrackRequest."""
        genre = self._parse_genre(request.genre)
        key_root, key_mode = self._parse_key(request.key)

        config = SessionConfig(
            genre=genre,
            tempo=request.tempo or 120,
            key=KeySignature(root=key_root, mode=key_mode),
            band=BandConfig(members=[
                BandMemberConfig(instrument=Instrument(request.instrument or "drums"))
            ]),
        )

        progressions = self._get_progressions(genre, key_root.value, key_mode.value)
        chord_progs: dict[str, ChordProgression] = {}
        for section in config.structure:
            section_name = section.name.lower()
            if section_name in ("chorus", "outro"):
                chord_progs[section_name] = progressions.get("chorus", progressions["verse"])
            else:
                chord_progs[section_name] = progressions.get("verse", progressions["verse"])

        # Inject reference tracks from previous generations
        existing: dict[str, Any] = {}
        for ref_name in request.reference_track_names:
            if ref_name in self._generated_tracks:
                ref = self._generated_tracks[ref_name]
                if ref.midi_data:
                    existing[ref.midi_data.instrument.value] = ref.midi_data

        return SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions=chord_progs,
            existing_tracks=existing,
        )

    @staticmethod
    def _parse_genre(genre: Optional[str]) -> Genre:
        if not genre:
            return Genre.CLASSIC_ROCK
        try:
            return Genre(genre)
        except ValueError:
            return Genre.CLASSIC_ROCK

    @staticmethod
    def _parse_key(key: Optional[str]) -> tuple[NoteName, Mode]:
        if not key:
            return NoteName.C, Mode.MAJOR
        parts = key.split()
        root = NoteName.C
        mode = Mode.MAJOR
        if parts:
            for n in NoteName:
                if n.value == parts[0]:
                    root = n
                    break
        if len(parts) > 1:
            for m in Mode:
                if m.value == parts[1].lower():
                    mode = m
                    break
        return root, mode

    @staticmethod
    def _get_progressions(
        genre: Genre, key_root: str, key_mode: str,
    ) -> dict[str, ChordProgression]:
        if genre == Genre.BLUES:
            return {
                "verse": ProgressionFactory.twelve_bar_blues(key_root),
                "chorus": ProgressionFactory.twelve_bar_blues(key_root),
            }
        elif genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK):
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.POP:
            return {
                "verse": ProgressionFactory.pop_I_V_vi_IV(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        else:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/providers/test_midi_provider.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Lint check**

Run: `ruff check src/audio_engineer/providers/midi_provider.py tests/providers/test_midi_provider.py`
Expected: Clean

- [ ] **Step 6: Commit**

```bash
git add src/audio_engineer/providers/midi_provider.py tests/providers/test_midi_provider.py
git commit -m "feat: add MidiProvider wrapping existing musician agents"
```

---

## Task 5: Gemini Lyria Provider

**Files:**
- Create: `src/audio_engineer/providers/gemini_provider.py`
- Create: `tests/providers/test_gemini_provider.py`

- [ ] **Step 1: Write failing tests (mocked — no real API calls)**

```python
# tests/providers/test_gemini_provider.py
"""Tests for Gemini Lyria provider (mocked API)."""
import pytest
from unittest.mock import MagicMock, patch
from audio_engineer.providers.gemini_provider import GeminiLyriaProvider
from audio_engineer.providers.base import ProviderCapability, TrackRequest
from audio_engineer.core.audio_track import TrackType


class TestGeminiLyriaProvider:
    def test_name(self):
        with patch("audio_engineer.providers.gemini_provider._gemini_importable", return_value=False):
            provider = GeminiLyriaProvider()
        assert provider.name == "gemini_lyria"

    def test_capabilities(self):
        with patch("audio_engineer.providers.gemini_provider._gemini_importable", return_value=False):
            provider = GeminiLyriaProvider()
        caps = provider.capabilities
        assert ProviderCapability.AUDIO_GENERATION in caps
        assert ProviderCapability.VOCALS in caps
        assert ProviderCapability.TEXT_TO_SPEECH in caps

    def test_not_available_without_genai(self):
        with patch("audio_engineer.providers.gemini_provider._gemini_importable", return_value=False):
            provider = GeminiLyriaProvider()
        assert not provider.is_available()

    def test_generate_returns_audio_track(self):
        mock_music_agent = MagicMock()
        mock_music_agent.generate_clip.return_value = MagicMock(
            audio_data=b"\xff\xfb\x90\x00",  # fake mp3 bytes
            lyrics=None,
            mime_type="audio/mp3",
        )

        provider = GeminiLyriaProvider()
        provider._music_agent = mock_music_agent
        provider._available = True

        req = TrackRequest(
            track_name="synth_pad",
            description="atmospheric synth pad in C minor, dreamy",
            genre="ambient",
            key="C minor",
            tempo=80,
        )
        result = provider.generate_track(req)

        assert result.success
        assert result.track is not None
        assert result.track.track_type == TrackType.AUDIO
        assert result.track.audio_data == b"\xff\xfb\x90\x00"
        assert result.track.provider == "gemini_lyria"
        mock_music_agent.generate_clip.assert_called_once()

    def test_generate_full_song_for_long_duration(self):
        mock_music_agent = MagicMock()
        mock_music_agent.generate_song.return_value = MagicMock(
            audio_data=b"\xff\xfb\x90\x00",
            lyrics="La la la",
            mime_type="audio/mp3",
        )

        provider = GeminiLyriaProvider()
        provider._music_agent = mock_music_agent
        provider._available = True

        req = TrackRequest(
            track_name="full_track",
            description="complete jazz ballad",
            duration_seconds=120.0,
        )
        result = provider.generate_track(req)

        assert result.success
        mock_music_agent.generate_song.assert_called_once()

    def test_generate_failure_returns_error(self):
        mock_music_agent = MagicMock()
        mock_music_agent.generate_clip.side_effect = RuntimeError("API quota exceeded")

        provider = GeminiLyriaProvider()
        provider._music_agent = mock_music_agent
        provider._available = True

        req = TrackRequest(track_name="test", description="test track")
        result = provider.generate_track(req)

        assert not result.success
        assert "API quota exceeded" in result.error

    def test_build_prompt_from_request(self):
        provider = GeminiLyriaProvider()
        req = TrackRequest(
            track_name="guitar",
            description="overdriven electric guitar riff",
            genre="hard_rock",
            key="E minor",
            tempo=140,
            style_hints=["aggressive", "palm-muted"],
        )
        prompt = provider._build_prompt(req)
        assert "hard_rock" in prompt or "hard rock" in prompt
        assert "E minor" in prompt
        assert "140" in prompt
        assert "overdriven electric guitar riff" in prompt
        assert "aggressive" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/providers/test_gemini_provider.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement GeminiLyriaProvider**

```python
# src/audio_engineer/providers/gemini_provider.py
"""Provider wrapping Google Gemini Lyria for AI audio generation."""
from __future__ import annotations

import logging
from typing import Any, Optional

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Duration threshold: above this, use full-song model instead of clip
_FULL_SONG_THRESHOLD_SECONDS = 45.0


def _gemini_importable() -> bool:
    try:
        import audio_engineer.gemini  # noqa: F401
        return True
    except Exception:
        return False


class GeminiLyriaProvider(AudioProvider):
    """Generate audio tracks via Google Lyria 3 models.

    Falls back gracefully when google-genai is not installed.
    Uses clip model for short segments, pro model for full songs.
    """

    def __init__(self) -> None:
        self._music_agent: Any = None
        self._available = False

        if _gemini_importable():
            try:
                from audio_engineer.gemini import MusicGenerationAgent
                self._music_agent = MusicGenerationAgent()
                self._available = True
                logger.info("Gemini Lyria provider initialized")
            except Exception as exc:
                logger.debug("Gemini Lyria init failed: %s", exc)

    @property
    def name(self) -> str:
        return "gemini_lyria"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.AUDIO_GENERATION,
            ProviderCapability.VOCALS,
            ProviderCapability.TEXT_TO_SPEECH,
        ]

    def is_available(self) -> bool:
        return self._available

    def generate_track(self, request: TrackRequest) -> TrackResult:
        if not self._available or self._music_agent is None:
            return TrackResult(
                track=None, success=False, provider_used=self.name,
                error="Gemini Lyria is not available (google-genai not installed or no API key)",
            )

        try:
            prompt = self._build_prompt(request)
            use_full_song = (
                request.duration_seconds is not None
                and request.duration_seconds > _FULL_SONG_THRESHOLD_SECONDS
            )

            if use_full_song:
                gen_result = self._music_agent.generate_song(
                    prompt, instrumental=True
                )
            else:
                gen_result = self._music_agent.generate_clip(
                    prompt, instrumental=True
                )

            track = AudioTrack(
                name=request.track_name,
                track_type=TrackType.AUDIO,
                provider=self.name,
                audio_data=gen_result.audio_data,
                mime_type=gen_result.mime_type,
                duration_seconds=request.duration_seconds,
                tags=request.style_hints[:],
            )

            return TrackResult(track=track, success=True, provider_used=self.name)

        except Exception as e:
            logger.error("Gemini Lyria generation failed: %s", e)
            return TrackResult(
                track=None, success=False, provider_used=self.name, error=str(e),
            )

    def _build_prompt(self, request: TrackRequest) -> str:
        """Construct a Lyria-friendly prompt from the track request."""
        parts: list[str] = [request.description]

        if request.genre:
            parts.append(f"Genre: {request.genre.replace('_', ' ')}.")
        if request.key:
            parts.append(f"Key: {request.key}.")
        if request.tempo:
            parts.append(f"Tempo: {request.tempo} BPM.")
        if request.style_hints:
            parts.append(f"Style: {', '.join(request.style_hints)}.")

        return " ".join(parts)
```

- [ ] **Step 4: Update providers __init__.py**

```python
# src/audio_engineer/providers/__init__.py
"""Audio generation providers — pluggable backends for track generation."""
from .base import AudioProvider, ProviderCapability, TrackRequest, TrackResult
from .registry import ProviderRegistry
from .midi_provider import MidiProvider
from .gemini_provider import GeminiLyriaProvider

__all__ = [
    "AudioProvider",
    "GeminiLyriaProvider",
    "MidiProvider",
    "ProviderCapability",
    "ProviderRegistry",
    "TrackRequest",
    "TrackResult",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/providers/test_gemini_provider.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Lint check**

Run: `ruff check src/audio_engineer/providers/gemini_provider.py tests/providers/test_gemini_provider.py`
Expected: Clean

- [ ] **Step 7: Commit**

```bash
git add src/audio_engineer/providers/gemini_provider.py src/audio_engineer/providers/__init__.py tests/providers/test_gemini_provider.py
git commit -m "feat: add GeminiLyriaProvider for AI audio generation"
```

---

## Task 6: TrackComposer — Layer MIDI + Audio Stems

**Files:**
- Create: `src/audio_engineer/core/track_composer.py`
- Create: `tests/core/test_track_composer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/test_track_composer.py
"""Tests for TrackComposer that layers multiple AudioTracks."""
import pytest
from pathlib import Path
from audio_engineer.core.track_composer import TrackComposer
from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.models import MidiTrackData, Instrument, NoteEvent


@pytest.fixture
def midi_track():
    return AudioTrack(
        name="drums",
        track_type=TrackType.MIDI,
        provider="midi_engine",
        midi_data=MidiTrackData(
            name="drums",
            instrument=Instrument.DRUMS,
            channel=9,
            events=[
                NoteEvent(pitch=36, velocity=100, start_tick=0, duration_ticks=240, channel=9),
            ],
            program=0,
        ),
    )


@pytest.fixture
def audio_track():
    return AudioTrack(
        name="synth_pad",
        track_type=TrackType.AUDIO,
        provider="gemini_lyria",
        audio_data=b"\xff\xfb\x90\x00" * 100,
        mime_type="audio/mp3",
    )


class TestTrackComposer:
    def test_create_composer(self):
        composer = TrackComposer()
        assert composer.tracks == []

    def test_add_track(self, midi_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        assert len(composer.tracks) == 1
        assert composer.tracks[0].name == "drums"

    def test_add_multiple_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        assert len(composer.tracks) == 2

    def test_get_midi_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        midi_tracks = composer.get_midi_tracks()
        assert len(midi_tracks) == 1
        assert midi_tracks[0].name == "drums"

    def test_get_audio_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        audio_tracks = composer.get_audio_tracks()
        assert len(audio_tracks) == 1
        assert audio_tracks[0].name == "synth_pad"

    def test_export_midi(self, midi_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(midi_track)
        out = composer.export_midi(tmp_path / "out.mid", tempo=120)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_audio_stems(self, audio_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(audio_track)
        stems = composer.export_audio_stems(tmp_path)
        assert len(stems) == 1
        assert stems[0].exists()

    def test_export_all(self, midi_track: AudioTrack, audio_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        files = composer.export_all(tmp_path, tempo=120)
        # Should produce at least: MIDI file + 1 audio stem
        assert len(files) >= 2

    def test_manifest(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        manifest = composer.manifest()
        assert len(manifest) == 2
        assert manifest[0]["name"] == "drums"
        assert manifest[0]["type"] == "midi"
        assert manifest[1]["name"] == "synth_pad"
        assert manifest[1]["type"] == "audio"

    def test_clear(self, midi_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.clear()
        assert composer.tracks == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_track_composer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement TrackComposer**

```python
# src/audio_engineer/core/track_composer.py
"""Compose multiple AudioTracks (MIDI + audio) into layered output."""
from __future__ import annotations

import logging
from pathlib import Path

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.midi_engine import MidiEngine

logger = logging.getLogger(__name__)


class TrackComposer:
    """Collects AudioTracks and exports them as layered stems.

    MIDI tracks are merged into a single .mid file.
    Audio tracks are exported as individual stem files.
    """

    def __init__(self) -> None:
        self.tracks: list[AudioTrack] = []
        self._midi_engine = MidiEngine()

    def add_track(self, track: AudioTrack) -> None:
        self.tracks.append(track)

    def clear(self) -> None:
        self.tracks.clear()

    def get_midi_tracks(self) -> list[AudioTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.MIDI]

    def get_audio_tracks(self) -> list[AudioTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.AUDIO]

    def export_midi(self, path: Path | str, tempo: int = 120) -> Path:
        """Merge all MIDI tracks into a single .mid file."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        midi_tracks = [t.midi_data for t in self.get_midi_tracks() if t.midi_data]
        if not midi_tracks:
            raise ValueError("No MIDI tracks to export")

        midi_file = self._midi_engine.merge_tracks(midi_tracks, tempo)
        self._midi_engine.export_midi(midi_file, out)
        logger.info("Exported MIDI: %s (%d tracks)", out, len(midi_tracks))
        return out

    def export_audio_stems(self, directory: Path | str) -> list[Path]:
        """Save each audio track as an individual stem file."""
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        stems: list[Path] = []

        for track in self.get_audio_tracks():
            if not track.has_audio:
                continue
            ext = _mime_to_ext(track.mime_type)
            stem_path = out_dir / f"{track.name}{ext}"
            track.save_audio(stem_path)
            stems.append(stem_path)
            logger.info("Exported audio stem: %s", stem_path)

        return stems

    def export_all(self, directory: Path | str, tempo: int = 120) -> list[Path]:
        """Export both MIDI and audio stems to a directory."""
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []

        # MIDI
        midi_tracks = self.get_midi_tracks()
        if midi_tracks:
            midi_path = out_dir / "combined.mid"
            self.export_midi(midi_path, tempo)
            files.append(midi_path)

        # Audio stems
        files.extend(self.export_audio_stems(out_dir))

        return files

    def manifest(self) -> list[dict]:
        """Return a summary of all tracks for serialization."""
        return [
            {
                "name": t.name,
                "type": t.track_type.value,
                "provider": t.provider,
                "has_data": t.has_audio or t.has_midi,
                "tags": t.tags,
            }
            for t in self.tracks
        ]


def _mime_to_ext(mime_type: str) -> str:
    mapping = {
        "audio/mp3": ".mp3",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/flac": ".flac",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
    }
    return mapping.get(mime_type, ".bin")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_track_composer.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Lint check**

Run: `ruff check src/audio_engineer/core/track_composer.py tests/core/test_track_composer.py`
Expected: Clean

- [ ] **Step 6: Commit**

```bash
git add src/audio_engineer/core/track_composer.py tests/core/test_track_composer.py
git commit -m "feat: add TrackComposer for layering MIDI + audio stems"
```

---

## Task 7: Wire Provider Registry into Orchestrator

**Files:**
- Modify: `src/audio_engineer/agents/orchestrator.py`
- Modify: `tests/agents/test_orchestrator.py`

- [ ] **Step 1: Write test for provider-based orchestrator**

Append to existing test file:

```python
# tests/agents/test_orchestrator.py — add to end
class TestOrchestratorProviderRegistry:
    def test_orchestrator_has_provider_registry(self, tmp_path):
        from audio_engineer.agents.orchestrator import SessionOrchestrator
        orch = SessionOrchestrator(output_dir=tmp_path)
        assert orch.provider_registry is not None

    def test_registry_has_midi_provider(self, tmp_path):
        from audio_engineer.agents.orchestrator import SessionOrchestrator
        orch = SessionOrchestrator(output_dir=tmp_path)
        available = orch.provider_registry.list_available()
        assert "midi_engine" in available

    def test_registry_lists_all_providers(self, tmp_path):
        from audio_engineer.agents.orchestrator import SessionOrchestrator
        orch = SessionOrchestrator(output_dir=tmp_path)
        all_names = orch.provider_registry.list_providers()
        # At minimum: midi_engine. Gemini if available.
        assert "midi_engine" in all_names

    def test_session_produces_track_composer(self, tmp_path):
        from audio_engineer.agents.orchestrator import SessionOrchestrator
        from audio_engineer.core.models import SessionConfig
        orch = SessionOrchestrator(output_dir=tmp_path)
        session = orch.create_session(SessionConfig())
        session = orch.run_session(session)
        # The composer should have been used internally
        assert session.status.value == "complete"
        assert len(session.output_files) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_orchestrator.py::TestOrchestratorProviderRegistry -v`
Expected: FAIL — `AttributeError: 'SessionOrchestrator' object has no attribute 'provider_registry'`

- [ ] **Step 3: Add provider registry to orchestrator**

Update `src/audio_engineer/agents/orchestrator.py`. Add these imports near the top (after line 22):

```python
from audio_engineer.providers import ProviderRegistry, MidiProvider, GeminiLyriaProvider
from audio_engineer.core.track_composer import TrackComposer
```

Then in `SessionOrchestrator.__init__` (after line 51, after `self.mastering = ...`), add:

```python
        # Provider registry
        self.provider_registry = ProviderRegistry()
        self.provider_registry.register(MidiProvider(llm=llm))
        self.provider_registry.register(GeminiLyriaProvider())
```

No other changes to `__init__` — the existing agents stay functional for now. The registry is additive.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_orchestrator.py -v`
Expected: All tests PASS (both old and new)

- [ ] **Step 5: Verify full test suite still passes**

Run: `pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Lint check**

Run: `ruff check src/audio_engineer/agents/orchestrator.py`
Expected: Clean

- [ ] **Step 7: Commit**

```bash
git add src/audio_engineer/agents/orchestrator.py tests/agents/test_orchestrator.py
git commit -m "feat: wire provider registry into SessionOrchestrator"
```

---

## Task 8: New MCP Tools — generate_audio_track and list_providers

**Files:**
- Modify: `src/audio_engineer/mcp_server.py`

- [ ] **Step 1: Add list_providers MCP tool**

Add after the existing `list_root_notes` tool in `mcp_server.py`:

```python
@mcp.tool()
def list_providers() -> str:
    """List all registered audio generation providers and their capabilities.

    Returns a JSON object mapping provider names to their capabilities and
    availability status. Use this to understand which providers can generate
    which types of tracks.
    """
    from audio_engineer.providers.base import ProviderCapability
    registry = _orchestrator.provider_registry
    result = {}
    for name in registry.list_providers():
        provider = registry.get(name)
        if provider:
            result[name] = {
                "available": provider.is_available(),
                "capabilities": [c.value for c in provider.capabilities],
            }
    return json.dumps(result, indent=2)
```

- [ ] **Step 2: Add generate_audio_track MCP tool**

Add after `list_providers`:

```python
@mcp.tool()
def generate_audio_track(
    track_name: str,
    description: str,
    genre: str = "",
    key: str = "C major",
    tempo: int = 120,
    instrument: str = "",
    preferred_provider: str = "",
    style_hints: Optional[list[str]] = None,
    duration_seconds: Optional[float] = None,
) -> str:
    """Generate a single audio track using the best available provider.

    This is the main entry point for generating individual tracks that can
    be layered together. The system automatically routes to the best provider
    based on the request, or you can specify a preferred_provider.

    For MIDI instrument tracks (drums, bass, guitar, keys), the midi_engine
    provider is used. For AI-generated audio (atmospheric pads, complex
    arrangements, vocals), the gemini_lyria provider is used.

    Args:
        track_name: Identifier for this track (e.g. "drums", "synth_pad").
        description: Natural language description of what to generate.
        genre: Musical genre (e.g. "jazz", "electronic", "cinematic").
        key: Key signature (e.g. "C major", "E minor").
        tempo: Beats per minute (40-300).
        instrument: Specific instrument (e.g. "drums", "bass", "electric_guitar").
        preferred_provider: Force a specific provider ("midi_engine" or "gemini_lyria").
        style_hints: Additional style descriptors (e.g. ["aggressive", "palm-muted"]).
        duration_seconds: Target duration. Over 45s uses full-song generation.

    Returns:
        JSON with track info, provider used, and file path if audio was saved.
    """
    from audio_engineer.providers.base import TrackRequest, ProviderCapability

    capabilities: list[ProviderCapability] = []
    if instrument in ("drums", "bass", "electric_guitar", "acoustic_guitar", "keys"):
        capabilities.append(ProviderCapability.MIDI_GENERATION)
    elif not preferred_provider:
        capabilities.append(ProviderCapability.AUDIO_GENERATION)

    request = TrackRequest(
        track_name=track_name,
        description=description,
        preferred_provider=preferred_provider or None,
        required_capabilities=capabilities,
        genre=genre or None,
        key=key or None,
        tempo=tempo,
        instrument=instrument or None,
        style_hints=style_hints or [],
        duration_seconds=duration_seconds,
    )

    registry = _orchestrator.provider_registry
    result = registry.generate(request)

    response: dict = {
        "success": result.success,
        "provider_used": result.provider_used,
        "track_name": track_name,
    }

    if result.error:
        response["error"] = result.error

    if result.track and result.track.has_audio:
        out_dir = _DEFAULT_OUTPUT / "tracks"
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = ".mp3" if "mp3" in result.track.mime_type else ".wav"
        path = out_dir / f"{track_name}{ext}"
        result.track.save_audio(path)
        response["file_path"] = str(path.resolve())
        response["mime_type"] = result.track.mime_type

    if result.track and result.track.has_midi:
        from audio_engineer.core.midi_engine import MidiEngine
        out_dir = _DEFAULT_OUTPUT / "tracks"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{track_name}.mid"
        engine = MidiEngine()
        engine.export_track(result.track.midi_data, path, tempo)
        response["file_path"] = str(path.resolve())

    return json.dumps(response, indent=2)
```

- [ ] **Step 3: Run lint**

Run: `ruff check src/audio_engineer/mcp_server.py`
Expected: Clean

- [ ] **Step 4: Verify existing tests still pass**

Run: `pytest -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/audio_engineer/mcp_server.py
git commit -m "feat: add generate_audio_track and list_providers MCP tools"
```

---

## Task 9: Settings Update for Provider Configuration

**Files:**
- Modify: `src/audio_engineer/config/settings.py`

- [ ] **Step 1: Add provider settings**

Add to `AudioEngineerSettings` class in `settings.py`:

```python
    # Providers
    default_audio_provider: str = "gemini_lyria"  # default for audio generation
    default_midi_provider: str = "midi_engine"    # default for MIDI generation
    enable_gemini_provider: bool = True
    enable_midi_provider: bool = True
```

- [ ] **Step 2: Lint check**

Run: `ruff check src/audio_engineer/config/settings.py`
Expected: Clean

- [ ] **Step 3: Commit**

```bash
git add src/audio_engineer/config/settings.py
git commit -m "feat: add provider configuration to settings"
```

---

## Task 10: Full Integration Test

**Files:**
- Create: `tests/test_provider_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_provider_integration.py
"""Integration test: generate tracks through provider registry end-to-end."""
import pytest
from pathlib import Path

from audio_engineer.providers import (
    ProviderRegistry,
    MidiProvider,
    ProviderCapability,
    TrackRequest,
)
from audio_engineer.core.track_composer import TrackComposer


class TestProviderIntegration:
    @pytest.fixture
    def registry(self):
        reg = ProviderRegistry()
        reg.register(MidiProvider())
        return reg

    def test_generate_full_band_via_registry(self, registry: ProviderRegistry, tmp_path: Path):
        """Generate drums, bass, guitar via MIDI provider and compose."""
        composer = TrackComposer()

        instruments = [
            ("drums", "rock drums with fills"),
            ("bass", "driving rock bass line"),
            ("electric_guitar", "overdriven power chords"),
        ]

        for instrument, desc in instruments:
            req = TrackRequest(
                track_name=instrument,
                description=desc,
                instrument=instrument,
                genre="classic_rock",
                key="E minor",
                tempo=130,
                required_capabilities=[ProviderCapability.MIDI_GENERATION],
            )
            result = registry.generate(req)
            assert result.success, f"Failed to generate {instrument}: {result.error}"
            assert result.track is not None
            composer.add_track(result.track)

        assert len(composer.tracks) == 3
        assert len(composer.get_midi_tracks()) == 3

        # Export
        files = composer.export_all(tmp_path, tempo=130)
        assert len(files) >= 1  # At least the combined MIDI
        midi_file = tmp_path / "combined.mid"
        assert midi_file.exists()
        assert midi_file.stat().st_size > 0

    def test_manifest_describes_all_tracks(self, registry: ProviderRegistry):
        composer = TrackComposer()

        req = TrackRequest(
            track_name="drums",
            description="test drums",
            instrument="drums",
            genre="classic_rock",
            key="C major",
            tempo=120,
            required_capabilities=[ProviderCapability.MIDI_GENERATION],
        )
        result = registry.generate(req)
        assert result.success
        composer.add_track(result.track)

        manifest = composer.manifest()
        assert len(manifest) == 1
        assert manifest[0]["name"] == "drums"
        assert manifest[0]["type"] == "midi"
        assert manifest[0]["provider"] == "midi_engine"
        assert manifest[0]["has_data"] is True
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_provider_integration.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Final lint**

Run: `ruff check src tests`
Expected: Clean

- [ ] **Step 5: Commit**

```bash
git add tests/test_provider_integration.py
git commit -m "test: add provider integration tests for full band generation"
```

---

## Future Phases (Reference)

### Phase 2: LLM-Driven Composition
- **Prompt Composer Agent**: Takes natural language ("dark cinematic trailer with electronic elements") and produces a list of `TrackRequest` objects with instruments, providers, and descriptions.
- **Dynamic genre system**: Replace the fixed `Genre` enum with free-text genres that the LLM interprets. The MIDI provider falls back to the closest matching preset; audio providers handle any genre natively.
- **Arrangement generator**: LLM designs song structure (sections, bars, intensity curves, instrumentation per section).

### Phase 3: Expanded Track Types
- **VocalistProvider**: Wraps Gemini TTS for spoken/sung vocal tracks. Add `ProviderCapability.VOCALS` routing.
- **SoundDesignProvider**: Generates ambient textures, foley, risers, impacts. Could use Stable Audio, AudioGen, or Lyria with sound-effect-specific prompts.
- **Additional providers**: MusicGen (Meta), Stable Audio (Stability AI), Udio API, Suno API — each implements `AudioProvider` and registers with the registry.

### Phase 4: Post-Production Pipeline
- **SourceSeparationProvider**: Wraps Demucs or similar model to split reference audio into stems (drums, bass, vocals, other).
- **EffectsProcessor**: Applies reverb, delay, EQ, compression to AudioTracks. Uses pydub for basic effects, optionally routes to Gemini for AI-suggested processing.
- **MasteringChain**: Enhanced mastering that analyzes the composed mix and applies loudness normalization, stereo width, limiting.

### Phase 5: Analysis Feedback Loop
- **AudioAnalysisAgent** (already exists in Gemini module): Evaluate generated tracks for quality, genre accuracy, mix balance.
- **Iterative refinement**: Generate → analyze → re-generate tracks that don't meet quality thresholds.
- **Multi-pass composition**: First pass generates core tracks, second pass adds complementary layers based on analysis.

---

## Self-Review Checklist

- [x] **Spec coverage**: All brainstorming decisions are reflected — hybrid MIDI + audio, capability routing with user override, provider abstraction, layered tracks, full production toolkit (phases 1-5).
- [x] **Placeholder scan**: No TBDs, TODOs, or "implement later" patterns. All code is complete.
- [x] **Type consistency**: `AudioTrack`, `TrackType`, `ProviderCapability`, `TrackRequest`, `TrackResult`, `AudioProvider`, `ProviderRegistry`, `TrackComposer` — names consistent across all tasks. Method signatures match between definition and usage.
- [x] **Import consistency**: Every import references the correct module path as defined in earlier tasks.
- [x] **Test coverage**: Every new module has a dedicated test file. Integration test exercises the full pipeline.
