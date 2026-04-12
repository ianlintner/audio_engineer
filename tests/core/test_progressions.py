"""Tests for all new ProgressionFactory methods."""
import pytest
from audio_engineer.core.music_theory import ProgressionFactory, ChordProgression


class TestJazzProgressions:
    def test_jazz_ii_V_I_returns_three_chords(self):
        prog = ProgressionFactory.jazz_ii_V_I("C")
        assert len(prog.chords) == 3

    def test_jazz_ii_V_I_chord_qualities(self):
        prog = ProgressionFactory.jazz_ii_V_I("C")
        qualities = [c.quality for c, _ in prog.chords]
        assert qualities == ["min7", "dom7", "maj7"]

    def test_jazz_ii_V_I_in_C(self):
        prog = ProgressionFactory.jazz_ii_V_I("C")
        roots = [c.root for c, _ in prog.chords]
        assert roots == ["D", "G", "C"]

    def test_jazz_turnaround_has_4_chords(self):
        prog = ProgressionFactory.jazz_turnaround("C")
        assert len(prog.chords) == 4

    def test_jazz_turnaround_ends_on_V7(self):
        prog = ProgressionFactory.jazz_turnaround("C")
        last_chord, _ = prog.chords[-1]
        assert last_chord.quality == "dom7"
        assert last_chord.root == "G"  # V of C

    def test_jazz_rhythm_changes_has_8_chords(self):
        prog = ProgressionFactory.jazz_rhythm_changes("C")
        assert len(prog.chords) == 8

    def test_blues_jazz_has_13_chords(self):
        prog = ProgressionFactory.blues_jazz("C")
        assert len(prog.chords) == 13

    def test_blues_jazz_all_dom7(self):
        prog = ProgressionFactory.blues_jazz("C")
        # First chord should be dom7
        first_chord, _ = prog.chords[0]
        assert first_chord.quality == "dom7"


class TestModalProgressions:
    def test_modal_dorian_has_2_chords(self):
        prog = ProgressionFactory.modal_dorian("D")
        assert len(prog.chords) == 2

    def test_modal_dorian_starts_with_min7(self):
        prog = ProgressionFactory.modal_dorian("D")
        first_chord, _ = prog.chords[0]
        assert first_chord.quality == "min7"
        assert first_chord.root == "D"

    def test_bossa_nova_has_5_chords(self):
        prog = ProgressionFactory.bossa_nova("C")
        assert len(prog.chords) == 5


class TestFunkMetalProgressions:
    def test_funk_I7_IV7_has_2_chords(self):
        prog = ProgressionFactory.funk_I7_IV7("C")
        assert len(prog.chords) == 2

    def test_funk_I7_IV7_both_dom7(self):
        prog = ProgressionFactory.funk_I7_IV7("C")
        for chord, _ in prog.chords:
            assert chord.quality == "dom7"

    def test_metal_power_I_VII_VI_has_4_chords(self):
        prog = ProgressionFactory.metal_power_I_VII_VI("E")
        assert len(prog.chords) == 4

    def test_metal_power_all_power_chords(self):
        prog = ProgressionFactory.metal_power_I_VII_VI("E")
        for chord, _ in prog.chords:
            assert chord.quality == "power"


class TestMinorGospelProgressions:
    def test_minor_vamp_has_4_chords(self):
        prog = ProgressionFactory.minor_i_VII_VI_VII("A")
        assert len(prog.chords) == 4

    def test_gospel_I_IV_I_V_has_4_chords(self):
        prog = ProgressionFactory.gospel_I_IV_I_V("G")
        assert len(prog.chords) == 4

    def test_gospel_starts_on_root(self):
        prog = ProgressionFactory.gospel_I_IV_I_V("G")
        first_chord, _ = prog.chords[0]
        assert first_chord.root == "G"
        assert first_chord.quality == "major"


class TestProgressionTransposability:
    @pytest.mark.parametrize("key", ["C", "D", "F", "G", "A"])
    def test_jazz_ii_V_I_all_keys(self, key):
        prog = ProgressionFactory.jazz_ii_V_I(key)
        assert len(prog.chords) == 3

    @pytest.mark.parametrize("key", ["C", "E", "A"])
    def test_metal_power_all_keys(self, key):
        prog = ProgressionFactory.metal_power_I_VII_VI(key)
        assert len(prog.chords) == 4


class TestProgressionReturnType:
    @pytest.mark.parametrize("factory_method,args", [
        (ProgressionFactory.jazz_ii_V_I, ("C",)),
        (ProgressionFactory.jazz_turnaround, ("C",)),
        (ProgressionFactory.jazz_rhythm_changes, ("C",)),
        (ProgressionFactory.blues_jazz, ("C",)),
        (ProgressionFactory.modal_dorian, ("C",)),
        (ProgressionFactory.bossa_nova, ("C",)),
        (ProgressionFactory.minor_i_VII_VI_VII, ("A",)),
        (ProgressionFactory.gospel_I_IV_I_V, ("G",)),
        (ProgressionFactory.metal_power_I_VII_VI, ("E",)),
        (ProgressionFactory.funk_I7_IV7, ("C",)),
    ])
    def test_returns_chord_progression(self, factory_method, args):
        result = factory_method(*args)
        assert isinstance(result, ChordProgression)

    @pytest.mark.parametrize("factory_method,args", [
        (ProgressionFactory.jazz_ii_V_I, ("C",)),
        (ProgressionFactory.metal_power_I_VII_VI, ("E",)),
        (ProgressionFactory.funk_I7_IV7, ("G",)),
    ])
    def test_all_events_have_positive_duration(self, factory_method, args):
        prog = factory_method(*args)
        for _chord, dur in prog.chords:
            assert dur > 0
