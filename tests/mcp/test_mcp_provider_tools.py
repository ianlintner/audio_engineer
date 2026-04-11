"""Tests for list_providers and generate_audio_track MCP tools."""
from unittest.mock import patch


from audio_engineer.providers.base import TrackResult
from audio_engineer.core.audio_track import AudioTrack, TrackType


class TestListProviders:
    """list_providers returns structured provider information."""

    def test_returns_dict_with_midi_engine(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        assert isinstance(result, dict)
        assert "midi_engine" in result

    def test_entries_have_capabilities_key(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        for name, info in result.items():
            assert "capabilities" in info, f"Provider '{name}' missing 'capabilities'"

    def test_entries_have_available_key(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        for name, info in result.items():
            assert "available" in info, f"Provider '{name}' missing 'available'"

    def test_midi_engine_is_available(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        assert result["midi_engine"]["available"] is True

    def test_capabilities_are_strings(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        for name, info in result.items():
            assert isinstance(info["capabilities"], list)
            for cap in info["capabilities"]:
                assert isinstance(cap, str), f"Capability '{cap}' in '{name}' is not a string"

    def test_midi_engine_has_midi_generation_capability(self):
        from audio_engineer.mcp_server import list_providers

        result = list_providers()

        assert "midi_generation" in result["midi_engine"]["capabilities"]


class TestGenerateAudioTrack:
    """generate_audio_track routes requests through the provider registry."""

    def _make_midi_result(self, track_name: str = "drums") -> TrackResult:
        track = AudioTrack(
            name=track_name,
            track_type=TrackType.MIDI,
            provider="midi_engine",
        )
        return TrackResult(track=track, success=True, provider_used="midi_engine")

    def test_returns_dict_with_success_key(self, tmp_path):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = self._make_midi_result("test_track")

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.return_value = mock_result
            mock_orch.provider_registry.list_providers.return_value = ["midi_engine"]

            result = generate_audio_track(
                track_name="test_track",
                description="simple drum beat",
            )

        assert isinstance(result, dict)
        assert "success" in result

    def test_successful_generation_returns_success_true(self, tmp_path):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = self._make_midi_result("drums")

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.return_value = mock_result

            result = generate_audio_track(
                track_name="drums",
                description="4/4 rock drum pattern",
            )

        assert result["success"] is True

    def test_explicit_provider_sets_preferred(self, tmp_path):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = self._make_midi_result("bass")
        captured_request = {}

        def capture_generate(req):
            captured_request["preferred_provider"] = req.preferred_provider
            return mock_result

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.side_effect = capture_generate

            generate_audio_track(
                track_name="bass",
                description="walking bass line",
                provider="midi_engine",
            )

        assert captured_request["preferred_provider"] == "midi_engine"

    def test_result_includes_provider_used(self, tmp_path):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = self._make_midi_result("guitar")

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.return_value = mock_result

            result = generate_audio_track(
                track_name="guitar",
                description="rock guitar riff",
                provider="midi_engine",
            )

        assert "provider_used" in result
        assert result["provider_used"] == "midi_engine"

    def test_failed_generation_returns_success_false(self):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = TrackResult(
            track=None,
            success=False,
            provider_used="none",
            error="No provider available",
        )

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.return_value = mock_result

            result = generate_audio_track(
                track_name="unknown",
                description="something impossible",
            )

        assert result["success"] is False

    def test_failed_generation_includes_error(self):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = TrackResult(
            track=None,
            success=False,
            provider_used="none",
            error="No provider available",
        )

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.return_value = mock_result

            result = generate_audio_track(
                track_name="unknown",
                description="something impossible",
            )

        assert "error" in result
        assert "No provider available" in result["error"]

    def test_genre_and_key_forwarded_to_request(self):
        from audio_engineer.mcp_server import generate_audio_track

        mock_result = self._make_midi_result("piano")
        captured = {}

        def capture(req):
            captured["genre"] = req.genre
            captured["key"] = req.key
            captured["tempo"] = req.tempo
            return mock_result

        with patch("audio_engineer.mcp_server._orchestrator") as mock_orch:
            mock_orch.provider_registry.generate.side_effect = capture

            generate_audio_track(
                track_name="piano",
                description="jazz piano comping",
                genre="jazz",
                key="Bb major",
                tempo=90,
            )

        assert captured["genre"] == "jazz"
        assert captured["key"] == "Bb major"
        assert captured["tempo"] == 90
