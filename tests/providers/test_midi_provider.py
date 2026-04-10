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
        provider.generate_track(drum_req)

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
