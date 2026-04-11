"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from audio_engineer.core.models import (
    Genre,
    Instrument,
    NoteName,
    Mode,
    SessionConfig,
    SessionStatus,
    KeySignature,
    TimeSignature,
    SectionDef,
    NoteEvent,
    MidiTrackData,
    BandConfig,
    Session,
    MixConfig,
    EQBand,
    MixTrackConfig,
)


class TestNoteEvent:
    def test_valid_note(self):
        note = NoteEvent(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
        assert note.pitch == 60
        assert note.velocity == 100
        assert note.channel == 0

    def test_pitch_too_high(self):
        with pytest.raises(ValidationError):
            NoteEvent(pitch=128, velocity=100, start_tick=0, duration_ticks=480)

    def test_pitch_too_low(self):
        with pytest.raises(ValidationError):
            NoteEvent(pitch=-1, velocity=100, start_tick=0, duration_ticks=480)

    def test_velocity_bounds(self):
        with pytest.raises(ValidationError):
            NoteEvent(pitch=60, velocity=128, start_tick=0, duration_ticks=480)

    def test_zero_duration_invalid(self):
        with pytest.raises(ValidationError):
            NoteEvent(pitch=60, velocity=100, start_tick=0, duration_ticks=0)

    def test_negative_start_tick_invalid(self):
        with pytest.raises(ValidationError):
            NoteEvent(pitch=60, velocity=100, start_tick=-1, duration_ticks=480)

    def test_channel_bounds(self):
        NoteEvent(pitch=60, velocity=100, start_tick=0, duration_ticks=480, channel=15)
        with pytest.raises(ValidationError):
            NoteEvent(pitch=60, velocity=100, start_tick=0, duration_ticks=480, channel=16)


class TestSessionConfig:
    def test_defaults(self, default_session_config):
        cfg = default_session_config
        assert cfg.genre == Genre.CLASSIC_ROCK
        assert cfg.tempo == 120
        assert cfg.key.root == NoteName.C
        assert cfg.key.mode == Mode.MAJOR
        assert cfg.time_signature.numerator == 4
        assert cfg.time_signature.denominator == 4
        assert len(cfg.structure) == 6
        assert len(cfg.band.members) == 3

    def test_tempo_too_low(self):
        with pytest.raises(ValidationError):
            SessionConfig(tempo=30)

    def test_tempo_too_high(self):
        with pytest.raises(ValidationError):
            SessionConfig(tempo=301)

    def test_custom_genre(self):
        cfg = SessionConfig(genre=Genre.BLUES)
        assert cfg.genre == Genre.BLUES

    def test_custom_key(self):
        cfg = SessionConfig(key=KeySignature(root=NoteName.A, mode=Mode.MINOR))
        assert cfg.key.root == NoteName.A
        assert cfg.key.mode == Mode.MINOR

    def test_serialization_round_trip(self):
        cfg = SessionConfig(
            genre=Genre.BLUES,
            tempo=90,
            key=KeySignature(root=NoteName.E, mode=Mode.MINOR),
        )
        json_str = cfg.model_dump_json()
        restored = SessionConfig.model_validate_json(json_str)
        assert restored.genre == Genre.BLUES
        assert restored.tempo == 90
        assert restored.key.root == NoteName.E


class TestTimeSignature:
    def test_defaults(self):
        ts = TimeSignature()
        assert ts.numerator == 4
        assert ts.denominator == 4

    def test_waltz(self):
        ts = TimeSignature(numerator=3, denominator=4)
        assert ts.numerator == 3

    def test_invalid_numerator(self):
        with pytest.raises(ValidationError):
            TimeSignature(numerator=0, denominator=4)


class TestSectionDef:
    def test_valid_section(self):
        s = SectionDef(name="verse", bars=8)
        assert s.name == "verse"
        assert s.bars == 8
        assert s.repeats == 1
        assert s.intensity == 0.7

    def test_intensity_clamped(self):
        with pytest.raises(ValidationError):
            SectionDef(name="chorus", bars=8, intensity=1.5)


class TestMidiTrackData:
    def test_create_track(self):
        track = MidiTrackData(
            name="Bass",
            instrument=Instrument.BASS,
            channel=1,
            program=33,
        )
        assert track.name == "Bass"
        assert track.instrument == Instrument.BASS
        assert len(track.events) == 0


class TestSession:
    def test_create_session(self):
        session = Session(id="test-123")
        assert session.id == "test-123"
        assert session.status == SessionStatus.CREATED
        assert len(session.tracks) == 0
        assert len(session.output_files) == 0

    def test_session_serialization(self):
        session = Session(id="test-456", status=SessionStatus.GENERATING)
        data = session.model_dump()
        restored = Session.model_validate(data)
        assert restored.id == "test-456"
        assert restored.status == SessionStatus.GENERATING


class TestBandConfig:
    def test_default_band(self):
        band = BandConfig()
        assert len(band.members) == 3
        instruments = [m.instrument for m in band.members]
        assert Instrument.DRUMS in instruments
        assert Instrument.BASS in instruments
        assert Instrument.ELECTRIC_GUITAR in instruments


class TestMixConfig:
    def test_default_mix(self):
        mix = MixConfig()
        assert mix.master_volume == 0.9
        assert len(mix.tracks) == 0

    def test_eq_band(self):
        eq = EQBand(frequency=1000, gain_db=3.0, q=1.4)
        assert eq.frequency == 1000
        assert eq.gain_db == 3.0

    def test_mix_track_pan(self):
        track = MixTrackConfig(instrument=Instrument.ELECTRIC_GUITAR, pan=-0.5)
        assert track.pan == -0.5
