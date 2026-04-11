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
