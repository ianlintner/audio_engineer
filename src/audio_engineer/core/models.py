"""Pydantic v2 data models for the AI Music Studio."""

from enum import Enum
from pydantic import BaseModel, Field


class Genre(str, Enum):
    CLASSIC_ROCK = "classic_rock"
    BLUES = "blues"
    POP = "pop"
    FOLK = "folk"
    COUNTRY = "country"
    PUNK = "punk"
    HARD_ROCK = "hard_rock"


class Instrument(str, Enum):
    DRUMS = "drums"
    BASS = "bass"
    ELECTRIC_GUITAR = "electric_guitar"
    ACOUSTIC_GUITAR = "acoustic_guitar"
    KEYS = "keys"
    VOCALS = "vocals"


class NoteName(str, Enum):
    C = "C"
    CS = "C#"
    D = "D"
    DS = "D#"
    E = "E"
    F = "F"
    FS = "F#"
    G = "G"
    GS = "G#"
    A = "A"
    AS = "A#"
    B = "B"


class Mode(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    DORIAN = "dorian"
    MIXOLYDIAN = "mixolydian"
    PENTATONIC_MAJOR = "pentatonic_major"
    PENTATONIC_MINOR = "pentatonic_minor"
    BLUES = "blues"


class ChordQuality(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    DOM7 = "dom7"
    MAJ7 = "maj7"
    MIN7 = "min7"
    DIM = "dim"
    AUG = "aug"
    SUS2 = "sus2"
    SUS4 = "sus4"
    POWER = "power"


class SessionStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    GENERATING = "generating"
    MIXING = "mixing"
    COMPLETE = "complete"
    ERROR = "error"


class KeySignature(BaseModel):
    root: NoteName = NoteName.C
    mode: Mode = Mode.MAJOR


class TimeSignature(BaseModel):
    numerator: int = Field(default=4, ge=1, le=16)
    denominator: int = Field(default=4, ge=1, le=16)


class SectionDef(BaseModel):
    name: str
    bars: int = Field(ge=1, le=64)
    repeats: int = Field(default=1, ge=1)
    intensity: float = Field(default=0.7, ge=0.0, le=1.0)


class NoteEvent(BaseModel):
    pitch: int = Field(ge=0, le=127)
    velocity: int = Field(default=100, ge=0, le=127)
    start_tick: int = Field(ge=0)
    duration_ticks: int = Field(gt=0)
    channel: int = Field(default=0, ge=0, le=15)


class MidiTrackData(BaseModel):
    name: str
    instrument: Instrument
    channel: int = Field(ge=0, le=15)
    events: list[NoteEvent] = Field(default_factory=list)
    program: int = Field(default=0, ge=0, le=127)


class BandMemberConfig(BaseModel):
    instrument: Instrument
    enabled: bool = True
    style_hints: list[str] = Field(default_factory=list)


class BandConfig(BaseModel):
    members: list[BandMemberConfig] = Field(default_factory=lambda: [
        BandMemberConfig(instrument=Instrument.DRUMS),
        BandMemberConfig(instrument=Instrument.BASS),
        BandMemberConfig(instrument=Instrument.ELECTRIC_GUITAR),
    ])


class SessionConfig(BaseModel):
    genre: Genre = Genre.CLASSIC_ROCK
    tempo: int = Field(default=120, ge=40, le=300)
    key: KeySignature = Field(default_factory=KeySignature)
    time_signature: TimeSignature = Field(default_factory=TimeSignature)
    structure: list[SectionDef] = Field(default_factory=lambda: [
        SectionDef(name="intro", bars=4, intensity=0.5),
        SectionDef(name="verse", bars=8, intensity=0.6),
        SectionDef(name="chorus", bars=8, intensity=0.9),
        SectionDef(name="verse", bars=8, intensity=0.7),
        SectionDef(name="chorus", bars=8, intensity=1.0),
        SectionDef(name="outro", bars=4, intensity=0.4),
    ])
    band: BandConfig = Field(default_factory=BandConfig)


class EQBand(BaseModel):
    frequency: float = Field(ge=20, le=20000)
    gain_db: float = Field(ge=-24, le=24)
    q: float = Field(default=1.0, ge=0.1, le=20)


class EffectConfig(BaseModel):
    effect_type: str
    parameters: dict[str, float] = Field(default_factory=dict)


class MixTrackConfig(BaseModel):
    instrument: Instrument
    volume: float = Field(default=0.8, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    eq_bands: list[EQBand] = Field(default_factory=list)
    effects: list[EffectConfig] = Field(default_factory=list)
    mute: bool = False
    solo: bool = False


class MixConfig(BaseModel):
    tracks: list[MixTrackConfig] = Field(default_factory=list)
    master_volume: float = Field(default=0.9, ge=0.0, le=1.0)


class RenderConfig(BaseModel):
    sample_rate: int = Field(default=44100, ge=22050, le=96000)
    format: str = Field(default="wav")
    normalize: bool = True


class Session(BaseModel):
    id: str
    status: SessionStatus = SessionStatus.CREATED
    config: SessionConfig = Field(default_factory=SessionConfig)
    tracks: dict[str, MidiTrackData] = Field(default_factory=dict)
    mix: MixConfig = Field(default_factory=MixConfig)
    output_files: list[str] = Field(default_factory=list)
