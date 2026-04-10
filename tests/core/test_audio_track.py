"""Tests for AudioTrack unified track model."""
import pytest
from audio_engineer.core.audio_track import AudioTrack, TrackType


class TestAudioTrack:
    def test_create_midi_track(self):
        track = AudioTrack(
            name="drums",
            track_type=TrackType.MIDI,
            provider="midi_engine",
        )
        assert track.track_type == TrackType.MIDI
        assert track.provider == "midi_engine"
        assert track.audio_data is None
        assert track.midi_data is None
        assert track.sample_rate is None

    def test_create_audio_track(self):
        track = AudioTrack(
            name="synth_pad",
            track_type=TrackType.AUDIO,
            provider="gemini_lyria",
            audio_data=b"\x00\x01\x02",
            mime_type="audio/mp3",
            sample_rate=44100,
        )
        assert track.track_type == TrackType.AUDIO
        assert track.audio_data == b"\x00\x01\x02"
        assert track.mime_type == "audio/mp3"
        assert track.sample_rate == 44100

    def test_has_audio_data(self):
        empty = AudioTrack(name="empty", track_type=TrackType.AUDIO, provider="test")
        assert not empty.has_audio

        with_data = AudioTrack(
            name="full",
            track_type=TrackType.AUDIO,
            provider="test",
            audio_data=b"\xff",
        )
        assert with_data.has_audio

    def test_has_midi_data(self):
        from audio_engineer.core.models import MidiTrackData, Instrument

        midi = MidiTrackData(
            name="bass", instrument=Instrument.BASS, channel=1, events=[]
        )
        track = AudioTrack(
            name="bass",
            track_type=TrackType.MIDI,
            provider="midi_engine",
            midi_data=midi,
        )
        assert track.has_midi

    def test_duration_seconds_from_audio_metadata(self):
        track = AudioTrack(
            name="clip",
            track_type=TrackType.AUDIO,
            provider="test",
            duration_seconds=30.0,
        )
        assert track.duration_seconds == 30.0

    def test_tags_for_categorization(self):
        track = AudioTrack(
            name="ambient_pad",
            track_type=TrackType.AUDIO,
            provider="gemini_lyria",
            tags=["ambient", "pad", "atmospheric"],
        )
        assert "ambient" in track.tags

    def test_track_type_enum_values(self):
        assert TrackType.MIDI.value == "midi"
        assert TrackType.AUDIO.value == "audio"

    def test_has_audio_empty_bytes_is_false(self):
        track = AudioTrack(
            name="empty_bytes",
            track_type=TrackType.AUDIO,
            provider="test",
            audio_data=b"",
        )
        assert not track.has_audio

    def test_save_audio_writes_file(self, tmp_path):
        track = AudioTrack(
            name="clip",
            track_type=TrackType.AUDIO,
            provider="test",
            audio_data=b"\x00\x01\x02\x03",
        )
        out = track.save_audio(tmp_path / "subdir" / "clip.wav")
        assert out.exists()
        assert out.read_bytes() == b"\x00\x01\x02\x03"

    def test_save_audio_raises_without_data(self):
        track = AudioTrack(
            name="no_data",
            track_type=TrackType.AUDIO,
            provider="test",
        )
        with pytest.raises(ValueError, match="no audio data"):
            track.save_audio("/tmp/should_not_exist.wav")
