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

    def test_route_default_to_first_available(self, registry: ProviderRegistry):
        req = TrackRequest(track_name="bass", description="bass line")
        provider = registry.route(req)
        assert provider is not None
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
