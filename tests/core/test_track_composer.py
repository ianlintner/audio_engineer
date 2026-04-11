"""Tests for TrackComposer that layers multiple AudioTracks."""
import pytest
from pathlib import Path
from audio_engineer.core.track_composer import TrackComposer
from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.models import MidiTrackData, Instrument, NoteEvent


@pytest.fixture
def midi_track():
    return AudioTrack(
        name="drums",
        track_type=TrackType.MIDI,
        provider="midi_engine",
        midi_data=MidiTrackData(
            name="drums",
            instrument=Instrument.DRUMS,
            channel=9,
            events=[
                NoteEvent(pitch=36, velocity=100, start_tick=0, duration_ticks=240, channel=9),
            ],
            program=0,
        ),
    )


@pytest.fixture
def audio_track():
    return AudioTrack(
        name="synth_pad",
        track_type=TrackType.AUDIO,
        provider="gemini_lyria",
        audio_data=b"\xff\xfb\x90\x00" * 100,
        mime_type="audio/mp3",
    )


class TestTrackComposer:
    def test_create_composer(self):
        composer = TrackComposer()
        assert composer.tracks == []

    def test_add_track(self, midi_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        assert len(composer.tracks) == 1
        assert composer.tracks[0].name == "drums"

    def test_add_multiple_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        assert len(composer.tracks) == 2

    def test_get_midi_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        midi_tracks = composer.get_midi_tracks()
        assert len(midi_tracks) == 1
        assert midi_tracks[0].name == "drums"

    def test_get_audio_tracks(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        audio_tracks = composer.get_audio_tracks()
        assert len(audio_tracks) == 1
        assert audio_tracks[0].name == "synth_pad"

    def test_export_midi(self, midi_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(midi_track)
        out = composer.export_midi(tmp_path / "out.mid", tempo=120)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_audio_stems(self, audio_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(audio_track)
        stems = composer.export_audio_stems(tmp_path)
        assert len(stems) == 1
        assert stems[0].exists()

    def test_export_all(self, midi_track: AudioTrack, audio_track: AudioTrack, tmp_path: Path):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        files = composer.export_all(tmp_path, tempo=120)
        # Should produce at least: MIDI file + 1 audio stem
        assert len(files) >= 2

    def test_manifest(self, midi_track: AudioTrack, audio_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.add_track(audio_track)
        manifest = composer.manifest()
        assert len(manifest) == 2
        assert manifest[0]["name"] == "drums"
        assert manifest[0]["type"] == "midi"
        assert manifest[1]["name"] == "synth_pad"
        assert manifest[1]["type"] == "audio"

    def test_clear(self, midi_track: AudioTrack):
        composer = TrackComposer()
        composer.add_track(midi_track)
        composer.clear()
        assert composer.tracks == []
