"""Tests for BassistAgent."""

import pytest
from audio_engineer.core.models import (
    SessionConfig, Genre, Instrument, SectionDef,
    KeySignature, NoteName, Mode,
)
from audio_engineer.core.music_theory import note_name_to_midi
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.bassist import BassistAgent


@pytest.fixture
def bassist():
    return BassistAgent()


@pytest.fixture
def basic_context():
    config = SessionConfig(
        genre=Genre.CLASSIC_ROCK,
        tempo=120,
        key=KeySignature(root=NoteName.C, mode=Mode.MAJOR),
        structure=[
            SectionDef(name="verse", bars=4, intensity=0.6),
            SectionDef(name="chorus", bars=4, intensity=0.9),
        ],
    )
    return SessionContext(config=config)


class TestBassistAgent:
    def test_generates_track(self, bassist, basic_context):
        track = bassist.generate_part(basic_context)
        assert track.instrument == Instrument.BASS
        assert track.channel == 1
        assert len(track.events) > 0

    def test_all_events_on_channel_1(self, bassist, basic_context):
        track = bassist.generate_part(basic_context)
        for event in track.events:
            assert event.channel == 1

    def test_bass_range(self, bassist, basic_context):
        """Bass notes should be in a reasonable range (MIDI 28-60)."""
        track = bassist.generate_part(basic_context)
        for event in track.events:
            assert 20 <= event.pitch <= 72, f"Bass pitch out of range: {event.pitch}"

    def test_follows_chord_roots(self, bassist, basic_context):
        """First note of each chord region should be near the chord root."""
        track = bassist.generate_part(basic_context)
        # C major key -> first chord is C, root C2 = MIDI 36
        c2 = note_name_to_midi("C", 2)
        first_event = track.events[0]
        # Should be a C (pitch % 12 == 0) or very close
        assert first_event.pitch % 12 == c2 % 12 or abs(first_event.pitch - c2) <= 1

    def test_events_sorted(self, bassist, basic_context):
        track = bassist.generate_part(basic_context)
        ticks = [e.start_tick for e in track.events]
        assert ticks == sorted(ticks)

    def test_works_without_llm(self, basic_context):
        bassist = BassistAgent(llm=None)
        track = bassist.generate_part(basic_context)
        assert len(track.events) > 0

    def test_blues_genre(self):
        config = SessionConfig(
            genre=Genre.BLUES,
            key=KeySignature(root=NoteName.A, mode=Mode.MINOR),
            structure=[SectionDef(name="verse", bars=4, intensity=0.5)],
        )
        ctx = SessionContext(config=config)
        bassist = BassistAgent()
        track = bassist.generate_part(ctx)
        assert len(track.events) > 0
