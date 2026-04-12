"""Tests for music theory utilities."""

import pytest

from audio_engineer.core.music_theory import (
    note_name_to_midi,
    midi_to_note_name,
    Scale,
    Chord,
    ChordProgression,
    ProgressionFactory,
)


class TestNoteConversion:
    def test_middle_c(self):
        assert note_name_to_midi("C", 4) == 60

    def test_a440(self):
        assert note_name_to_midi("A", 4) == 69

    def test_lowest_c(self):
        assert note_name_to_midi("C", -1) == 0

    def test_round_trip(self):
        for midi_note in [0, 36, 48, 60, 69, 72, 84, 127]:
            name, octave = midi_to_note_name(midi_note)
            assert note_name_to_midi(name, octave) == midi_note

    def test_sharps(self):
        assert note_name_to_midi("C#", 4) == 61
        assert note_name_to_midi("F#", 3) == 54

    def test_midi_to_name(self):
        name, octave = midi_to_note_name(60)
        assert name == "C"
        assert octave == 4

    def test_invalid_note_name(self):
        with pytest.raises(ValueError):
            note_name_to_midi("X", 4)

    def test_invalid_midi_note(self):
        with pytest.raises(ValueError):
            midi_to_note_name(128)


class TestScale:
    def test_c_major_degrees(self, c_major_scale):
        assert c_major_scale.degrees() == [0, 2, 4, 5, 7, 9, 11]

    def test_c_major_notes_octave_4(self, c_major_scale):
        notes = c_major_scale.notes_in_octave(4)
        assert notes == [60, 62, 64, 65, 67, 69, 71]

    def test_a_minor_degrees(self):
        scale = Scale("A", "minor")
        assert scale.degrees() == [0, 2, 3, 5, 7, 8, 10]

    def test_note_at_degree(self, c_major_scale):
        # C major: C=1, D=2, E=3, F=4, G=5, A=6, B=7
        assert c_major_scale.note_at_degree(1, 4) == 60  # C4
        assert c_major_scale.note_at_degree(3, 4) == 64  # E4
        assert c_major_scale.note_at_degree(5, 4) == 67  # G4

    def test_note_at_degree_wraps_octave(self, c_major_scale):
        # Degree 8 should be C5
        assert c_major_scale.note_at_degree(8, 4) == 72

    def test_contains(self, c_major_scale):
        assert c_major_scale.contains(60)  # C
        assert c_major_scale.contains(62)  # D
        assert c_major_scale.contains(64)  # E
        assert not c_major_scale.contains(61)  # C#
        assert not c_major_scale.contains(63)  # D#

    def test_pentatonic_minor(self):
        scale = Scale("A", "pentatonic_minor")
        assert len(scale.degrees()) == 5
        notes = scale.notes_in_octave(4)
        assert len(notes) == 5

    def test_blues_scale(self):
        scale = Scale("E", "blues")
        assert len(scale.degrees()) == 6

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            Scale("C", "not_a_real_mode")

    def test_invalid_root(self):
        with pytest.raises(ValueError):
            Scale("X", "major")


class TestChord:
    def test_c_major_notes(self, c_major_chord):
        notes = c_major_chord.midi_notes(4)
        assert notes == [60, 64, 67]  # C, E, G

    def test_a_minor_notes(self):
        chord = Chord("A", "minor")
        notes = chord.midi_notes(3)
        assert notes == [57, 60, 64]  # A, C, E

    def test_dom7(self):
        chord = Chord("G", "dom7")
        notes = chord.midi_notes(3)
        # G=55, B=59, D=62, F=65
        assert notes == [55, 59, 62, 65]

    def test_power_chord(self):
        chord = Chord("E", "power")
        notes = chord.midi_notes(2)
        assert len(notes) == 2  # root + fifth

    def test_transpose(self):
        chord = Chord("C", "major")
        transposed = chord.transpose(2)
        assert transposed.root == "D"
        assert transposed.quality == "major"

    def test_transpose_wraps(self):
        chord = Chord("B", "major")
        transposed = chord.transpose(1)
        assert transposed.root == "C"

    def test_invalid_quality(self):
        with pytest.raises(ValueError):
            Chord("C", "nonexistent")

    def test_from_roman_I(self):
        chord = Chord.from_roman("I", "C", "major")
        assert chord.root == "C"
        assert chord.quality == "major"

    def test_from_roman_IV(self):
        chord = Chord.from_roman("IV", "C", "major")
        assert chord.root == "F"
        assert chord.quality == "major"

    def test_from_roman_V(self):
        chord = Chord.from_roman("V", "C", "major")
        assert chord.root == "G"
        assert chord.quality == "major"

    def test_from_roman_vi(self):
        chord = Chord.from_roman("vi", "C", "major")
        assert chord.root == "A"
        assert chord.quality == "minor"

    def test_from_roman_V7(self):
        chord = Chord.from_roman("V7", "C", "major")
        assert chord.root == "G"
        assert chord.quality == "dom7"

    def test_from_roman_ii(self):
        chord = Chord.from_roman("ii", "C", "major")
        assert chord.root == "D"
        assert chord.quality == "minor"


class TestChordProgression:
    def test_from_string(self):
        prog = ChordProgression.from_string("I - IV - V - I", "C", "major")
        assert len(prog) == 4

    def test_resolve(self):
        prog = ChordProgression.from_string("I - V", "C", "major")
        resolved = prog.resolve(octave=3)
        assert len(resolved) == 2
        notes_1, dur_1 = resolved[0]
        assert 48 in notes_1  # C3
        assert dur_1 == 4.0

    def test_transpose(self):
        prog = ChordProgression.from_string("I - IV - V", "C", "major")
        transposed = prog.transpose(2)  # Up a whole step -> D major
        resolved = transposed.resolve(octave=3)
        # First chord root should be D
        first_notes = resolved[0][0]
        assert 50 in first_notes  # D3

    def test_pipe_separator(self):
        prog = ChordProgression.from_string("I | IV | V | I", "G", "major")
        assert len(prog) == 4


class TestProgressionFactory:
    def test_classic_rock(self):
        prog = ProgressionFactory.classic_rock_I_IV_V("C", "major")
        assert len(prog) == 4
        resolved = prog.resolve(3)
        roots = [r[0][0] for r in resolved]
        assert roots[0] == note_name_to_midi("C", 3)  # I
        assert roots[1] == note_name_to_midi("F", 3)  # IV
        assert roots[2] == note_name_to_midi("G", 3)  # V
        assert roots[3] == note_name_to_midi("C", 3)  # I

    def test_twelve_bar_blues(self):
        prog = ProgressionFactory.twelve_bar_blues("A")
        assert len(prog) == 12
        # All chords should be dom7
        for chord, _ in prog.chords:
            assert chord.quality == "dom7"

    def test_pop_progression(self):
        prog = ProgressionFactory.pop_I_V_vi_IV("C")
        assert len(prog) == 4

    def test_rock_ballad(self):
        prog = ProgressionFactory.rock_ballad("G")
        assert len(prog) == 4

    def test_different_keys(self):
        for key in ["C", "D", "E", "F", "G", "A", "B"]:
            prog = ProgressionFactory.classic_rock_I_IV_V(key, "major")
            resolved = prog.resolve(3)
            assert len(resolved) == 4
            # First chord root should match key
            root_midi = note_name_to_midi(key, 3)
            assert resolved[0][0][0] == root_midi
