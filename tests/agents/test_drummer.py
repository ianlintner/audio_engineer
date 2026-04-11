"""Tests for DrummerAgent."""

import pytest
from audio_engineer.core.models import (
    SessionConfig, Genre, Instrument, SectionDef,
)
from audio_engineer.core.constants import GM_DRUMS
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent


@pytest.fixture
def drummer():
    return DrummerAgent()


@pytest.fixture
def basic_context():
    config = SessionConfig(
        genre=Genre.CLASSIC_ROCK,
        tempo=120,
        structure=[
            SectionDef(name="verse", bars=4, intensity=0.6),
            SectionDef(name="chorus", bars=4, intensity=0.9),
        ],
    )
    return SessionContext(config=config)


class TestDrummerAgent:
    def test_generates_track(self, drummer, basic_context):
        track = drummer.generate_part(basic_context)
        assert track.instrument == Instrument.DRUMS
        assert track.channel == 9
        assert len(track.events) > 0

    def test_all_events_on_channel_9(self, drummer, basic_context):
        track = drummer.generate_part(basic_context)
        for event in track.events:
            assert event.channel == 9

    def test_uses_valid_drum_pitches(self, drummer, basic_context):
        track = drummer.generate_part(basic_context)
        valid_pitches = set(GM_DRUMS.values())
        for event in track.events:
            assert event.pitch in valid_pitches, f"Invalid drum pitch: {event.pitch}"

    def test_events_sorted_by_tick(self, drummer, basic_context):
        track = drummer.generate_part(basic_context)
        ticks = [e.start_tick for e in track.events]
        assert ticks == sorted(ticks)

    def test_crash_on_chorus(self, drummer, basic_context):
        """Chorus section should have crash cymbal on first bar."""
        track = drummer.generate_part(basic_context)
        crash_pitch = GM_DRUMS["crash"]
        crash_events = [e for e in track.events if e.pitch == crash_pitch]
        assert len(crash_events) > 0, "Expected crash cymbal in chorus"

    def test_works_without_llm(self, basic_context):
        drummer = DrummerAgent(llm=None)
        track = drummer.generate_part(basic_context)
        assert len(track.events) > 0

    def test_blues_genre(self):
        config = SessionConfig(
            genre=Genre.BLUES,
            structure=[SectionDef(name="verse", bars=4, intensity=0.5)],
        )
        ctx = SessionContext(config=config)
        drummer = DrummerAgent()
        track = drummer.generate_part(ctx)
        assert len(track.events) > 0

    def test_velocity_scales_with_intensity(self, drummer):
        low = SessionContext(config=SessionConfig(
            structure=[SectionDef(name="verse", bars=2, intensity=0.3)]
        ))
        high = SessionContext(config=SessionConfig(
            structure=[SectionDef(name="chorus", bars=2, intensity=1.0)]
        ))
        low_track = drummer.generate_part(low)
        high_track = drummer.generate_part(high)
        avg_low = sum(e.velocity for e in low_track.events) / len(low_track.events)
        avg_high = sum(e.velocity for e in high_track.events) / len(high_track.events)
        assert avg_high > avg_low
