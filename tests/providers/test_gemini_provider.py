"""Tests for Gemini Lyria provider (mocked API)."""
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
            audio_data=b"\xff\xfb\x90\x00",
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
