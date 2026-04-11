"""Tests for provider routing settings in AudioEngineerSettings."""
from audio_engineer.config.settings import AudioEngineerSettings


class TestProviderRoutingSettings:
    """Provider routing settings have correct defaults and types."""

    def setup_method(self):
        self.settings = AudioEngineerSettings()

    def test_default_audio_provider_is_midi_engine(self):
        assert self.settings.default_audio_provider == "midi_engine"

    def test_default_midi_provider_is_midi_engine(self):
        assert self.settings.default_midi_provider == "midi_engine"

    def test_enable_gemini_provider_defaults_true(self):
        assert self.settings.enable_gemini_provider is True

    def test_default_audio_provider_is_string(self):
        assert isinstance(self.settings.default_audio_provider, str)

    def test_default_midi_provider_is_string(self):
        assert isinstance(self.settings.default_midi_provider, str)

    def test_enable_gemini_provider_is_bool(self):
        assert isinstance(self.settings.enable_gemini_provider, bool)

    def test_override_default_audio_provider(self, monkeypatch):
        monkeypatch.setenv("AUDIO_ENGINEER_DEFAULT_AUDIO_PROVIDER", "gemini_lyria")
        settings = AudioEngineerSettings()
        assert settings.default_audio_provider == "gemini_lyria"

    def test_override_enable_gemini_provider_false(self, monkeypatch):
        monkeypatch.setenv("AUDIO_ENGINEER_ENABLE_GEMINI_PROVIDER", "false")
        settings = AudioEngineerSettings()
        assert settings.enable_gemini_provider is False
