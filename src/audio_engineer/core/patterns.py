"""Pattern Repository - Pre-built drum and bass patterns."""

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
