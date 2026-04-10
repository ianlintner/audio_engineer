"""Tests for the Gemini integration module."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock helpers – the google-genai SDK may not be installed in the test env
# ---------------------------------------------------------------------------


def _make_mock_types():
    """Build a mock ``google.genai.types`` namespace."""
    types = MagicMock()
    types.GenerateContentConfig = MagicMock
    types.SpeechConfig = MagicMock
    types.VoiceConfig = MagicMock
    types.PrebuiltVoiceConfig = MagicMock
    # Part.from_bytes returns a sentinel object
    types.Part.from_bytes.return_value = MagicMock()
    return types


def _make_mock_client(response_text: str = "", audio_data: bytes = b""):
    """Return a mocked ``GeminiClient``."""
    from audio_engineer.gemini.client import GeminiClient

    mock_raw = MagicMock()

    # Build fake response
    response = MagicMock()
    response.text = response_text

    # For audio responses (music gen / TTS)
    part = MagicMock()
    part.inline_data.data = audio_data
    part.inline_data.mime_type = "audio/mp3"
    part.text = None
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [part] if audio_data else []

    # response.parts mirrors candidates[0].content.parts (as the real SDK does)
    response.parts = [part] if audio_data else []

    mock_raw.models.generate_content.return_value = response

    client = GeminiClient.__new__(GeminiClient)
    client._client = mock_raw
    client._api_key = "test-key"

    # Patch the generate_content convenience method to go through our mock
    client.generate_content = MagicMock(return_value=response)

    # Expose types
    client._types = _make_mock_types()
    return client


# =========================================================================
# GeminiClient
# =========================================================================


class TestGeminiClient:
    def test_singleton_returns_same_instance(self):
        """get_gemini_client() returns the same instance across calls."""
        from audio_engineer.gemini.client import get_gemini_client
        import audio_engineer.gemini.client as mod

        c1 = _make_mock_client()
        mod._client_instance = c1

        result = get_gemini_client()
        assert result is c1

        # Cleanup
        mod._client_instance = None

    def test_types_property(self):
        client = _make_mock_client()
        assert client._types is not None


# =========================================================================
# MusicGenerationAgent
# =========================================================================


class TestMusicGenerationAgent:
    def test_generate_clip_returns_result(self):
        from audio_engineer.gemini.music_gen import MusicGenerationAgent, MusicGenResult

        client = _make_mock_client(audio_data=b"\x00\x01\x02\x03")
        agent = MusicGenerationAgent(client=client)

        result = agent.generate_clip("upbeat jazz trio")

        assert isinstance(result, MusicGenResult)
        assert result.audio_data == b"\x00\x01\x02\x03"
        client.generate_content.assert_called_once()

    def test_generate_song_returns_result(self):
        from audio_engineer.gemini.music_gen import MusicGenerationAgent

        client = _make_mock_client(audio_data=b"\xff\xfe")
        agent = MusicGenerationAgent(client=client)

        result = agent.generate_song("soft acoustic ballad")

        assert result.audio_data == b"\xff\xfe"

    def test_generate_from_session_builds_prompt(self):
        from audio_engineer.gemini.music_gen import MusicGenerationAgent

        client = _make_mock_client(audio_data=b"audio")
        agent = MusicGenerationAgent(client=client)

        result = agent.generate_from_session(
            genre="blues",
            key="E minor",
            tempo=120,
            structure=["intro", "verse", "chorus"],
            instruments=["drums", "bass", "guitar"],
        )

        assert result.audio_data == b"audio"

    def test_save_writes_file(self, tmp_path):
        from audio_engineer.gemini.music_gen import MusicGenResult

        result = MusicGenResult(
            audio_data=b"\x00" * 100,
            lyrics=None,
            mime_type="audio/mp3",
        )
        out = result.save(tmp_path / "test.mp3")
        assert out.exists()
        assert out.read_bytes() == b"\x00" * 100


# =========================================================================
# AudioAnalysisAgent
# =========================================================================


class TestAudioAnalysisAgent:
    def test_analyse_file_returns_result(self, tmp_path):
        from audio_engineer.gemini.audio_analysis import AudioAnalysisAgent, AudioAnalysisResult

        # Create a dummy wav
        wav_path = tmp_path / "test.wav"
        wav_path.write_bytes(b"\x00" * 44)  # minimal stub

        resp_json = '{"summary": "A test track", "key_detected": "C major", "tempo_estimate": "120"}'
        client = _make_mock_client(response_text=resp_json)
        agent = AudioAnalysisAgent(client=client)

        result = agent.analyse_file(wav_path)

        assert isinstance(result, AudioAnalysisResult)
        assert result.summary == "A test track"
        assert result.key_detected == "C major"

    def test_analyse_file_not_found(self):
        from audio_engineer.gemini.audio_analysis import AudioAnalysisAgent

        client = _make_mock_client()
        agent = AudioAnalysisAgent(client=client)

        with pytest.raises(FileNotFoundError):
            agent.analyse_file("/nonexistent/audio.wav")

    def test_unsupported_format(self, tmp_path):
        from audio_engineer.gemini.audio_analysis import AudioAnalysisAgent

        bad_file = tmp_path / "test.xyz"
        bad_file.write_bytes(b"data")
        client = _make_mock_client()
        agent = AudioAnalysisAgent(client=client)

        with pytest.raises(ValueError, match="Unsupported audio format"):
            agent.analyse_file(bad_file)

    def test_get_mix_feedback_returns_text(self, tmp_path):
        from audio_engineer.gemini.audio_analysis import AudioAnalysisAgent

        wav_path = tmp_path / "mix.wav"
        wav_path.write_bytes(b"\x00" * 44)

        client = _make_mock_client(response_text="Reduce 2-4kHz by 3dB")
        agent = AudioAnalysisAgent(client=client)

        feedback = agent.get_mix_feedback(wav_path, genre="rock")
        assert "Reduce" in feedback

    def test_describe_audio_returns_text(self, tmp_path):
        from audio_engineer.gemini.audio_analysis import AudioAnalysisAgent

        wav_path = tmp_path / "track.mp3"
        wav_path.write_bytes(b"\x00" * 44)

        client = _make_mock_client(response_text="A mellow jazz piece")
        agent = AudioAnalysisAgent(client=client)

        desc = agent.describe_audio(wav_path)
        assert "jazz" in desc


# =========================================================================
# TTSAgent
# =========================================================================


class TestTTSAgent:
    def test_speak_returns_tts_result(self):
        from audio_engineer.gemini.tts import TTSAgent, TTSResult

        client = _make_mock_client(audio_data=b"\x00\x01" * 100)
        agent = TTSAgent(client=client)

        result = agent.speak("Hello world")

        assert isinstance(result, TTSResult)
        assert len(result.pcm_data) > 0

    def test_wav_bytes_valid_header(self):
        from audio_engineer.gemini.tts import TTSResult

        result = TTSResult(pcm_data=b"\x00\x01" * 100, sample_rate=24000)
        wav = result.wav_bytes

        # RIFF header
        assert wav[:4] == b"RIFF"

    def test_save_wav(self, tmp_path):
        from audio_engineer.gemini.tts import TTSResult

        result = TTSResult(pcm_data=b"\x00\x01" * 100, sample_rate=24000)
        out = result.save(tmp_path / "speech.wav")
        assert out.exists()
        data = out.read_bytes()
        assert data[:4] == b"RIFF"

    def test_save_raw(self, tmp_path):
        from audio_engineer.gemini.tts import TTSResult

        result = TTSResult(pcm_data=b"\xab\xcd" * 50)
        out = result.save(tmp_path / "raw.pcm", fmt="raw")
        assert out.exists()
        assert out.read_bytes() == b"\xab\xcd" * 50

    def test_generate_vocal_track(self):
        from audio_engineer.gemini.tts import TTSAgent

        client = _make_mock_client(audio_data=b"\x01\x02" * 50)
        agent = TTSAgent(client=client)

        result = agent.generate_vocal_track(
            lyrics="Verse one lyrics here",
            style="slow, breathy",
        )
        assert len(result.pcm_data) > 0

    def test_no_audio_raises(self):
        from audio_engineer.gemini.tts import TTSAgent

        client = _make_mock_client(audio_data=b"")  # empty → no parts
        agent = TTSAgent(client=client)

        with pytest.raises(RuntimeError, match="no audio data"):
            agent.speak("Hello world")


# =========================================================================
# Orchestrator Gemini integration
# =========================================================================


class TestOrchestratorGemini:
    def test_gemini_agents_none_when_unavailable(self, tmp_path):
        """Gemini agents are None when google-genai is not installed."""
        with patch(
            "audio_engineer.agents.orchestrator._gemini_available",
            return_value=False,
        ):
            from audio_engineer.agents.orchestrator import SessionOrchestrator

            orch = SessionOrchestrator(output_dir=tmp_path)
            assert orch._gemini_music is None
            assert orch._gemini_analysis is None
            assert orch._gemini_tts is None
