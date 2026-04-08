"""Tests for FileExportBackend."""
from pathlib import Path

import pytest

from audio_engineer.daw.export import FileExportBackend
from audio_engineer.daw.base import AudioFormat


@pytest.fixture
def backend():
    return FileExportBackend()


class TestFileExportBackend:
    def test_is_always_available(self, backend: FileExportBackend):
        assert backend.is_available() is True

    def test_get_info(self, backend: FileExportBackend):
        info = backend.get_info()
        assert info.name == "FileExport"
        assert info.tier == 3
        assert info.available is True

    def test_supported_formats_empty(self, backend: FileExportBackend):
        assert backend.supported_formats() == []

    def test_render_audio_raises(self, backend: FileExportBackend, tmp_path: Path):
        with pytest.raises(NotImplementedError, match="FluidSynth"):
            backend.render_audio(tmp_path / "test.mid", tmp_path / "out.wav")

    def test_export_midi(self, backend: FileExportBackend, tmp_path: Path):
        # Create a fake MIDI file
        midi_file = tmp_path / "source" / "song.mid"
        midi_file.parent.mkdir()
        midi_file.write_bytes(b"fake midi data")

        output_dir = tmp_path / "output"
        result = backend.export_midi(midi_file, output_dir)

        assert result.exists()
        assert result.name == "song.mid"
        assert result.read_bytes() == b"fake midi data"

    def test_export_midi_creates_output_dir(
        self, backend: FileExportBackend, tmp_path: Path
    ):
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"data")
        output_dir = tmp_path / "nested" / "output"

        result = backend.export_midi(midi_file, output_dir)
        assert result.parent == output_dir
