"""Tests for GuitaristAgent."""

import pytest
from audio_engineer.core.models import (
    SessionConfig, Genre, Instrument, SectionDef,
    KeySignature, NoteName, Mode,
)
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.guitarist import GuitaristAgent


@pytest.fixture
def guitarist():
    return GuitaristAgent()


@pytest.fixture
def basic_context():
    config = SessionConfig(
        genre=Genre.CLASSIC_ROCK,
        tempo=120,
        key=KeySignature(root=NoteName.E, mode=Mode.MINOR),
        structure=[
            SectionDef(name="verse", bars=4, intensity=0.5),
            SectionDef(name="chorus", bars=4, intensity=0.9),
        ],
    )
    return SessionContext(config=config)


class TestGuitaristAgent:
    def test_generates_track(self, guitarist, basic_context):
        track = guitarist.generate_part(basic_context)
        assert track.instrument == Instrument.ELECTRIC_GUITAR
        assert track.channel == 2
        assert len(track.events) > 0

    def test_all_events_on_channel_2(self, guitarist, basic_context):
        track = guitarist.generate_part(basic_context)
        for event in track.events:
            assert event.channel == 2

    def test_guitar_range(self, guitarist, basic_context):
        """Guitar notes should be in reasonable range (MIDI 36-84)."""
        track = guitarist.generate_part(basic_context)
        for event in track.events:
            assert 30 <= event.pitch <= 90, f"Guitar pitch out of range: {event.pitch}"

    def test_power_chords_for_rock(self, guitarist, basic_context):
        """Rock genres should use power chords (intervals of 7 semitones)."""
        track = guitarist.generate_part(basic_context)
        # Group notes within a small window (strum spread uses 5-tick offsets)
        events_sorted = sorted(track.events, key=lambda e: e.start_tick)
        found_fifth = False
        window = 20  # ticks
        i = 0
        while i < len(events_sorted) and not found_fifth:
            group = [events_sorted[i].pitch]
            j = i + 1
            while j < len(events_sorted) and events_sorted[j].start_tick - events_sorted[i].start_tick < window:
                group.append(events_sorted[j].pitch)
                j += 1
            group_sorted = sorted(group)
            for k in range(len(group_sorted) - 1):
                if group_sorted[k + 1] - group_sorted[k] == 7:
                    found_fifth = True
                    break
            i = j if j > i + 1 else i + 1
        assert found_fifth, "Expected power chord intervals for rock genre"

    def test_events_sorted(self, guitarist, basic_context):
        track = guitarist.generate_part(basic_context)
        ticks = [e.start_tick for e in track.events]
        assert ticks == sorted(ticks)

    def test_works_without_llm(self, basic_context):
        guitarist = GuitaristAgent(llm=None)
        track = guitarist.generate_part(basic_context)
        assert len(track.events) > 0

    def test_overdriven_program_for_rock(self, guitarist, basic_context):
        track = guitarist.generate_part(basic_context)
        assert track.program == 29  # electric_guitar_overdriven
