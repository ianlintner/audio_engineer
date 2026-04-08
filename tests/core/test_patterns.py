"""Tests for the pattern repository."""

import pytest

from audio_engineer.core.patterns import PatternRepository, DrumPattern, DrumFill
from audio_engineer.core.models import Genre, NoteEvent
from audio_engineer.core.constants import GM_DRUMS, TICKS_PER_BEAT


class TestDrumPattern:
    def test_basic_pattern_to_events(self):
        pattern = DrumPattern(
            name="test",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
        )
        events = pattern.to_events(bar_offset=0)
        assert len(events) == 4
        pitches = {e.pitch for e in events}
        assert GM_DRUMS["kick"] in pitches
        assert GM_DRUMS["snare"] in pitches

    def test_bar_offset(self):
        pattern = DrumPattern(
            name="test",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0],
        )
        events_bar0 = pattern.to_events(bar_offset=0)
        events_bar1 = pattern.to_events(bar_offset=1)
        assert events_bar1[0].start_tick == events_bar0[0].start_tick + TICKS_PER_BEAT * 4

    def test_intensity_affects_velocity(self):
        pattern = DrumPattern(
            name="test",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0],
            velocity_map={"kick": 100},
        )
        events_full = pattern.to_events(bar_offset=0, intensity=1.0)
        events_half = pattern.to_events(bar_offset=0, intensity=0.5)
        assert events_full[0].velocity > events_half[0].velocity

    def test_all_drums_on_channel_9(self):
        pattern = DrumPattern(
            name="test",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0],
            snares=[2.0],
            hihats=[1.0, 2.0, 3.0, 4.0],
        )
        events = pattern.to_events()
        for e in events:
            assert e.channel == 9


class TestDrumFill:
    def test_fill_offset(self):
        fill = DrumFill(
            name="test_fill",
            genre=Genre.CLASSIC_ROCK,
            events=[
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=100, start_tick=0, duration_ticks=120, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=110, start_tick=240, duration_ticks=480, channel=9),
            ],
        )
        events = fill.to_events(bar_offset=3, beat_start=3.0)
        # All events should be offset
        assert all(e.start_tick > 0 for e in events)
        assert len(events) == 2


class TestPatternRepository:
    def test_classic_rock_patterns(self, pattern_repo):
        patterns = pattern_repo.get_drum_patterns(Genre.CLASSIC_ROCK)
        assert len(patterns) >= 4
        names = [p.name for p in patterns]
        assert "rock_straight_8th" in names
        assert "rock_driving" in names

    def test_blues_patterns(self, pattern_repo):
        patterns = pattern_repo.get_drum_patterns(Genre.BLUES)
        assert len(patterns) >= 2
        names = [p.name for p in patterns]
        assert "blues_shuffle" in names

    def test_get_pattern_by_name(self, pattern_repo):
        pattern = pattern_repo.get_pattern_by_name("rock_straight_8th")
        assert pattern is not None
        assert pattern.genre == Genre.CLASSIC_ROCK

    def test_get_nonexistent_pattern(self, pattern_repo):
        assert pattern_repo.get_pattern_by_name("nonexistent") is None

    def test_classic_rock_fills(self, pattern_repo):
        fills = pattern_repo.get_drum_fills(Genre.CLASSIC_ROCK)
        assert len(fills) >= 2
        names = [f.name for f in fills]
        assert "tom_roll_2beat" in names
        assert "snare_build" in names

    def test_unsupported_genre_returns_empty(self, pattern_repo):
        patterns = pattern_repo.get_drum_patterns(Genre.FOLK)
        assert patterns == []

    def test_register_custom_pattern(self, pattern_repo):
        custom = DrumPattern(
            name="custom_pattern",
            genre=Genre.PUNK,
            kicks=[1.0, 2.0, 3.0, 4.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        )
        pattern_repo.register_drum_pattern(custom)
        patterns = pattern_repo.get_drum_patterns(Genre.PUNK)
        assert len(patterns) == 1
        assert patterns[0].name == "custom_pattern"

    def test_pattern_generates_valid_events(self, pattern_repo):
        patterns = pattern_repo.get_drum_patterns(Genre.CLASSIC_ROCK)
        for pattern in patterns:
            events = pattern.to_events(bar_offset=0)
            for e in events:
                assert 0 <= e.pitch <= 127
                assert 0 <= e.velocity <= 127
                assert e.start_tick >= 0
                assert e.duration_ticks > 0
                assert e.channel == 9

    def test_pop_patterns(self, pattern_repo):
        patterns = pattern_repo.get_drum_patterns(Genre.POP)
        assert len(patterns) >= 1
