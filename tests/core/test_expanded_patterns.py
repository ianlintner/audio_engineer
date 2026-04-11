"""Tests for expanded drum patterns, new genres, and pattern classes."""
import pytest
from audio_engineer.core.models import Genre, NoteEvent
from audio_engineer.core.patterns import (
    PatternRepository,
    BASS_PATTERNS,
    MELODIC_PATTERNS,
)
from audio_engineer.core.constants import TICKS_PER_BEAT


class TestExpandedDrumPatterns:
    @pytest.fixture
    def repo(self):
        return PatternRepository()

    @pytest.mark.parametrize("genre", [
        Genre.JAZZ, Genre.FUNK, Genre.REGGAE, Genre.SOUL,
        Genre.METAL, Genre.HIP_HOP, Genre.LATIN, Genre.ELECTRONIC,
        Genre.HOUSE, Genre.GOSPEL, Genre.AMBIENT,
    ])
    def test_genre_has_patterns(self, repo, genre):
        patterns = repo.get_drum_patterns(genre)
        assert len(patterns) > 0, f"No drum patterns registered for {genre}"

    @pytest.mark.parametrize("genre", [
        Genre.JAZZ, Genre.FUNK, Genre.METAL, Genre.LATIN,
    ])
    def test_genre_has_fills(self, repo, genre):
        fills = repo.get_drum_fills(genre)
        assert len(fills) > 0, f"No drum fills registered for {genre}"

    def test_jazz_ride_swing_pattern(self, repo):
        patterns = repo.get_drum_patterns(Genre.JAZZ)
        names = [p.name for p in patterns]
        assert "jazz_ride_swing" in names

    def test_metal_blast_beat_pattern(self, repo):
        patterns = repo.get_drum_patterns(Genre.METAL)
        names = [p.name for p in patterns]
        assert "metal_blast_beat" in names

    def test_reggae_one_drop_pattern(self, repo):
        patterns = repo.get_drum_patterns(Genre.REGGAE)
        names = [p.name for p in patterns]
        assert "reggae_one_drop" in names

    def test_pattern_events_in_valid_range(self, repo):
        """All patterns should produce events with valid MIDI pitch + velocity."""
        for genre_patterns in repo._drum_patterns.values():
            for pattern in genre_patterns:
                events = pattern.to_events(bar_offset=0, intensity=0.8)
                for ev in events:
                    assert isinstance(ev, NoteEvent)
                    assert 0 <= ev.pitch <= 127
                    assert 1 <= ev.velocity <= 127
                    assert ev.start_tick >= 0
                    assert ev.duration_ticks > 0

    def test_original_rock_patterns_still_work(self, repo):
        patterns = repo.get_drum_patterns(Genre.CLASSIC_ROCK)
        assert len(patterns) >= 3

    def test_bebop_patterns_exist(self, repo):
        patterns = repo.get_drum_patterns(Genre.BEBOP)
        assert len(patterns) > 0


class TestBassPatterns:
    def test_all_patterns_registered(self):
        expected = [
            "jazz_walking", "funk_slap", "reggae_skank",
            "rnb_two_feel", "pop_root_fifth", "latin_tumbao",
            "motown_bass_line", "country_boom_chick",
        ]
        for name in expected:
            assert name in BASS_PATTERNS, f"BassPattern '{name}' missing"

    def test_jazz_walking_produces_events(self):
        pattern = BASS_PATTERNS["jazz_walking"]
        events = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        assert len(events) == 4  # 4 quarter notes per bar

    def test_funk_slap_velocities_valid(self):
        pattern = BASS_PATTERNS["funk_slap"]
        events = pattern.to_events(root_midi=40, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        for ev in events:
            assert 1 <= ev.velocity <= 127

    def test_intensity_scales_velocity(self):
        pattern = BASS_PATTERNS["pop_root_fifth"]
        low = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=0, intensity=0.3)
        high = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=0, intensity=1.0)
        avg_low = sum(e.velocity for e in low) / len(low)
        avg_high = sum(e.velocity for e in high) / len(high)
        assert avg_low < avg_high

    def test_bar_offset_shifts_ticks(self):
        pattern = BASS_PATTERNS["country_boom_chick"]
        e0 = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        e1 = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=1920)
        assert e1[0].start_tick == e0[0].start_tick + 1920


class TestMelodicPatterns:
    def test_all_patterns_registered(self):
        expected = [
            "jazz_chord_shell", "jazz_chord_full",
            "guitar_arpeggio_up", "guitar_arpeggio_down",
            "guitar_travis_picking", "guitar_bossa_comp",
            "funk_rhythm_guitar_16th",
            "keys_stride_left_hand", "keys_jazz_two_handed",
            "keys_synth_arp",
        ]
        for name in expected:
            assert name in MELODIC_PATTERNS, f"MelodicPattern '{name}' missing"

    def test_jazz_chord_shell_produces_events(self):
        pattern = MELODIC_PATTERNS["jazz_chord_shell"]
        chord_pitches = [48, 52, 55, 58]  # Cmaj7 approximation
        events = pattern.to_events(chord_pitches, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        assert len(events) > 0
        for ev in events:
            assert 0 <= ev.pitch <= 127

    def test_keys_synth_arp_16_steps(self):
        pattern = MELODIC_PATTERNS["keys_synth_arp"]
        chord_pitches = [60, 64, 67]  # C major
        events = pattern.to_events(chord_pitches, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        assert len(events) == 16

    def test_octave_offset_applied(self):
        pattern = MELODIC_PATTERNS["guitar_arpeggio_up"]
        chord_pitches = [60, 64, 67]
        events = pattern.to_events(chord_pitches, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
        pitches = [e.pitch for e in events]
        # Some events should be an octave higher (octave_offset=1 adds 12)
        assert any(p >= 72 for p in pitches)
