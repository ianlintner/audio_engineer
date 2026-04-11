"""Tests for the 40 PAS standard drum rudiments."""
import pytest
from audio_engineer.core.patterns import DRUM_RUDIMENTS
from audio_engineer.core.models import NoteEvent


# The 40 official PAS rudiment names (as registered)
_EXPECTED_RUDIMENTS = [
    "single_stroke_roll", "single_stroke_4", "single_stroke_7",
    "multiple_bounce_roll", "triple_stroke_roll", "double_stroke_roll",
    "5_stroke_roll", "6_stroke_roll", "7_stroke_roll",
    "9_stroke_roll", "10_stroke_roll", "11_stroke_roll",
    "13_stroke_roll", "15_stroke_roll", "17_stroke_roll",
    "single_paradiddle", "double_paradiddle", "triple_paradiddle",
    "single_paradiddle_diddle",
    "flam", "flam_accent", "flam_tap", "flamacue",
    "flam_paradiddle", "single_flammed_mill", "flam_paradiddle_diddle",
    "pataflafla", "swiss_army_triplet", "inverted_flam_tap",
    "flam_drag", "single_flam_drag",
    "drag", "single_drag_tap", "double_drag_tap", "lesson_25",
    "single_dragadiddle", "drag_paradiddle_1", "drag_paradiddle_2",
    "single_ratamacue", "double_ratamacue", "triple_ratamacue",
]


class TestDrumRudimentRegistry:
    def test_all_40_rudiments_registered(self):
        for name in _EXPECTED_RUDIMENTS:
            assert name in DRUM_RUDIMENTS, f"Rudiment '{name}' not found"

    def test_rudiment_count_at_least_40(self):
        assert len(DRUM_RUDIMENTS) >= 40


class TestDrumRudimentEvents:
    @pytest.mark.parametrize("name", _EXPECTED_RUDIMENTS)
    def test_rudiment_produces_events(self, name):
        rudiment = DRUM_RUDIMENTS[name]
        assert len(rudiment.events) > 0

    @pytest.mark.parametrize("name", _EXPECTED_RUDIMENTS)
    def test_all_events_valid_midi(self, name):
        rudiment = DRUM_RUDIMENTS[name]
        for ev in rudiment.events:
            assert isinstance(ev, NoteEvent)
            assert 0 <= ev.pitch <= 127, f"{name}: pitch {ev.pitch} out of range"
            assert 1 <= ev.velocity <= 127, f"{name}: velocity {ev.velocity} out of range"
            assert ev.start_tick >= 0, f"{name}: negative start_tick"
            assert ev.duration_ticks > 0, f"{name}: non-positive duration_ticks"
            assert ev.channel == 9, f"{name}: wrong channel {ev.channel}"

    @pytest.mark.parametrize("name", _EXPECTED_RUDIMENTS)
    def test_to_events_bar_offset(self, name):
        rudiment = DRUM_RUDIMENTS[name]
        events_bar0 = rudiment.to_events(bar_offset=0, beat_offset=1.0)
        events_bar1 = rudiment.to_events(bar_offset=1, beat_offset=1.0)
        assert len(events_bar0) == len(events_bar1)
        # bar 1 should be offset by exactly 4 * TICKS_PER_BEAT (4/4)
        from audio_engineer.core.constants import TICKS_PER_BEAT
        expected_offset = TICKS_PER_BEAT * 4
        for e0, e1 in zip(events_bar0, events_bar1):
            assert e1.start_tick == e0.start_tick + expected_offset

    def test_single_paradiddle_pattern(self):
        """RLRR: first note R (snare=38), second L (rim=37), then RR."""
        r = DRUM_RUDIMENTS["single_paradiddle"]
        pitches = [e.pitch for e in r.events]
        assert pitches == [38, 37, 38, 38]  # R L R R

    def test_flam_has_ghost_note(self):
        """Flam should have a low-velocity grace note before the accent."""
        r = DRUM_RUDIMENTS["flam"]
        assert len(r.events) == 2
        grace, accent = r.events[0], r.events[1]
        assert grace.velocity < accent.velocity

    def test_drag_starts_with_two_ghosts(self):
        r = DRUM_RUDIMENTS["drag"]
        assert len(r.events) >= 3
        assert r.events[0].velocity < 80
        assert r.events[1].velocity < 80
