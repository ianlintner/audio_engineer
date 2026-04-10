"""Integration tests: ProviderRegistry → MidiProvider → musician agents.

These tests exercise the full generate path without mocking, verifying
that routing contracts and real agent implementations are compatible.
"""
from __future__ import annotations

from audio_engineer.providers.base import ProviderCapability, TrackRequest
from audio_engineer.providers.midi_provider import MidiProvider
from audio_engineer.providers.registry import ProviderRegistry


def _make_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(MidiProvider())
    return registry


def _drums_request(**kwargs) -> TrackRequest:
    return TrackRequest(
        track_name="drums",
        description="4/4 rock drum pattern",
        instrument="drums",
        genre="classic_rock",
        key="C major",
        tempo=120,
        **kwargs,
    )


class TestRegistryToMidiProviderIntegration:
    """ProviderRegistry routes to MidiProvider and gets real MIDI output."""

    def test_generate_returns_success(self):
        registry = _make_registry()
        result = registry.generate(_drums_request())
        assert result.success is True

    def test_generate_uses_midi_engine(self):
        registry = _make_registry()
        result = registry.generate(_drums_request())
        assert result.provider_used == "midi_engine"

    def test_generate_returns_non_none_track(self):
        registry = _make_registry()
        result = registry.generate(_drums_request())
        assert result.track is not None

    def test_generate_track_has_midi_data(self):
        registry = _make_registry()
        result = registry.generate(_drums_request())
        assert result.track is not None
        assert result.track.midi_data is not None

    def test_generate_bass_track(self):
        registry = _make_registry()
        request = TrackRequest(
            track_name="bass",
            description="walking bass line",
            instrument="bass",
            genre="blues",
            key="A minor",
            tempo=100,
        )
        result = registry.generate(request)
        assert result.success is True
        assert result.track is not None
        assert result.track.midi_data is not None

    def test_generate_error_on_unsupported_instrument(self):
        registry = _make_registry()
        request = TrackRequest(
            track_name="vocals",
            description="lead vocals",
            instrument="vocals",
        )
        result = registry.generate(request)
        assert result.success is False
        assert result.error is not None


class TestCapabilityRouting:
    """required_capabilities routes to the correct provider."""

    def test_midi_generation_capability_routes_to_midi_engine(self):
        registry = _make_registry()
        request = _drums_request(
            required_capabilities=[ProviderCapability.MIDI_GENERATION]
        )
        result = registry.generate(request)
        assert result.provider_used == "midi_engine"

    def test_audio_generation_capability_finds_no_provider(self):
        registry = _make_registry()
        request = TrackRequest(
            track_name="stem",
            description="audio stem",
            instrument="drums",
            required_capabilities=[ProviderCapability.AUDIO_GENERATION],
        )
        result = registry.generate(request)
        assert result.success is False
        assert result.provider_used == "none"


class TestPreferredProviderRouting:
    """preferred_provider selects named provider when available."""

    def test_preferred_provider_midi_engine_succeeds(self):
        registry = _make_registry()
        result = registry.generate(_drums_request(preferred_provider="midi_engine"))
        assert result.success is True
        assert result.provider_used == "midi_engine"

    def test_preferred_provider_unknown_falls_back_to_first_available(self):
        registry = _make_registry()
        result = registry.generate(_drums_request(preferred_provider="nonexistent"))
        # Falls back to midi_engine (only registered provider)
        assert result.success is True
        assert result.provider_used == "midi_engine"


class TestEmptyRegistry:
    """Empty registry returns a clear failure."""

    def test_empty_registry_returns_failure(self):
        registry = ProviderRegistry()
        result = registry.generate(_drums_request())
        assert result.success is False

    def test_empty_registry_reports_no_provider(self):
        registry = ProviderRegistry()
        result = registry.generate(_drums_request())
        assert result.provider_used == "none"

    def test_empty_registry_includes_error_message(self):
        registry = ProviderRegistry()
        result = registry.generate(_drums_request())
        assert result.error is not None
        assert len(result.error) > 0
