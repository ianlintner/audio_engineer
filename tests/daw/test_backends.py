"""Tests for DAW backend factory and availability."""
import pytest

from audio_engineer.daw import get_backend, DAWBackend
from audio_engineer.daw.export import FileExportBackend
from audio_engineer.daw.fluidsynth import FluidSynthBackend
from audio_engineer.daw.timidity import TiMidityBackend


class TestGetBackend:
    def test_get_export_backend(self):
        b = get_backend("export")
        assert isinstance(b, FileExportBackend)

    def test_get_fluidsynth_backend(self):
        b = get_backend("fluidsynth")
        assert isinstance(b, FluidSynthBackend)

    def test_get_timidity_backend(self):
        b = get_backend("timidity")
        assert isinstance(b, TiMidityBackend)

    def test_case_insensitive(self):
        b = get_backend("Export")
        assert isinstance(b, FileExportBackend)

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("nonexistent")


class TestFluidSynthAvailability:
    def test_is_available_returns_bool(self):
        b = FluidSynthBackend()
        assert isinstance(b.is_available(), bool)

    def test_info_reflects_availability(self):
        b = FluidSynthBackend()
        info = b.get_info()
        assert info.name == "FluidSynth"
        assert info.tier == 1
        assert info.available == b.is_available()
