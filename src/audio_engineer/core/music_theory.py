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

    @staticmethod
    def jazz_ii_V_I(key_root: str) -> ChordProgression:
        """ii min7 - V dom7 - I maj7 (the core jazz cadence)."""
        scale = Scale(key_root, "major")
        ii_root = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V_root = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        return ChordProgression([
            (Chord(ii_root, "min7"), 4.0),
            (Chord(V_root, "dom7"), 4.0),
            (Chord(I_root, "maj7"), 8.0),
        ])

    @staticmethod
    def jazz_turnaround(key_root: str) -> ChordProgression:
        """I maj7 - vi min7 - ii min7 - V dom7 turnaround."""
        scale = Scale(key_root, "major")
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        vi_root = NOTE_NAMES[scale.note_at_degree(6, 0) % 12]
        ii_root = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V_root = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        return ChordProgression([
            (Chord(I_root, "maj7"), 4.0),
            (Chord(vi_root, "min7"), 4.0),
            (Chord(ii_root, "min7"), 4.0),
            (Chord(V_root, "dom7"), 4.0),
        ])

    @staticmethod
    def jazz_rhythm_changes(key_root: str) -> ChordProgression:
        """A-section of Rhythm Changes (Gershwin): I - vi - ii - V pattern."""
        scale = Scale(key_root, "major")
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        vi_root = NOTE_NAMES[scale.note_at_degree(6, 0) % 12]
        ii_root = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V_root = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        IV_root = NOTE_NAMES[scale.note_at_degree(4, 0) % 12]
        return ChordProgression([
            (Chord(I_root, "maj7"), 2.0),
            (Chord(vi_root, "dom7"), 2.0),
            (Chord(ii_root, "min7"), 2.0),
            (Chord(V_root, "dom7"), 2.0),
            (Chord(I_root, "maj7"), 2.0),
            (Chord(IV_root, "dom7"), 2.0),
            (Chord(I_root, "maj7"), 2.0),
            (Chord(V_root, "dom7"), 2.0),
        ])

    @staticmethod
    def blues_jazz(key_root: str) -> ChordProgression:
        """Jazz blues with tritone substitutions and ii-V pairs."""
        scale = Scale(key_root, "major")
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        IV_root = NOTE_NAMES[scale.note_at_degree(4, 0) % 12]
        V_root = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        ii_root = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        vi_root = NOTE_NAMES[scale.note_at_degree(6, 0) % 12]
        return ChordProgression([
            (Chord(I_root, "dom7"), 4.0),
            (Chord(IV_root, "dom7"), 4.0),
            (Chord(I_root, "dom7"), 4.0),
            (Chord(I_root, "dom7"), 4.0),
            (Chord(IV_root, "dom7"), 4.0),
            (Chord(IV_root, "dom7"), 4.0),
            (Chord(I_root, "dom7"), 4.0),
            (Chord(vi_root, "min7"), 4.0),
            (Chord(ii_root, "min7"), 4.0),
            (Chord(V_root, "dom7"), 4.0),
            (Chord(I_root, "dom7"), 4.0),
            (Chord(ii_root, "min7"), 2.0),
            (Chord(V_root, "dom7"), 2.0),
        ])

    @staticmethod
    def modal_dorian(key_root: str) -> ChordProgression:
        """Dorian modal vamp: i min7 - IV dom7."""
        i_chord = Chord(key_root, "min7")
        IV_root = NOTE_NAMES[(NOTE_NAMES.index(key_root.upper()) + 5) % 12]
        return ChordProgression([
            (i_chord, 8.0),
            (Chord(IV_root, "dom7"), 8.0),
        ])

    @staticmethod
    def bossa_nova(key_root: str) -> ChordProgression:
        """Bossa nova: ii min7 - V dom7 - I maj7 with sus coloring."""
        scale = Scale(key_root, "major")
        ii_root = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V_root = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        iii_root = NOTE_NAMES[scale.note_at_degree(3, 0) % 12]
        return ChordProgression([
            (Chord(I_root, "maj7"), 4.0),
            (Chord(iii_root, "min7"), 2.0),
            (Chord(ii_root, "min7"), 2.0),
            (Chord(V_root, "dom7"), 4.0),
            (Chord(I_root, "maj7"), 4.0),
        ])

    @staticmethod
    def minor_i_VII_VI_VII(key_root: str) -> ChordProgression:
        """Natural minor vamp: i - bVII - bVI - bVII."""
        return ChordProgression.from_string("I - VII - VI - VII", key_root, "minor")

    @staticmethod
    def gospel_I_IV_I_V(key_root: str) -> ChordProgression:
        """Gospel: I - IV - I - V turnaround."""
        return ChordProgression.from_string("I - IV - I - V", key_root, "major")

    @staticmethod
    def metal_power_I_VII_VI(key_root: str) -> ChordProgression:
        """Metal power chord progression: I5 - bVII5 - bVI5 - bVII5."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bVII_root = NOTE_NAMES[(root_idx + 10) % 12]
        bVI_root = NOTE_NAMES[(root_idx + 8) % 12]
        return ChordProgression([
            (Chord(key_root, "power"), 4.0),
            (Chord(bVII_root, "power"), 4.0),
            (Chord(bVI_root, "power"), 4.0),
            (Chord(bVII_root, "power"), 4.0),
        ])

    @staticmethod
    def funk_I7_IV7(key_root: str) -> ChordProgression:
        """Funk dominant 7th vamp: I7 - IV7."""
        IV_root = NOTE_NAMES[(NOTE_NAMES.index(key_root.strip().upper()) + 5) % 12]
        return ChordProgression([
            (Chord(key_root, "dom7"), 8.0),
            (Chord(IV_root, "dom7"), 8.0),
        ])

    # ------------------------------------------------------------------
    # Expanded progressions for new genres
    # ------------------------------------------------------------------

    @staticmethod
    def indie_I_vi_iii_IV(key_root: str) -> ChordProgression:
        """Indie / dream-pop: I - vi - iii - IV."""
        return ChordProgression.from_string("I - vi - iii - IV", key_root, "major")

    @staticmethod
    def grunge_minor_vamp(key_root: str) -> ChordProgression:
        """Grunge minor power vamp: i - bIII - bVII - IV."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bIII = NOTE_NAMES[(root_idx + 3) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        IV = NOTE_NAMES[(root_idx + 5) % 12]
        return ChordProgression([
            (Chord(key_root, "power"), 4.0),
            (Chord(bIII, "power"), 4.0),
            (Chord(bVII, "power"), 4.0),
            (Chord(IV, "power"), 4.0),
        ])

    @staticmethod
    def prog_rock_epic(key_root: str) -> ChordProgression:
        """Prog-rock: I - III - bVII - IV (mixed-mode colour)."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        III = NOTE_NAMES[(root_idx + 4) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        IV = NOTE_NAMES[(root_idx + 5) % 12]
        return ChordProgression([
            (Chord(key_root, "maj7"), 4.0),
            (Chord(III, "major"), 4.0),
            (Chord(bVII, "major"), 4.0),
            (Chord(IV, "major"), 4.0),
        ])

    @staticmethod
    def disco_I_vi_ii_V(key_root: str) -> ChordProgression:
        """Disco / dance: I - vi - ii - V."""
        scale = Scale(key_root, "major")
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        vi = NOTE_NAMES[scale.note_at_degree(6, 0) % 12]
        ii = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        return ChordProgression([
            (Chord(I_root, "major"), 4.0),
            (Chord(vi, "minor"), 4.0),
            (Chord(ii, "minor"), 4.0),
            (Chord(V, "dom7"), 4.0),
        ])

    @staticmethod
    def synthwave_i_III_VII_VI(key_root: str) -> ChordProgression:
        """Synthwave / retrowave: i - bIII - bVII - bVI."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bIII = NOTE_NAMES[(root_idx + 3) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        bVI = NOTE_NAMES[(root_idx + 8) % 12]
        return ChordProgression([
            (Chord(key_root, "minor"), 4.0),
            (Chord(bIII, "major"), 4.0),
            (Chord(bVII, "major"), 4.0),
            (Chord(bVI, "major"), 4.0),
        ])

    @staticmethod
    def trap_minor_vamp(key_root: str) -> ChordProgression:
        """Trap / dark hip-hop: i - bVI - bIII - bVII."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bVI = NOTE_NAMES[(root_idx + 8) % 12]
        bIII = NOTE_NAMES[(root_idx + 3) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "minor"), 4.0),
            (Chord(bVI, "major"), 4.0),
            (Chord(bIII, "major"), 4.0),
            (Chord(bVII, "major"), 4.0),
        ])

    @staticmethod
    def trance_uplifting(key_root: str) -> ChordProgression:
        """Trance / uplifting: vi - IV - I - V."""
        return ChordProgression.from_string("vi - IV - I - V", key_root, "major")

    @staticmethod
    def dubstep_halftime(key_root: str) -> ChordProgression:
        """Dubstep / halftime: i - bVII (two-chord minor vamp)."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "minor"), 8.0),
            (Chord(bVII, "major"), 8.0),
        ])

    @staticmethod
    def dnb_minor_tension(key_root: str) -> ChordProgression:
        """Drum-and-bass: i - iv - bVI - bVII."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        iv = NOTE_NAMES[(root_idx + 5) % 12]
        bVI = NOTE_NAMES[(root_idx + 8) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "minor"), 4.0),
            (Chord(iv, "minor"), 4.0),
            (Chord(bVI, "major"), 4.0),
            (Chord(bVII, "major"), 4.0),
        ])

    @staticmethod
    def salsa_montuno(key_root: str) -> ChordProgression:
        """Salsa / son montuno: I - IV - V - I."""
        return ChordProgression.from_string("I - IV - V - I", key_root, "major")

    @staticmethod
    def reggaeton_i_IV_V(key_root: str) -> ChordProgression:
        """Reggaeton: i - iv - V (minor with dominant turnaround)."""
        scale = Scale(key_root, "minor")
        i = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        iv = NOTE_NAMES[scale.note_at_degree(4, 0) % 12]
        V_root = NOTE_NAMES[(NOTE_NAMES.index(key_root.strip().upper()) + 7) % 12]
        return ChordProgression([
            (Chord(i, "minor"), 4.0),
            (Chord(iv, "minor"), 4.0),
            (Chord(V_root, "major"), 4.0),
            (Chord(i, "minor"), 4.0),
        ])

    @staticmethod
    def ska_offbeat(key_root: str) -> ChordProgression:
        """Ska: I - IV - V - IV (bright, upbeat)."""
        return ChordProgression.from_string("I - IV - V - IV", key_root, "major")

    @staticmethod
    def afrobeat_vamp(key_root: str) -> ChordProgression:
        """Afrobeat: extended i7 - IV7 vamp."""
        IV_root = NOTE_NAMES[(NOTE_NAMES.index(key_root.strip().upper()) + 5) % 12]
        return ChordProgression([
            (Chord(key_root, "min7"), 8.0),
            (Chord(IV_root, "dom7"), 4.0),
            (Chord(key_root, "min7"), 4.0),
        ])

    @staticmethod
    def flamenco_phrygian(key_root: str) -> ChordProgression:
        """Flamenco Phrygian cadence: iv - bIII - bII - I."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        iv = NOTE_NAMES[(root_idx + 5) % 12]
        bIII = NOTE_NAMES[(root_idx + 3) % 12]
        bII = NOTE_NAMES[(root_idx + 1) % 12]
        return ChordProgression([
            (Chord(iv, "minor"), 4.0),
            (Chord(bIII, "major"), 4.0),
            (Chord(bII, "major"), 4.0),
            (Chord(key_root, "major"), 4.0),
        ])

    @staticmethod
    def middle_eastern_hijaz(key_root: str) -> ChordProgression:
        """Middle-Eastern Hijaz mode colour: I - bII - I - bVII."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bII = NOTE_NAMES[(root_idx + 1) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "major"), 4.0),
            (Chord(bII, "major"), 4.0),
            (Chord(key_root, "major"), 4.0),
            (Chord(bVII, "minor"), 4.0),
        ])

    @staticmethod
    def classical_I_IV_V_I(key_root: str) -> ChordProgression:
        """Classical: I - IV - V - I (authentic cadence)."""
        return ChordProgression.from_string("I - IV - V - I", key_root, "major")

    @staticmethod
    def baroque_circle_of_fifths(key_root: str) -> ChordProgression:
        """Baroque circle-of-fifths: I - IV - vii - iii - vi - ii - V - I."""
        return ChordProgression.from_string(
            "I - IV - vii - iii - vi - ii - V - I", key_root, "major"
        )

    @staticmethod
    def cinematic_epic(key_root: str) -> ChordProgression:
        """Cinematic / epic: i - bVI - bIII - bVII."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bVI = NOTE_NAMES[(root_idx + 8) % 12]
        bIII = NOTE_NAMES[(root_idx + 3) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "minor"), 4.0),
            (Chord(bVI, "major"), 4.0),
            (Chord(bIII, "major"), 4.0),
            (Chord(bVII, "major"), 4.0),
        ])

    @staticmethod
    def bluegrass_I_IV_V(key_root: str) -> ChordProgression:
        """Bluegrass: I - IV - V - I."""
        return ChordProgression.from_string("I - IV - V - I", key_root, "major")

    @staticmethod
    def neo_soul_ii_V_I(key_root: str) -> ChordProgression:
        """Neo-soul: ii min9 - V dom9 - I maj9."""
        scale = Scale(key_root, "major")
        ii = NOTE_NAMES[scale.note_at_degree(2, 0) % 12]
        V = NOTE_NAMES[scale.note_at_degree(5, 0) % 12]
        I_root = NOTE_NAMES[scale.note_at_degree(1, 0) % 12]
        return ChordProgression([
            (Chord(ii, "min9"), 4.0),
            (Chord(V, "dom9"), 4.0),
            (Chord(I_root, "maj9"), 8.0),
        ])

    @staticmethod
    def worship_I_IV_vi_V(key_root: str) -> ChordProgression:
        """Worship / praise: I - IV - vi - V."""
        return ChordProgression.from_string("I - IV - vi - V", key_root, "major")

    @staticmethod
    def post_rock_ambient(key_root: str) -> ChordProgression:
        """Post-rock: I - iii - vi - IV (slow, expansive)."""
        return ChordProgression.from_string("I - iii - vi - IV", key_root, "major")

    @staticmethod
    def math_rock_odd(key_root: str) -> ChordProgression:
        """Math-rock: I - III - vi - ii (non-obvious voicings)."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        III = NOTE_NAMES[(root_idx + 4) % 12]
        vi = NOTE_NAMES[(root_idx + 9) % 12]
        ii = NOTE_NAMES[(root_idx + 2) % 12]
        return ChordProgression([
            (Chord(key_root, "major"), 3.5),
            (Chord(III, "major"), 3.5),
            (Chord(vi, "minor"), 3.5),
            (Chord(ii, "minor"), 3.5),
        ])

    @staticmethod
    def emo_vi_IV_I_V(key_root: str) -> ChordProgression:
        """Emo: vi - IV - I - V."""
        return ChordProgression.from_string("vi - IV - I - V", key_root, "major")

    @staticmethod
    def industrial_power_riff(key_root: str) -> ChordProgression:
        """Industrial / EBM: i5 - bII5 - i5 - bVII5."""
        root_idx = NOTE_NAMES.index(key_root.strip().upper()) if key_root.strip().upper() in NOTE_NAMES else 0
        bII = NOTE_NAMES[(root_idx + 1) % 12]
        bVII = NOTE_NAMES[(root_idx + 10) % 12]
        return ChordProgression([
            (Chord(key_root, "power"), 4.0),
            (Chord(bII, "power"), 4.0),
            (Chord(key_root, "power"), 4.0),
            (Chord(bVII, "power"), 4.0),
        ])
