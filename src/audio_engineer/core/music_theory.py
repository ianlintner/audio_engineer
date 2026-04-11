"""Music theory utilities: scales, chords, progressions."""

from __future__ import annotations

from .constants import NOTE_NAMES, SCALE_FORMULAS, CHORD_FORMULAS


def note_name_to_midi(name: str, octave: int) -> int:
    """Convert a note name and octave to a MIDI note number.

    >>> note_name_to_midi("C", 4)
    60
    >>> note_name_to_midi("A", 4)
    69
    """
    name_upper = name.strip().upper()
    # Handle flats by converting to sharps
    flat_map = {"DB": "C#", "EB": "D#", "FB": "E", "GB": "F#", "AB": "G#", "BB": "A#", "CB": "B"}
    if name_upper in flat_map:
        name_upper = flat_map[name_upper]
    if name_upper not in NOTE_NAMES:
        raise ValueError(f"Unknown note name: {name}")
    return NOTE_NAMES.index(name_upper) + (octave + 1) * 12


def midi_to_note_name(midi_note: int) -> tuple[str, int]:
    """Convert a MIDI note number to (note_name, octave).

    >>> midi_to_note_name(60)
    ('C', 4)
    """
    if not 0 <= midi_note <= 127:
        raise ValueError(f"MIDI note must be 0-127, got {midi_note}")
    octave = (midi_note // 12) - 1
    note_idx = midi_note % 12
    return NOTE_NAMES[note_idx], octave


class Scale:
    """A musical scale rooted on a given note."""

    def __init__(self, root: str, mode: str = "major"):
        root_upper = root.strip().upper()
        flat_map = {"DB": "C#", "EB": "D#", "FB": "E", "GB": "F#", "AB": "G#", "BB": "A#", "CB": "B"}
        if root_upper in flat_map:
            root_upper = flat_map[root_upper]
        if root_upper not in NOTE_NAMES:
            raise ValueError(f"Unknown root note: {root}")
        if mode not in SCALE_FORMULAS:
            raise ValueError(f"Unknown mode: {mode}. Available: {list(SCALE_FORMULAS.keys())}")
        self.root = root_upper
        self.mode = mode
        self._root_idx = NOTE_NAMES.index(self.root)
        self._intervals = SCALE_FORMULAS[mode]

    def degrees(self) -> list[int]:
        """Return the semitone intervals that define this scale."""
        return list(self._intervals)

    def notes_in_octave(self, octave: int) -> list[int]:
        """Return MIDI note numbers for this scale in the given octave."""
        base = note_name_to_midi(self.root, octave)
        return [base + interval for interval in self._intervals]

    def note_at_degree(self, degree: int, octave: int) -> int:
        """Return the MIDI note at the given scale degree (1-indexed).

        Degrees beyond the scale length wrap into higher octaves.
        """
        if degree < 1:
            raise ValueError("Degree must be >= 1")
        num_notes = len(self._intervals)
        idx = (degree - 1) % num_notes
        extra_octaves = (degree - 1) // num_notes
        base = note_name_to_midi(self.root, octave + extra_octaves)
        return base + self._intervals[idx]

    def contains(self, midi_note: int) -> bool:
        """Check if a MIDI note belongs to this scale (any octave)."""
        # Check if (midi_note's pitch class - root) mod 12 is in intervals
        pc = (midi_note % 12 - self._root_idx) % 12
        return pc in self._intervals

    def __repr__(self) -> str:
        return f"Scale({self.root}, {self.mode})"


class Chord:
    """A chord defined by root and quality."""

    def __init__(self, root: str, quality: str = "major"):
        root_upper = root.strip().upper()
        flat_map = {"DB": "C#", "EB": "D#", "FB": "E", "GB": "F#", "AB": "G#", "BB": "A#", "CB": "B"}
        if root_upper in flat_map:
            root_upper = flat_map[root_upper]
        if root_upper not in NOTE_NAMES:
            raise ValueError(f"Unknown root note: {root}")
        if quality not in CHORD_FORMULAS:
            raise ValueError(f"Unknown chord quality: {quality}. Available: {list(CHORD_FORMULAS.keys())}")
        self.root = root_upper
        self.quality = quality
        self._intervals = CHORD_FORMULAS[quality]

    def midi_notes(self, octave: int = 3) -> list[int]:
        """Return MIDI note numbers for this chord in the given octave."""
        base = note_name_to_midi(self.root, octave)
        return [base + i for i in self._intervals]

    @classmethod
    def from_roman(cls, numeral: str, key_root: str, key_mode: str = "major") -> Chord:
        """Build a Chord from a Roman numeral in a given key.

        Uppercase = major, lowercase = minor. Suffix '7' = dom7/min7.
        Examples: I, ii, IV, V7, vi, viio (diminished via 'o' not yet supported, use dim).
        """
        numeral = numeral.strip()

        # Parse quality suffix
        has_7 = numeral.endswith("7")
        clean = numeral.rstrip("7")

        # Determine if major or minor from case
        roman_map_upper = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}

        is_minor = clean == clean.lower() and clean.upper() in roman_map_upper
        degree_str = clean.upper()

        if degree_str not in roman_map_upper:
            raise ValueError(f"Unknown Roman numeral: {numeral}")

        degree = roman_map_upper[degree_str]

        # Get the root note from the scale
        scale = Scale(key_root, key_mode)
        midi_root = scale.note_at_degree(degree, 0)
        root_name = NOTE_NAMES[midi_root % 12]

        # Determine quality
        if has_7:
            quality = "min7" if is_minor else "dom7"
        else:
            quality = "minor" if is_minor else "major"

        return cls(root_name, quality)

    def transpose(self, semitones: int) -> Chord:
        """Return a new Chord transposed by the given semitones."""
        new_idx = (NOTE_NAMES.index(self.root) + semitones) % 12
        return Chord(NOTE_NAMES[new_idx], self.quality)

    def __repr__(self) -> str:
        return f"Chord({self.root}, {self.quality})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chord):
            return NotImplemented
        return self.root == other.root and self.quality == other.quality


class ChordProgression:
    """An ordered sequence of chords with durations (in beats)."""

    def __init__(self, chords: list[tuple[Chord, float]]):
        self.chords = chords

    @classmethod
    def from_string(cls, s: str, key_root: str, key_mode: str = "major") -> ChordProgression:
        """Parse a string like 'I - IV - V - I' into a ChordProgression.

        Each chord gets a default duration of 4 beats (one bar of 4/4).
        Use '|' or '-' as separators.
        """
        # Normalize separators
        s = s.replace("|", "-")
        tokens = [t.strip() for t in s.split("-") if t.strip()]
        chords: list[tuple[Chord, float]] = []
        for token in tokens:
            chord = Chord.from_roman(token, key_root, key_mode)
            chords.append((chord, 4.0))
        return cls(chords)

    def transpose(self, semitones: int) -> ChordProgression:
        """Return a new progression transposed by the given semitones."""
        return ChordProgression([
            (chord.transpose(semitones), dur) for chord, dur in self.chords
        ])

    def resolve(self, octave: int = 3) -> list[tuple[list[int], float]]:
        """Resolve to a list of (midi_notes, duration_in_beats)."""
        return [(chord.midi_notes(octave), dur) for chord, dur in self.chords]

    def __repr__(self) -> str:
        parts = [f"{c.root}{c.quality}({d})" for c, d in self.chords]
        return f"ChordProgression([{', '.join(parts)}])"

    def __len__(self) -> int:
        return len(self.chords)


class ProgressionFactory:
    """Factory for common chord progressions."""

    @staticmethod
    def classic_rock_I_IV_V(key_root: str, key_mode: str = "major") -> ChordProgression:
        """I - IV - V - I progression."""
        return ChordProgression.from_string("I - IV - V - I", key_root, key_mode)

    @staticmethod
    def twelve_bar_blues(key_root: str) -> ChordProgression:
        """Standard 12-bar blues: I I I I - IV IV I I - V IV I V."""
        numerals = ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"]
        chords = []
        for n in numerals:
            chord = Chord.from_roman(n, key_root, "major")
            # Blues typically uses dom7
            chord = Chord(chord.root, "dom7")
            chords.append((chord, 4.0))
        return ChordProgression(chords)

    @staticmethod
    def pop_I_V_vi_IV(key_root: str) -> ChordProgression:
        """I - V - vi - IV (the 'pop punk' progression)."""
        return ChordProgression.from_string("I - V - vi - IV", key_root, "major")

    @staticmethod
    def rock_ballad(key_root: str) -> ChordProgression:
        """I - vi - IV - V ballad progression."""
        return ChordProgression.from_string("I - vi - IV - V", key_root, "major")
