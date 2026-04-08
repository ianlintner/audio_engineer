"""Shared pytest fixtures for audio_engineer tests."""

import pytest
from audio_engineer.core.models import (
    SessionConfig,
    KeySignature,
    TimeSignature,
    NoteName,
    Mode,
    Genre,
    NoteEvent,
    MidiTrackData,
    Instrument,
)
from audio_engineer.core.midi_engine import MidiEngine, TickConverter
from audio_engineer.core.patterns import PatternRepository
from audio_engineer.core.music_theory import Scale, Chord


@pytest.fixture
def default_session_config() -> SessionConfig:
    return SessionConfig()


@pytest.fixture
def c_major_key() -> KeySignature:
    return KeySignature(root=NoteName.C, mode=Mode.MAJOR)


@pytest.fixture
def time_sig_4_4() -> TimeSignature:
    return TimeSignature(numerator=4, denominator=4)


@pytest.fixture
def midi_engine() -> MidiEngine:
    return MidiEngine()


@pytest.fixture
def tick_converter() -> TickConverter:
    return TickConverter()


@pytest.fixture
def pattern_repo() -> PatternRepository:
    return PatternRepository()


@pytest.fixture
def sample_note_event() -> NoteEvent:
    return NoteEvent(pitch=60, velocity=100, start_tick=0, duration_ticks=480, channel=0)


@pytest.fixture
def sample_track(sample_note_event: NoteEvent) -> MidiTrackData:
    return MidiTrackData(
        name="Test Track",
        instrument=Instrument.BASS,
        channel=0,
        events=[sample_note_event],
        program=33,
    )


@pytest.fixture
def c_major_scale() -> Scale:
    return Scale("C", "major")


@pytest.fixture
def c_major_chord() -> Chord:
    return Chord("C", "major")
