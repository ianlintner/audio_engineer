"""Pattern Repository - Pre-built drum, bass, and melodic patterns."""

from .models import Genre, NoteEvent, TimeSignature
from .constants import GM_DRUMS, TICKS_PER_BEAT


class DrumPattern:
    """A single bar drum pattern."""

    def __init__(
        self,
        name: str,
        genre: Genre,
        time_sig: TimeSignature | None = None,
        kicks: list[float] | None = None,
        snares: list[float] | None = None,
        hihats: list[float] | None = None,
        open_hihats: list[float] | None = None,
        crashes: list[float] | None = None,
        rides: list[float] | None = None,
        velocity_map: dict[str, int] | None = None,
    ):
        self.name = name
        self.genre = genre
        self.time_sig = time_sig or TimeSignature()
        self.kicks = kicks or []
        self.snares = snares or []
        self.hihats = hihats or []
        self.open_hihats = open_hihats or []
        self.crashes = crashes or []
        self.rides = rides or []
        self.velocity_map = velocity_map or {
            "kick": 100,
            "snare": 95,
            "hihat": 80,
            "open_hihat": 85,
            "crash": 110,
            "ride": 75,
        }

    def to_events(self, bar_offset: int = 0, intensity: float = 1.0) -> list[NoteEvent]:
        """Convert pattern to NoteEvents for a specific bar."""
        events: list[NoteEvent] = []
        tpb = TICKS_PER_BEAT
        bar_start = bar_offset * tpb * self.time_sig.numerator

        vel_scale = max(0.3, min(1.0, intensity))

        def add_hits(positions: list[float], drum_key: str, duration_beats: float = 0.25) -> None:
            vel = int(self.velocity_map.get(drum_key, 80) * vel_scale)
            for pos in positions:
                tick = bar_start + int((pos - 1.0) * tpb)
                events.append(NoteEvent(
                    pitch=GM_DRUMS[drum_key],
                    velocity=vel,
                    start_tick=tick,
                    duration_ticks=int(duration_beats * tpb),
                    channel=9,
                ))

        add_hits(self.kicks, "kick")
        add_hits(self.snares, "snare")
        add_hits(self.hihats, "closed_hihat")
        add_hits(self.open_hihats, "open_hihat")
        add_hits(self.crashes, "crash")
        add_hits(self.rides, "ride")

        return events


class DrumFill:
    """A drum fill spanning specified beats."""

    def __init__(self, name: str, genre: Genre, events: list[NoteEvent] | None = None):
        self.name = name
        self.genre = genre
        self.events = events or []

    def to_events(self, bar_offset: int, beat_start: float = 3.0) -> list[NoteEvent]:
        """Get fill events positioned at a specific bar and beat."""
        tpb = TICKS_PER_BEAT
        offset_ticks = bar_offset * tpb * 4 + int((beat_start - 1.0) * tpb)
        return [
            e.model_copy(update={"start_tick": e.start_tick + offset_ticks})
            for e in self.events
        ]


class PatternRepository:
    """Library of patterns indexed by genre."""

    def __init__(self):
        self._drum_patterns: dict[Genre, list[DrumPattern]] = {}
        self._drum_fills: dict[Genre, list[DrumFill]] = {}
        self._register_defaults()
        self._register_extended_patterns()

    def _register_defaults(self) -> None:
        # Classic Rock patterns
        self.register_drum_pattern(DrumPattern(
            name="rock_straight_8th",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="rock_driving",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0, 1.5, 3.0, 3.5],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="rock_half_time",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0],
            snares=[3.0],
            hihats=[1.0, 2.0, 3.0, 4.0],
        ))
        self.register_drum_pattern(DrumPattern(
            name="rock_four_on_floor",
            genre=Genre.CLASSIC_ROCK,
            kicks=[1.0, 2.0, 3.0, 4.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # Blues patterns
        self.register_drum_pattern(DrumPattern(
            name="blues_shuffle",
            genre=Genre.BLUES,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.67, 2.0, 2.67, 3.0, 3.67, 4.0, 4.67],
        ))
        self.register_drum_pattern(DrumPattern(
            name="blues_slow",
            genre=Genre.BLUES,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            rides=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # Pop patterns
        self.register_drum_pattern(DrumPattern(
            name="pop_basic",
            genre=Genre.POP,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # Rock fills
        tpb = TICKS_PER_BEAT
        self.register_drum_fill(DrumFill(
            name="tom_roll_2beat",
            genre=Genre.CLASSIC_ROCK,
            events=[
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=100, start_tick=0, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=95, start_tick=tpb // 2, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=100, start_tick=tpb, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=95, start_tick=tpb + tpb // 2, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["floor_tom"], velocity=105, start_tick=tpb * 2 - tpb // 4, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=110, start_tick=tpb * 2, duration_ticks=tpb, channel=9),
            ],
        ))
        self.register_drum_fill(DrumFill(
            name="snare_build",
            genre=Genre.CLASSIC_ROCK,
            events=[
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=80, start_tick=0, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=85, start_tick=tpb // 4, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=90, start_tick=tpb // 2, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=95, start_tick=3 * tpb // 4, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=100, start_tick=tpb, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=110, start_tick=5 * tpb // 4, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=120, start_tick=3 * tpb // 2, duration_ticks=tpb, channel=9),
            ],
        ))

        # Blues fills
        self.register_drum_fill(DrumFill(
            name="blues_turnaround",
            genre=Genre.BLUES,
            events=[
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=85, start_tick=0, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=90, start_tick=tpb // 2, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=95, start_tick=tpb, duration_ticks=tpb // 2, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=100, start_tick=3 * tpb // 2, duration_ticks=tpb, channel=9),
            ],
        ))

    def register_drum_pattern(self, pattern: DrumPattern) -> None:
        self._drum_patterns.setdefault(pattern.genre, []).append(pattern)

    def register_drum_fill(self, fill: DrumFill) -> None:
        self._drum_fills.setdefault(fill.genre, []).append(fill)

    def get_drum_patterns(self, genre: Genre) -> list[DrumPattern]:
        return self._drum_patterns.get(genre, [])

    def get_drum_fills(self, genre: Genre) -> list[DrumFill]:
        return self._drum_fills.get(genre, [])

    def get_pattern_by_name(self, name: str) -> DrumPattern | None:
        for patterns in self._drum_patterns.values():
            for p in patterns:
                if p.name == name:
                    return p
        return None

    def _register_extended_patterns(self) -> None:
        """Register extended genre patterns."""
        tpb = TICKS_PER_BEAT
        s16 = tpb // 4  # sixteenth note ticks

        # ---- Jazz ----
        self.register_drum_pattern(DrumPattern(
            name="jazz_ride_swing",
            genre=Genre.JAZZ,
            rides=[1.0, 1.67, 2.0, 2.67, 3.0, 3.67, 4.0, 4.67],
            kicks=[1.0, 3.0],
            snares=[3.0],
        ))
        self.register_drum_pattern(DrumPattern(
            name="jazz_2beat",
            genre=Genre.JAZZ,
            kicks=[1.0, 3.0],
            rides=[1.0, 2.0, 3.0, 4.0],
        ))
        self.register_drum_pattern(DrumPattern(
            name="jazz_bossa",
            genre=Genre.JAZZ,
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
            kicks=[1.0, 2.5],
            snares=[2.0, 4.0],
        ))
        self.register_drum_pattern(DrumPattern(
            name="bebop_fast",
            genre=Genre.JAZZ,
            rides=[1.0, 1.33, 1.67, 2.0, 2.33, 2.67, 3.0, 3.33, 3.67, 4.0, 4.33, 4.67],
            kicks=[1.0],
            snares=[2.0, 4.0],
        ))
        # Bebop genre alias
        self.register_drum_pattern(DrumPattern(
            name="bebop_ride_pattern",
            genre=Genre.BEBOP,
            rides=[1.0, 1.33, 1.67, 2.0, 2.33, 2.67, 3.0, 3.33, 3.67, 4.0, 4.33, 4.67],
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
        ))
        # Swing genre
        self.register_drum_pattern(DrumPattern(
            name="swing_ride",
            genre=Genre.SWING,
            rides=[1.0, 1.67, 2.0, 2.67, 3.0, 3.67, 4.0, 4.67],
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
        ))

        # ---- Funk ----
        self.register_drum_pattern(DrumPattern(
            name="funk_16th_hihat",
            genre=Genre.FUNK,
            kicks=[1.0, 2.75, 3.5],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="funk_syncopated",
            genre=Genre.FUNK,
            kicks=[1.0, 1.75, 3.0, 3.75],
            snares=[2.0, 2.5, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="funk_broken_beat",
            genre=Genre.FUNK,
            kicks=[1.0, 2.5, 3.25],
            snares=[1.75, 3.0, 4.5],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 2.75, 3.25, 3.5, 4.0, 4.25],
        ))
        self.register_drum_pattern(DrumPattern(
            name="new_orleans_second_line",
            genre=Genre.FUNK,
            kicks=[1.0, 2.5, 3.0],
            snares=[1.5, 2.0, 3.5, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # ---- Reggae ----
        self.register_drum_pattern(DrumPattern(
            name="reggae_one_drop",
            genre=Genre.REGGAE,
            kicks=[3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="reggae_steppers",
            genre=Genre.REGGAE,
            kicks=[1.0, 2.0, 3.0, 4.0],
            snares=[2.0, 4.0],
            hihats=[1.5, 2.5, 3.5, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="reggae_rockers",
            genre=Genre.REGGAE,
            kicks=[1.0, 3.0],
            snares=[2.5, 4.5],
            rides=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # ---- Soul / R&B ----
        self.register_drum_pattern(DrumPattern(
            name="soul_gospel_groove",
            genre=Genre.SOUL,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="motown_snare_16th",
            genre=Genre.SOUL,
            kicks=[1.0, 3.0],
            snares=[2.0, 2.5, 4.0, 4.5],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="rnb_groove",
            genre=Genre.RNB,
            kicks=[1.0, 2.75, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))

        # ---- Metal ----
        self.register_drum_pattern(DrumPattern(
            name="metal_blast_beat",
            genre=Genre.METAL,
            kicks=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                   3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
            snares=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="metal_double_kick",
            genre=Genre.METAL,
            kicks=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="metal_gallop",
            genre=Genre.METAL,
            kicks=[1.0, 1.33, 1.67, 2.0, 2.33, 2.67, 3.0, 3.33, 3.67, 4.0, 4.33, 4.67],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="metal_half_time",
            genre=Genre.METAL,
            kicks=[1.0, 1.5],
            snares=[3.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # ---- Hip-Hop ----
        self.register_drum_pattern(DrumPattern(
            name="hip_hop_boom_bap",
            genre=Genre.HIP_HOP,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="hip_hop_trap",
            genre=Genre.HIP_HOP,
            kicks=[1.0, 2.75, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="lofi_groove",
            genre=Genre.HIP_HOP,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 2.0, 3.0, 4.0],
        ))

        # ---- Latin ----
        self.register_drum_pattern(DrumPattern(
            name="bossa_nova_drum",
            genre=Genre.BOSSA_NOVA,
            kicks=[1.0, 2.5],
            snares=[2.0, 3.5],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="samba_surdo",
            genre=Genre.LATIN,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="clave_son",
            genre=Genre.LATIN,
            kicks=[1.0, 2.5, 3.5],
            snares=[2.0, 3.0, 4.5],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="cha_cha",
            genre=Genre.LATIN,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))
        self.register_drum_pattern(DrumPattern(
            name="mambo_groove",
            genre=Genre.LATIN,
            kicks=[1.0, 2.5, 3.0, 4.5],
            snares=[2.0, 3.5],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
        ))

        # ---- Electronic ----
        self.register_drum_pattern(DrumPattern(
            name="four_on_floor_edm",
            genre=Genre.ELECTRONIC,
            kicks=[1.0, 2.0, 3.0, 4.0],
            snares=[2.0, 4.0],
            hihats=[1.25, 1.5, 1.75, 2.25, 2.5, 2.75, 3.25, 3.5, 3.75, 4.25, 4.5, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="house_groove",
            genre=Genre.HOUSE,
            kicks=[1.0, 2.0, 3.0, 4.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
            open_hihats=[1.75, 2.75, 3.75, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="techno_kick",
            genre=Genre.ELECTRONIC,
            kicks=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
            snares=[2.0, 4.0],
            hihats=[1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75],
        ))
        self.register_drum_pattern(DrumPattern(
            name="breakbeat",
            genre=Genre.ELECTRONIC,
            kicks=[1.0, 2.5, 3.0],
            snares=[1.75, 2.0, 4.0],
            hihats=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
                    3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75],
        ))

        # ---- Gospel ----
        self.register_drum_pattern(DrumPattern(
            name="gospel_groove",
            genre=Genre.GOSPEL,
            kicks=[1.0, 3.0],
            snares=[2.0, 4.0],
            hihats=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
            crashes=[1.0],
        ))

        # ---- Ambient ----
        self.register_drum_pattern(DrumPattern(
            name="ambient_sparse",
            genre=Genre.AMBIENT,
            kicks=[1.0],
            rides=[1.0, 2.0, 3.0, 4.0],
        ))

        # ---- Extended fills for new genres ----
        self.register_drum_fill(DrumFill(
            name="jazz_fill",
            genre=Genre.JAZZ,
            events=[
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=85, start_tick=0, duration_ticks=tpb // 3, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=90, start_tick=tpb // 3, duration_ticks=tpb // 3, channel=9),
                NoteEvent(pitch=GM_DRUMS["floor_tom"], velocity=95, start_tick=2 * tpb // 3, duration_ticks=tpb // 3, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=100, start_tick=tpb, duration_ticks=tpb // 4, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=105, start_tick=tpb + tpb // 2, duration_ticks=tpb, channel=9),
            ],
        ))
        self.register_drum_fill(DrumFill(
            name="funk_fill",
            genre=Genre.FUNK,
            events=[
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=90, start_tick=0, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=80, start_tick=s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=95, start_tick=2 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=100, start_tick=3 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=100, start_tick=4 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["floor_tom"], velocity=105, start_tick=5 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=110, start_tick=8 * s16, duration_ticks=tpb, channel=9),
            ],
        ))
        self.register_drum_fill(DrumFill(
            name="metal_fill",
            genre=Genre.METAL,
            events=[
                NoteEvent(pitch=GM_DRUMS["snare"], velocity=110, start_tick=i * s16, duration_ticks=s16, channel=9)
                for i in range(8)
            ] + [
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=127, start_tick=8 * s16, duration_ticks=tpb, channel=9),
            ],
        ))
        self.register_drum_fill(DrumFill(
            name="latin_fill",
            genre=Genre.LATIN,
            events=[
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=90, start_tick=0, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["high_tom"], velocity=85, start_tick=s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["mid_tom"], velocity=90, start_tick=2 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["floor_tom"], velocity=95, start_tick=3 * s16, duration_ticks=s16, channel=9),
                NoteEvent(pitch=GM_DRUMS["crash"], velocity=105, start_tick=4 * s16, duration_ticks=tpb, channel=9),
            ],
        ))


# ---------------------------------------------------------------------------
# DrumRudiment — 40 PAS Standard Rudiments encoded as NoteEvent sequences
# ---------------------------------------------------------------------------

# Convention: pitch 38 = snare (right hand), pitch 37 = rim/cross-stick (left hand)
_R = 38   # right snare
_L = 37   # left snare (rim shot / ghost note representation)
_ACCENT = 110
_NORMAL = 80
_GHOST = 55


def _e(pitch: int, vel: int, start_16th: int, dur_16th: int = 1) -> NoteEvent:
    """Helper to build a NoteEvent from 16th-note grid positions."""
    s = TICKS_PER_BEAT // 4
    return NoteEvent(
        pitch=pitch, velocity=vel,
        start_tick=start_16th * s,
        duration_ticks=dur_16th * s,
        channel=9,
    )


class DrumRudiment:
    """A single drum rudiment encoded as NoteEvents (one repetition)."""

    def __init__(self, name: str, events: list[NoteEvent]):
        self.name = name
        self.events = events

    def to_events(self, bar_offset: int = 0, beat_offset: float = 1.0) -> list[NoteEvent]:
        """Place rudiment events at given bar / beat position."""
        tpb = TICKS_PER_BEAT
        offset = bar_offset * tpb * 4 + int((beat_offset - 1.0) * tpb)
        return [
            e.model_copy(update={"start_tick": e.start_tick + offset})
            for e in self.events
        ]


# Build the 40 standard rudiments
def _build_rudiments() -> dict[str, DrumRudiment]:  # noqa: C901
    s = TICKS_PER_BEAT // 4  # sixteenth note

    def _ne(pitch: int, vel: int, tick: int) -> NoteEvent:
        return NoteEvent(pitch=pitch, velocity=vel, start_tick=tick, duration_ticks=s, channel=9)

    rudiments: dict[str, DrumRudiment] = {}

    # --- Rolls ---
    # Single stroke roll (8 alternating 16ths)
    rudiments["single_stroke_roll"] = DrumRudiment("single_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL, i * s) for i in range(8)
    ])
    # Single stroke 4 (RLRL)
    rudiments["single_stroke_4"] = DrumRudiment("single_stroke_4", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
    ])
    # Single stroke 7 (RLRLRLR)
    rudiments["single_stroke_7"] = DrumRudiment("single_stroke_7", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL, i * s) for i in range(7)
    ])
    # Double stroke open roll (RRLLRRLL)
    rudiments["double_stroke_roll"] = DrumRudiment("double_stroke_roll", [
        _ne(_R, _ACCENT, 0), _ne(_R, _NORMAL, s),
        _ne(_L, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
        _ne(_R, _ACCENT, 4 * s), _ne(_R, _NORMAL, 5 * s),
        _ne(_L, _NORMAL, 6 * s), _ne(_L, _NORMAL, 7 * s),
    ])
    # Triple stroke roll (RRRLLLS)
    rudiments["triple_stroke_roll"] = DrumRudiment("triple_stroke_roll", [
        _ne(_R, _ACCENT, 0), _ne(_R, _NORMAL, s), _ne(_R, _NORMAL, 2 * s),
        _ne(_L, _NORMAL, 3 * s), _ne(_L, _NORMAL, 4 * s), _ne(_L, _NORMAL, 5 * s),
    ])
    # Multiple bounce roll (buzz — represented as fast doubles)
    rudiments["multiple_bounce_roll"] = DrumRudiment("multiple_bounce_roll", [
        _ne(_R, _ACCENT, 0), _ne(_R, _GHOST, s // 2),
        _ne(_L, _NORMAL, s), _ne(_L, _GHOST, s + s // 2),
        _ne(_R, _NORMAL, 2 * s), _ne(_R, _GHOST, 2 * s + s // 2),
        _ne(_L, _NORMAL, 3 * s), _ne(_L, _GHOST, 3 * s + s // 2),
    ])
    # 5-stroke roll: RRLL R
    rudiments["5_stroke_roll"] = DrumRudiment("5_stroke_roll", [
        _ne(_R, _NORMAL, 0), _ne(_R, _NORMAL, s),
        _ne(_L, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
        _ne(_R, _ACCENT, 4 * s),
    ])
    # 6-stroke roll: RLLRRL
    rudiments["6_stroke_roll"] = DrumRudiment("6_stroke_roll", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s), _ne(_L, _NORMAL, 2 * s),
        _ne(_R, _NORMAL, 3 * s), _ne(_R, _NORMAL, 4 * s), _ne(_L, _ACCENT, 5 * s),
    ])
    # 7-stroke roll: RRLLRRL
    rudiments["7_stroke_roll"] = DrumRudiment("7_stroke_roll", [
        _ne(_R, _NORMAL, 0), _ne(_R, _NORMAL, s),
        _ne(_L, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
        _ne(_R, _NORMAL, 4 * s), _ne(_R, _NORMAL, 5 * s),
        _ne(_L, _ACCENT, 6 * s),
    ])
    # 9-stroke roll
    rudiments["9_stroke_roll"] = DrumRudiment("9_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 8 else _ACCENT, i * s)
        for i in range(9)
    ])
    # 10-stroke roll
    rudiments["10_stroke_roll"] = DrumRudiment("10_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 9 else _ACCENT, i * s)
        for i in range(10)
    ])
    # 11-stroke roll
    rudiments["11_stroke_roll"] = DrumRudiment("11_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 10 else _ACCENT, i * s)
        for i in range(11)
    ])
    # 13-stroke roll
    rudiments["13_stroke_roll"] = DrumRudiment("13_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 12 else _ACCENT, i * s)
        for i in range(13)
    ])
    # 15-stroke roll
    rudiments["15_stroke_roll"] = DrumRudiment("15_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 14 else _ACCENT, i * s)
        for i in range(15)
    ])
    # 17-stroke roll
    rudiments["17_stroke_roll"] = DrumRudiment("17_stroke_roll", [
        _ne(_R if i % 2 == 0 else _L, _NORMAL if i < 16 else _ACCENT, i * s)
        for i in range(17)
    ])

    # --- Diddles ---
    # Single paradiddle: RLRR
    rudiments["single_paradiddle"] = DrumRudiment("single_paradiddle", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s), _ne(_R, _NORMAL, 3 * s),
    ])
    # Double paradiddle: RLRLRR
    rudiments["double_paradiddle"] = DrumRudiment("double_paradiddle", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
        _ne(_R, _NORMAL, 4 * s), _ne(_R, _NORMAL, 5 * s),
    ])
    # Triple paradiddle: RLRLRLRR
    rudiments["triple_paradiddle"] = DrumRudiment("triple_paradiddle", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s), _ne(_L, _NORMAL, 3 * s),
        _ne(_R, _NORMAL, 4 * s), _ne(_L, _NORMAL, 5 * s),
        _ne(_R, _NORMAL, 6 * s), _ne(_R, _NORMAL, 7 * s),
    ])
    # Single paradiddle-diddle: RLRRLL
    rudiments["single_paradiddle_diddle"] = DrumRudiment("single_paradiddle_diddle", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s), _ne(_R, _NORMAL, 3 * s),
        _ne(_L, _NORMAL, 4 * s), _ne(_L, _NORMAL, 5 * s),
    ])

    # --- Flams ---
    # Flam: grace note before accent (grace = 1/4 of s before)
    g = s // 4  # grace note offset
    rudiments["flam"] = DrumRudiment("flam", [
        _ne(_L, _GHOST, 0),
        _ne(_R, _ACCENT, g),
    ])
    # Flam accent: L(RL)R
    rudiments["flam_accent"] = DrumRudiment("flam_accent", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _NORMAL, s + g),
        _ne(_R, _GHOST, 2 * s), _ne(_L, _ACCENT, 2 * s + g),
    ])
    # Flam tap: LLR / RRL
    rudiments["flam_tap"] = DrumRudiment("flam_tap", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_R, _NORMAL, s + g),
        _ne(_R, _GHOST, 2 * s), _ne(_L, _ACCENT, 2 * s + g),
        _ne(_L, _NORMAL, 3 * s + g),
    ])
    # Flamacue: LRLRL with flam
    rudiments["flamacue"] = DrumRudiment("flamacue", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _NORMAL, s + g), _ne(_R, _NORMAL, 2 * s + g), _ne(_L, _NORMAL, 3 * s + g),
        _ne(_R, _GHOST, 4 * s), _ne(_L, _ACCENT, 4 * s + g),
    ])
    # Flam paradiddle: LRLLRR
    rudiments["flam_paradiddle"] = DrumRudiment("flam_paradiddle", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _NORMAL, s + g),
        _ne(_R, _NORMAL, 2 * s + g), _ne(_R, _NORMAL, 3 * s + g),
    ])
    # Single flammed mill: LRRL
    rudiments["single_flammed_mill"] = DrumRudiment("single_flammed_mill", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_R, _NORMAL, s + g),
        _ne(_R, _GHOST, 2 * s), _ne(_L, _ACCENT, 2 * s + g),
    ])
    # Flam paradiddle-diddle: LRLLRRLL
    rudiments["flam_paradiddle_diddle"] = DrumRudiment("flam_paradiddle_diddle", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _NORMAL, s + g), _ne(_R, _NORMAL, 2 * s + g), _ne(_R, _NORMAL, 3 * s + g),
        _ne(_L, _NORMAL, 4 * s + g), _ne(_L, _NORMAL, 5 * s + g),
    ])
    # Pataflafla: RLRLRL pattern with flams
    rudiments["pataflafla"] = DrumRudiment("pataflafla", [
        _ne(_R, _ACCENT, 0), _ne(_L, _GHOST, g), _ne(_L, _ACCENT, s),
        _ne(_R, _GHOST, s + g), _ne(_R, _ACCENT, 2 * s), _ne(_L, _GHOST, 2 * s + g),
        _ne(_L, _ACCENT, 3 * s), _ne(_R, _GHOST, 3 * s + g),
    ])
    # Swiss army triplet
    rudiments["swiss_army_triplet"] = DrumRudiment("swiss_army_triplet", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_R, _NORMAL, s), _ne(_L, _NORMAL, 2 * s),
    ])
    # Inverted flam tap
    rudiments["inverted_flam_tap"] = DrumRudiment("inverted_flam_tap", [
        _ne(_R, _GHOST, 0), _ne(_L, _ACCENT, g),
        _ne(_L, _NORMAL, s + g),
        _ne(_L, _GHOST, 2 * s), _ne(_R, _ACCENT, 2 * s + g),
        _ne(_R, _NORMAL, 3 * s + g),
    ])
    # Flam drag
    rudiments["flam_drag"] = DrumRudiment("flam_drag", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _GHOST, s), _ne(_L, _GHOST, s + s // 3),
        _ne(_R, _ACCENT, 2 * s),
    ])
    # Single flam drag
    rudiments["single_flam_drag"] = DrumRudiment("single_flam_drag", [
        _ne(_L, _GHOST, 0), _ne(_R, _ACCENT, g),
        _ne(_L, _GHOST, s), _ne(_L, _GHOST, s + g),
        _ne(_R, _ACCENT, 2 * s),
        _ne(_R, _GHOST, 3 * s), _ne(_L, _ACCENT, 3 * s + g),
        _ne(_R, _GHOST, 4 * s), _ne(_R, _GHOST, 4 * s + g),
        _ne(_L, _ACCENT, 5 * s),
    ])

    # --- Drags ---
    # Drag: two grace notes before accent (LLRR)
    d = s // 4
    rudiments["drag"] = DrumRudiment("drag", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d),
        _ne(_R, _ACCENT, 2 * d),
    ])
    # Single drag tap: LLRR / RRLL
    rudiments["single_drag_tap"] = DrumRudiment("single_drag_tap", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d),
        _ne(_R, _ACCENT, 2 * d), _ne(_R, _NORMAL, s + 2 * d),
        _ne(_R, _GHOST, 2 * s), _ne(_R, _GHOST, 2 * s + d),
        _ne(_L, _ACCENT, 2 * s + 2 * d), _ne(_L, _NORMAL, 3 * s + 2 * d),
    ])
    # Double drag tap
    rudiments["double_drag_tap"] = DrumRudiment("double_drag_tap", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d),
        _ne(_R, _NORMAL, 2 * d),
        _ne(_L, _GHOST, s), _ne(_L, _GHOST, s + d),
        _ne(_R, _ACCENT, s + 2 * d), _ne(_R, _NORMAL, 2 * s + 2 * d),
        _ne(_R, _GHOST, 3 * s), _ne(_R, _GHOST, 3 * s + d),
        _ne(_L, _ACCENT, 3 * s + 2 * d),
    ])
    # Lesson 25
    rudiments["lesson_25"] = DrumRudiment("lesson_25", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d),
        _ne(_R, _ACCENT, 2 * d), _ne(_L, _NORMAL, s),
        _ne(_R, _GHOST, s + d), _ne(_R, _GHOST, s + 2 * d),
        _ne(_L, _ACCENT, s + 3 * d), _ne(_R, _NORMAL, 2 * s),
    ])
    # Single dragadiddle
    rudiments["single_dragadiddle"] = DrumRudiment("single_dragadiddle", [
        _ne(_R, _GHOST, 0), _ne(_R, _GHOST, d),
        _ne(_L, _ACCENT, 2 * d), _ne(_R, _NORMAL, s),
        _ne(_L, _NORMAL, s + d * 2), _ne(_L, _NORMAL, s + d * 3),
    ])
    # Drag paradiddle #1
    rudiments["drag_paradiddle_1"] = DrumRudiment("drag_paradiddle_1", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_L, _GHOST, 2 * s), _ne(_L, _GHOST, 2 * s + d),
        _ne(_R, _ACCENT, 2 * s + 2 * d), _ne(_R, _NORMAL, 3 * s),
        _ne(_L, _NORMAL, 3 * s + 2 * d), _ne(_L, _NORMAL, 4 * s),
    ])
    # Drag paradiddle #2
    rudiments["drag_paradiddle_2"] = DrumRudiment("drag_paradiddle_2", [
        _ne(_R, _ACCENT, 0), _ne(_L, _NORMAL, s),
        _ne(_R, _NORMAL, 2 * s),
        _ne(_L, _GHOST, 3 * s), _ne(_L, _GHOST, 3 * s + d),
        _ne(_R, _ACCENT, 3 * s + 2 * d), _ne(_R, _NORMAL, 4 * s),
        _ne(_L, _NORMAL, 4 * s + 2 * d), _ne(_L, _NORMAL, 5 * s),
    ])
    # Single ratamacue
    rudiments["single_ratamacue"] = DrumRudiment("single_ratamacue", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d), _ne(_L, _GHOST, 2 * d),
        _ne(_R, _ACCENT, 3 * d), _ne(_L, _NORMAL, s), _ne(_R, _NORMAL, s + 3 * d),
    ])
    # Double ratamacue
    rudiments["double_ratamacue"] = DrumRudiment("double_ratamacue", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d), _ne(_L, _GHOST, 2 * d),
        _ne(_R, _NORMAL, 3 * d),
        _ne(_R, _GHOST, s), _ne(_R, _GHOST, s + d), _ne(_R, _GHOST, s + 2 * d),
        _ne(_L, _ACCENT, s + 3 * d), _ne(_R, _NORMAL, 2 * s), _ne(_L, _NORMAL, 2 * s + 3 * d),
    ])
    # Triple ratamacue
    rudiments["triple_ratamacue"] = DrumRudiment("triple_ratamacue", [
        _ne(_L, _GHOST, 0), _ne(_L, _GHOST, d), _ne(_L, _GHOST, 2 * d),
        _ne(_R, _NORMAL, 3 * d),
        _ne(_R, _GHOST, s), _ne(_R, _GHOST, s + d), _ne(_R, _GHOST, s + 2 * d),
        _ne(_L, _NORMAL, s + 3 * d),
        _ne(_L, _GHOST, 2 * s), _ne(_L, _GHOST, 2 * s + d), _ne(_L, _GHOST, 2 * s + 2 * d),
        _ne(_R, _ACCENT, 2 * s + 3 * d), _ne(_L, _NORMAL, 3 * s), _ne(_R, _NORMAL, 3 * s + 3 * d),
    ])

    return rudiments


# Module-level rudiment registry (built once at import time)
DRUM_RUDIMENTS: dict[str, DrumRudiment] = _build_rudiments()


# ---------------------------------------------------------------------------
# BassPattern — pre-built repeating bass line fragments
# ---------------------------------------------------------------------------

class BassPattern:
    """A single-bar bass pattern (relative to chord root)."""

    def __init__(self, name: str, genre: Genre, beats: list[dict]):
        """
        beats: list of dicts with keys:
          beat (float, 1-indexed), interval (int semitones from root),
          velocity (int), duration_beats (float)
        """
        self.name = name
        self.genre = genre
        self.beats = beats

    def to_events(
        self, root_midi: int, tpb: int, bar_offset_ticks: int, intensity: float = 1.0
    ) -> list[NoteEvent]:
        """Render this pattern starting at bar_offset_ticks."""
        events: list[NoteEvent] = []
        vel_scale = max(0.3, min(1.0, intensity))
        for beat_def in self.beats:
            tick = bar_offset_ticks + int((beat_def["beat"] - 1.0) * tpb)
            pitch = max(0, min(127, root_midi + beat_def["interval"]))
            vel = max(1, min(127, int(beat_def["velocity"] * vel_scale)))
            dur = int(beat_def["duration_beats"] * tpb)
            events.append(NoteEvent(
                pitch=pitch, velocity=vel,
                start_tick=tick, duration_ticks=max(1, dur),
                channel=1,
            ))
        return events


BASS_PATTERNS: dict[str, BassPattern] = {
    "jazz_walking": BassPattern("jazz_walking", Genre.JAZZ, [
        {"beat": 1.0, "interval": 0, "velocity": 90, "duration_beats": 1.0},
        {"beat": 2.0, "interval": 7, "velocity": 85, "duration_beats": 1.0},
        {"beat": 3.0, "interval": 12, "velocity": 90, "duration_beats": 1.0},
        {"beat": 4.0, "interval": 10, "velocity": 85, "duration_beats": 1.0},
    ]),
    "funk_slap": BassPattern("funk_slap", Genre.FUNK, [
        {"beat": 1.0, "interval": 0, "velocity": 110, "duration_beats": 0.25},
        {"beat": 1.5, "interval": 0, "velocity": 70, "duration_beats": 0.25},
        {"beat": 1.75, "interval": 12, "velocity": 95, "duration_beats": 0.25},
        {"beat": 2.25, "interval": 0, "velocity": 100, "duration_beats": 0.25},
        {"beat": 3.0, "interval": 0, "velocity": 110, "duration_beats": 0.25},
        {"beat": 3.5, "interval": 7, "velocity": 75, "duration_beats": 0.25},
        {"beat": 4.0, "interval": 0, "velocity": 95, "duration_beats": 0.25},
        {"beat": 4.75, "interval": 2, "velocity": 80, "duration_beats": 0.25},
    ]),
    "reggae_skank": BassPattern("reggae_skank", Genre.REGGAE, [
        {"beat": 1.0, "interval": 0, "velocity": 95, "duration_beats": 0.5},
        {"beat": 3.0, "interval": 0, "velocity": 90, "duration_beats": 0.5},
        {"beat": 3.5, "interval": 7, "velocity": 80, "duration_beats": 0.5},
    ]),
    "rnb_two_feel": BassPattern("rnb_two_feel", Genre.RNB, [
        {"beat": 1.0, "interval": 0, "velocity": 95, "duration_beats": 1.5},
        {"beat": 3.0, "interval": 0, "velocity": 90, "duration_beats": 1.5},
    ]),
    "pop_root_fifth": BassPattern("pop_root_fifth", Genre.POP, [
        {"beat": 1.0, "interval": 0, "velocity": 95, "duration_beats": 1.0},
        {"beat": 2.0, "interval": 7, "velocity": 85, "duration_beats": 1.0},
        {"beat": 3.0, "interval": 0, "velocity": 90, "duration_beats": 1.0},
        {"beat": 4.0, "interval": 7, "velocity": 85, "duration_beats": 1.0},
    ]),
    "latin_tumbao": BassPattern("latin_tumbao", Genre.LATIN, [
        {"beat": 1.0, "interval": 0, "velocity": 95, "duration_beats": 0.5},
        {"beat": 2.5, "interval": 0, "velocity": 90, "duration_beats": 0.5},
        {"beat": 3.0, "interval": 7, "velocity": 85, "duration_beats": 0.5},
        {"beat": 4.5, "interval": 0, "velocity": 90, "duration_beats": 0.5},
    ]),
    "motown_bass_line": BassPattern("motown_bass_line", Genre.SOUL, [
        {"beat": 1.0, "interval": 0, "velocity": 100, "duration_beats": 0.5},
        {"beat": 1.5, "interval": 7, "velocity": 85, "duration_beats": 0.5},
        {"beat": 2.0, "interval": 12, "velocity": 90, "duration_beats": 0.5},
        {"beat": 2.5, "interval": 7, "velocity": 80, "duration_beats": 0.5},
        {"beat": 3.0, "interval": 0, "velocity": 100, "duration_beats": 0.5},
        {"beat": 3.5, "interval": 7, "velocity": 85, "duration_beats": 0.5},
        {"beat": 4.0, "interval": 5, "velocity": 90, "duration_beats": 0.5},
        {"beat": 4.5, "interval": 2, "velocity": 85, "duration_beats": 0.5},
    ]),
    "country_boom_chick": BassPattern("country_boom_chick", Genre.COUNTRY, [
        {"beat": 1.0, "interval": 0, "velocity": 100, "duration_beats": 1.0},
        {"beat": 3.0, "interval": 7, "velocity": 90, "duration_beats": 1.0},
    ]),
}


# ---------------------------------------------------------------------------
# MelodicPattern — chord-tone / arpeggio patterns for guitar & keys
# ---------------------------------------------------------------------------

class MelodicPattern:
    """A pattern of chord-tone events relative to a chord's MIDI notes."""

    def __init__(self, name: str, genre: Genre, steps: list[dict]):
        """
        steps: list of dicts:
          index (int — chord tone index, 0-based),
          beat (float, 1-indexed),
          velocity (int),
          duration_beats (float),
          octave_offset (int, default 0)
        """
        self.name = name
        self.genre = genre
        self.steps = steps

    def to_events(
        self,
        chord_pitches: list[int],
        tpb: int,
        bar_offset_ticks: int,
        channel: int = 3,
        intensity: float = 1.0,
    ) -> list[NoteEvent]:
        vel_scale = max(0.3, min(1.0, intensity))
        events: list[NoteEvent] = []
        n = len(chord_pitches)
        for step in self.steps:
            idx = step["index"] % n
            pitch = chord_pitches[idx] + step.get("octave_offset", 0) * 12
            pitch = max(0, min(127, pitch))
            tick = bar_offset_ticks + int((step["beat"] - 1.0) * tpb)
            vel = max(1, min(127, int(step["velocity"] * vel_scale)))
            dur = int(step["duration_beats"] * tpb)
            events.append(NoteEvent(
                pitch=pitch, velocity=vel,
                start_tick=tick, duration_ticks=max(1, dur),
                channel=channel,
            ))
        return events


MELODIC_PATTERNS: dict[str, MelodicPattern] = {
    "jazz_chord_shell": MelodicPattern("jazz_chord_shell", Genre.JAZZ, [
        # Shell voicing: 3rd + 7th only
        {"index": 1, "beat": 1.0, "velocity": 75, "duration_beats": 2.0},
        {"index": 3, "beat": 1.0, "velocity": 70, "duration_beats": 2.0},
        {"index": 1, "beat": 3.0, "velocity": 70, "duration_beats": 2.0},
        {"index": 3, "beat": 3.0, "velocity": 65, "duration_beats": 2.0},
    ]),
    "jazz_chord_full": MelodicPattern("jazz_chord_full", Genre.JAZZ, [
        {"index": 0, "beat": 1.0, "velocity": 75, "duration_beats": 4.0},
        {"index": 1, "beat": 1.0, "velocity": 70, "duration_beats": 4.0},
        {"index": 2, "beat": 1.0, "velocity": 70, "duration_beats": 4.0},
        {"index": 3, "beat": 1.0, "velocity": 65, "duration_beats": 4.0},
    ]),
    "guitar_arpeggio_up": MelodicPattern("guitar_arpeggio_up", Genre.FOLK, [
        {"index": 0, "beat": 1.0, "velocity": 80, "duration_beats": 0.5},
        {"index": 1, "beat": 1.5, "velocity": 75, "duration_beats": 0.5},
        {"index": 2, "beat": 2.0, "velocity": 78, "duration_beats": 0.5},
        {"index": 0, "beat": 2.5, "velocity": 73, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 1, "beat": 3.0, "velocity": 80, "duration_beats": 0.5},
        {"index": 2, "beat": 3.5, "velocity": 75, "duration_beats": 0.5},
        {"index": 0, "beat": 4.0, "velocity": 78, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 1, "beat": 4.5, "velocity": 73, "duration_beats": 0.5, "octave_offset": 1},
    ]),
    "guitar_arpeggio_down": MelodicPattern("guitar_arpeggio_down", Genre.FOLK, [
        {"index": 2, "beat": 1.0, "velocity": 80, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 1, "beat": 1.5, "velocity": 75, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 0, "beat": 2.0, "velocity": 78, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 2, "beat": 2.5, "velocity": 73, "duration_beats": 0.5},
        {"index": 1, "beat": 3.0, "velocity": 80, "duration_beats": 0.5},
        {"index": 0, "beat": 3.5, "velocity": 75, "duration_beats": 0.5},
        {"index": 2, "beat": 4.0, "velocity": 78, "duration_beats": 0.5},
        {"index": 1, "beat": 4.5, "velocity": 73, "duration_beats": 0.5},
    ]),
    "guitar_travis_picking": MelodicPattern("guitar_travis_picking", Genre.COUNTRY, [
        # Alternating bass / treble fingerpicking pattern
        {"index": 0, "beat": 1.0, "velocity": 85, "duration_beats": 0.5},
        {"index": 2, "beat": 1.5, "velocity": 70, "duration_beats": 0.25},
        {"index": 1, "beat": 1.75, "velocity": 65, "duration_beats": 0.25},
        {"index": 0, "beat": 2.0, "velocity": 80, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 2, "beat": 2.5, "velocity": 68, "duration_beats": 0.25},
        {"index": 1, "beat": 2.75, "velocity": 65, "duration_beats": 0.25},
        {"index": 0, "beat": 3.0, "velocity": 85, "duration_beats": 0.5},
        {"index": 2, "beat": 3.5, "velocity": 70, "duration_beats": 0.25},
        {"index": 1, "beat": 3.75, "velocity": 65, "duration_beats": 0.25},
        {"index": 0, "beat": 4.0, "velocity": 80, "duration_beats": 0.5, "octave_offset": 1},
        {"index": 2, "beat": 4.5, "velocity": 68, "duration_beats": 0.25},
        {"index": 1, "beat": 4.75, "velocity": 65, "duration_beats": 0.25},
    ]),
    "guitar_bossa_comp": MelodicPattern("guitar_bossa_comp", Genre.BOSSA_NOVA, [
        {"index": 0, "beat": 1.0, "velocity": 75, "duration_beats": 0.5},
        {"index": 1, "beat": 1.0, "velocity": 70, "duration_beats": 0.5},
        {"index": 2, "beat": 1.0, "velocity": 70, "duration_beats": 0.5},
        {"index": 0, "beat": 1.75, "velocity": 65, "duration_beats": 0.25},
        {"index": 1, "beat": 1.75, "velocity": 60, "duration_beats": 0.25},
        {"index": 2, "beat": 2.5, "velocity": 70, "duration_beats": 0.5},
        {"index": 0, "beat": 3.25, "velocity": 68, "duration_beats": 0.25},
        {"index": 1, "beat": 3.25, "velocity": 63, "duration_beats": 0.25},
        {"index": 0, "beat": 4.0, "velocity": 72, "duration_beats": 0.5},
        {"index": 2, "beat": 4.0, "velocity": 68, "duration_beats": 0.5},
    ]),
    "funk_rhythm_guitar_16th": MelodicPattern("funk_rhythm_guitar_16th", Genre.FUNK, [
        # Tight 16th note chops with rests
        {"index": 0, "beat": 1.0, "velocity": 90, "duration_beats": 0.25},
        {"index": 0, "beat": 1.5, "velocity": 85, "duration_beats": 0.25},
        {"index": 0, "beat": 1.75, "velocity": 80, "duration_beats": 0.25},
        {"index": 0, "beat": 2.5, "velocity": 90, "duration_beats": 0.25},
        {"index": 0, "beat": 3.0, "velocity": 88, "duration_beats": 0.25},
        {"index": 0, "beat": 3.5, "velocity": 82, "duration_beats": 0.25},
        {"index": 0, "beat": 4.0, "velocity": 90, "duration_beats": 0.25},
        {"index": 0, "beat": 4.75, "velocity": 80, "duration_beats": 0.25},
    ]),
    "keys_stride_left_hand": MelodicPattern("keys_stride_left_hand", Genre.SWING, [
        # Stride: bass note on 1&3, chord on 2&4
        {"index": 0, "beat": 1.0, "velocity": 85, "duration_beats": 0.75, "octave_offset": -1},
        {"index": 1, "beat": 2.0, "velocity": 75, "duration_beats": 0.75},
        {"index": 2, "beat": 2.0, "velocity": 72, "duration_beats": 0.75},
        {"index": 0, "beat": 3.0, "velocity": 82, "duration_beats": 0.75, "octave_offset": -1},
        {"index": 1, "beat": 4.0, "velocity": 75, "duration_beats": 0.75},
        {"index": 2, "beat": 4.0, "velocity": 72, "duration_beats": 0.75},
    ]),
    "keys_jazz_two_handed": MelodicPattern("keys_jazz_two_handed", Genre.JAZZ, [
        # Left hand bass + right hand chord stabs
        {"index": 0, "beat": 1.0, "velocity": 80, "duration_beats": 1.0, "octave_offset": -1},
        {"index": 1, "beat": 1.67, "velocity": 72, "duration_beats": 0.5},
        {"index": 2, "beat": 1.67, "velocity": 70, "duration_beats": 0.5},
        {"index": 3, "beat": 1.67, "velocity": 68, "duration_beats": 0.5},
        {"index": 0, "beat": 3.0, "velocity": 78, "duration_beats": 1.0, "octave_offset": -1},
        {"index": 1, "beat": 3.67, "velocity": 70, "duration_beats": 0.5},
        {"index": 2, "beat": 3.67, "velocity": 68, "duration_beats": 0.5},
        {"index": 3, "beat": 3.67, "velocity": 65, "duration_beats": 0.5},
    ]),
    "keys_synth_arp": MelodicPattern("keys_synth_arp", Genre.ELECTRONIC, [
        {"index": 0, "beat": 1.0, "velocity": 85, "duration_beats": 0.25},
        {"index": 1, "beat": 1.25, "velocity": 80, "duration_beats": 0.25},
        {"index": 2, "beat": 1.5, "velocity": 83, "duration_beats": 0.25},
        {"index": 0, "beat": 1.75, "velocity": 78, "duration_beats": 0.25, "octave_offset": 1},
        {"index": 1, "beat": 2.0, "velocity": 85, "duration_beats": 0.25},
        {"index": 2, "beat": 2.25, "velocity": 80, "duration_beats": 0.25},
        {"index": 0, "beat": 2.5, "velocity": 83, "duration_beats": 0.25},
        {"index": 1, "beat": 2.75, "velocity": 78, "duration_beats": 0.25, "octave_offset": 1},
        {"index": 0, "beat": 3.0, "velocity": 85, "duration_beats": 0.25},
        {"index": 1, "beat": 3.25, "velocity": 80, "duration_beats": 0.25},
        {"index": 2, "beat": 3.5, "velocity": 83, "duration_beats": 0.25},
        {"index": 0, "beat": 3.75, "velocity": 78, "duration_beats": 0.25, "octave_offset": 1},
        {"index": 1, "beat": 4.0, "velocity": 85, "duration_beats": 0.25},
        {"index": 2, "beat": 4.25, "velocity": 80, "duration_beats": 0.25},
        {"index": 0, "beat": 4.5, "velocity": 83, "duration_beats": 0.25, "octave_offset": 1},
        {"index": 1, "beat": 4.75, "velocity": 78, "duration_beats": 0.25, "octave_offset": 1},
    ]),
}
