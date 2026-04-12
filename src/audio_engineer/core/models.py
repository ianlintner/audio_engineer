"""Pydantic v2 data models for the AI Music Studio."""

from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Genre(str, Enum):
    # --- Rock family ---
    CLASSIC_ROCK = "classic_rock"
    HARD_ROCK = "hard_rock"
    PUNK = "punk"
    INDIE_ROCK = "indie_rock"
    ALT_ROCK = "alt_rock"
    GRUNGE = "grunge"
    PROG_ROCK = "prog_rock"
    PSYCHEDELIC_ROCK = "psychedelic_rock"
    GARAGE_ROCK = "garage_rock"
    POST_ROCK = "post_rock"
    SURF_ROCK = "surf_rock"
    SOUTHERN_ROCK = "southern_rock"
    SOFT_ROCK = "soft_rock"
    # --- Metal family ---
    METAL = "metal"
    THRASH_METAL = "thrash_metal"
    DEATH_METAL = "death_metal"
    DOOM_METAL = "doom_metal"
    BLACK_METAL = "black_metal"
    POWER_METAL = "power_metal"
    PROGRESSIVE_METAL = "progressive_metal"
    NU_METAL = "nu_metal"
    METALCORE = "metalcore"
    # --- Pop / mainstream ---
    POP = "pop"
    SYNTH_POP = "synth_pop"
    INDIE_POP = "indie_pop"
    DREAM_POP = "dream_pop"
    K_POP = "k_pop"
    DISCO = "disco"
    NEW_WAVE = "new_wave"
    # --- Blues family ---
    BLUES = "blues"
    DELTA_BLUES = "delta_blues"
    CHICAGO_BLUES = "chicago_blues"
    # --- Jazz family ---
    JAZZ = "jazz"
    SWING = "swing"
    BEBOP = "bebop"
    COOL_JAZZ = "cool_jazz"
    FUSION = "fusion"
    SMOOTH_JAZZ = "smooth_jazz"
    FREE_JAZZ = "free_jazz"
    ACID_JAZZ = "acid_jazz"
    # --- Funk / Soul / R&B ---
    FUNK = "funk"
    SOUL = "soul"
    RNB = "rnb"
    NEO_SOUL = "neo_soul"
    MOTOWN = "motown"
    # --- Hip-hop family ---
    HIP_HOP = "hip_hop"
    TRAP = "trap"
    LO_FI_HIP_HOP = "lo_fi_hip_hop"
    BOOM_BAP = "boom_bap"
    # --- Electronic family ---
    ELECTRONIC = "electronic"
    HOUSE = "house"
    DEEP_HOUSE = "deep_house"
    TECH_HOUSE = "tech_house"
    TECHNO = "techno"
    TRANCE = "trance"
    DRUM_AND_BASS = "drum_and_bass"
    DUBSTEP = "dubstep"
    AMBIENT = "ambient"
    SYNTHWAVE = "synthwave"
    IDM = "idm"
    CHILLWAVE = "chillwave"
    DOWNTEMPO = "downtempo"
    GARAGE_ELECTRONIC = "garage_electronic"
    ELECTRO = "electro"
    # --- Country / folk / Americana ---
    COUNTRY = "country"
    FOLK = "folk"
    BLUEGRASS = "bluegrass"
    AMERICANA = "americana"
    CELTIC = "celtic"
    # --- Latin family ---
    LATIN = "latin"
    BOSSA_NOVA = "bossa_nova"
    SALSA = "salsa"
    SAMBA = "samba"
    REGGAETON = "reggaeton"
    CUMBIA = "cumbia"
    TANGO = "tango"
    # --- Caribbean ---
    REGGAE = "reggae"
    SKA = "ska"
    DUB = "dub"
    DANCEHALL = "dancehall"
    CALYPSO = "calypso"
    # --- African ---
    AFROBEAT = "afrobeat"
    HIGHLIFE = "highlife"
    # --- Other world ---
    FLAMENCO = "flamenco"
    MIDDLE_EASTERN = "middle_eastern"
    BOLLYWOOD = "bollywood"
    # --- Classical / orchestral ---
    CLASSICAL = "classical"
    BAROQUE = "baroque"
    ROMANTIC_ERA = "romantic_era"
    CINEMATIC = "cinematic"
    # --- Spiritual / worship ---
    GOSPEL = "gospel"
    WORSHIP = "worship"
    # --- Experimental ---
    NOISE = "noise"
    SHOEGAZE = "shoegaze"
    MATH_ROCK = "math_rock"
    EMO = "emo"
    POST_PUNK = "post_punk"
    INDUSTRIAL = "industrial"
    VAPORWAVE = "vaporwave"


class Instrument(str, Enum):
    DRUMS = "drums"
    BASS = "bass"
    ELECTRIC_GUITAR = "electric_guitar"
    ACOUSTIC_GUITAR = "acoustic_guitar"
    LEAD_GUITAR = "lead_guitar"
    KEYS = "keys"
    ORGAN = "organ"
    VOCALS = "vocals"
    STRINGS = "strings"
    VIOLIN = "violin"
    CELLO = "cello"
    VIOLA = "viola"
    CONTRABASS = "contrabass"
    HARP = "harp"
    BRASS = "brass"
    TRUMPET = "trumpet"
    TROMBONE = "trombone"
    FRENCH_HORN = "french_horn"
    TUBA = "tuba"
    WOODWINDS = "woodwinds"
    SAXOPHONE = "saxophone"
    FLUTE = "flute"
    CLARINET = "clarinet"
    OBOE = "oboe"
    SYNTHESIZER = "synthesizer"
    PAD = "pad"
    VIBRAPHONE = "vibraphone"
    MARIMBA = "marimba"
    PERCUSSION = "percussion"
    BANJO = "banjo"
    UKULELE = "ukulele"
    MANDOLIN = "mandolin"
    SITAR = "sitar"
    CONGA = "conga"
    BONGO = "bongo"
    DJEMBE = "djembe"
    HARMONICA = "harmonica"
    ACCORDION = "accordion"
    STEEL_DRUMS = "steel_drums"
    TABLA = "tabla"
    ERHU = "erhu"
    KOTO = "koto"
    KALIMBA = "kalimba"
    BAGPIPE = "bagpipe"
    FIDDLE = "fiddle"
    ELECTRIC_PIANO = "electric_piano"


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
    LYDIAN = "lydian"
    PHRYGIAN = "phrygian"
    LOCRIAN = "locrian"
    PENTATONIC_MAJOR = "pentatonic_major"
    PENTATONIC_MINOR = "pentatonic_minor"
    BLUES = "blues"
    HARMONIC_MINOR = "harmonic_minor"
    MELODIC_MINOR = "melodic_minor"
    WHOLE_TONE = "whole_tone"
    DIMINISHED = "diminished"
    BEBOP_DOMINANT = "bebop_dominant"
    BEBOP_MAJOR = "bebop_major"
    SPANISH_PHRYGIAN = "spanish_phrygian"
    HUNGARIAN_MINOR = "hungarian_minor"


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
    DIM7 = "dim7"
    HALF_DIM = "half_dim"
    MIN_MAJ7 = "min_maj7"
    DOM9 = "dom9"
    MAJ9 = "maj9"
    MIN9 = "min9"
    ADD9 = "add9"
    SHARP9 = "sharp9"
    ALT = "alt"
    DOM11 = "dom11"
    DOM13 = "dom13"
    SIXTH = "6th"
    MIN6 = "min6"
    QUARTAL = "quartal"


class SessionStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    GENERATING = "generating"
    MIXING = "mixing"
    COMPLETE = "complete"
    ERROR = "error"


class TrackType(str, Enum):
    """Type of audio track data."""
    MIDI = "midi"
    AUDIO = "audio"


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
    mp3_bitrate: str = Field(default="192k")
    normalize: bool = True


class GenreBlend(BaseModel):
    """Describes a blend of multiple genres with relative weights.

    The primary genre (highest weight) drives the overall feel while
    secondary genres influence chord choices, rhythm patterns, and
    instrument selection proportionally.
    """
    genres: list[Genre] = Field(min_length=1, max_length=4)
    weights: list[float] = Field(
        default_factory=list,
        description="Relative weights for each genre; normalised internally.",
    )

    @model_validator(mode="after")
    def _validate_weights(self) -> "GenreBlend":
        if self.weights:
            if len(self.weights) != len(self.genres):
                raise ValueError(
                    f"weights length ({len(self.weights)}) must match "
                    f"genres length ({len(self.genres)})"
                )
            if any(w < 0 for w in self.weights):
                raise ValueError("All weights must be non-negative")
        return self

    @property
    def primary(self) -> Genre:
        """Return the genre with the highest weight."""
        if not self.weights:
            return self.genres[0]
        return self.genres[self.weights.index(max(self.weights))]

    @property
    def normalised_weights(self) -> list[float]:
        if not self.weights:
            n = len(self.genres)
            return [1.0 / n] * n
        total = sum(self.weights)
        if total == 0:
            n = len(self.genres)
            return [1.0 / n] * n
        return [w / total for w in self.weights]


class Session(BaseModel):
    id: str
    status: SessionStatus = SessionStatus.CREATED
    config: SessionConfig = Field(default_factory=SessionConfig)
    tracks: dict[str, MidiTrackData] = Field(default_factory=dict)
    mix: MixConfig = Field(default_factory=MixConfig)
    output_files: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Genre alias / synonym resolver
# ---------------------------------------------------------------------------

# Maps informal, colloquial, or abbreviated terms to a canonical Genre value.
# All keys are lower-cased; lookup should also lower-case the query.
GENRE_ALIASES: dict[str, Genre] = {
    # Rock family
    "rock": Genre.CLASSIC_ROCK,
    "rock and roll": Genre.CLASSIC_ROCK,
    "rock n roll": Genre.CLASSIC_ROCK,
    "rock & roll": Genre.CLASSIC_ROCK,
    "classic rock": Genre.CLASSIC_ROCK,
    "hard rock": Genre.HARD_ROCK,
    "punk": Genre.PUNK,
    "punk rock": Genre.PUNK,
    "pop punk": Genre.PUNK,
    "indie": Genre.INDIE_ROCK,
    "indie rock": Genre.INDIE_ROCK,
    "alternative": Genre.ALT_ROCK,
    "alternative rock": Genre.ALT_ROCK,
    "alt rock": Genre.ALT_ROCK,
    "grunge": Genre.GRUNGE,
    "progressive rock": Genre.PROG_ROCK,
    "prog rock": Genre.PROG_ROCK,
    "prog": Genre.PROG_ROCK,
    "psychedelic": Genre.PSYCHEDELIC_ROCK,
    "psychedelic rock": Genre.PSYCHEDELIC_ROCK,
    "psych rock": Genre.PSYCHEDELIC_ROCK,
    "garage rock": Genre.GARAGE_ROCK,
    "garage": Genre.GARAGE_ROCK,
    "post-rock": Genre.POST_ROCK,
    "post rock": Genre.POST_ROCK,
    "surf": Genre.SURF_ROCK,
    "surf rock": Genre.SURF_ROCK,
    "southern rock": Genre.SOUTHERN_ROCK,
    "soft rock": Genre.SOFT_ROCK,
    "yacht rock": Genre.SOFT_ROCK,
    # Metal family
    "metal": Genre.METAL,
    "heavy metal": Genre.METAL,
    "thrash": Genre.THRASH_METAL,
    "thrash metal": Genre.THRASH_METAL,
    "death metal": Genre.DEATH_METAL,
    "doom metal": Genre.DOOM_METAL,
    "doom": Genre.DOOM_METAL,
    "stoner metal": Genre.DOOM_METAL,
    "black metal": Genre.BLACK_METAL,
    "power metal": Genre.POWER_METAL,
    "progressive metal": Genre.PROGRESSIVE_METAL,
    "prog metal": Genre.PROGRESSIVE_METAL,
    "djent": Genre.PROGRESSIVE_METAL,
    "nu metal": Genre.NU_METAL,
    "nu-metal": Genre.NU_METAL,
    "metalcore": Genre.METALCORE,
    # Pop / mainstream
    "pop": Genre.POP,
    "pop music": Genre.POP,
    "synth pop": Genre.SYNTH_POP,
    "synthpop": Genre.SYNTH_POP,
    "electropop": Genre.SYNTH_POP,
    "indie pop": Genre.INDIE_POP,
    "dream pop": Genre.DREAM_POP,
    "shoegaze": Genre.SHOEGAZE,
    "k-pop": Genre.K_POP,
    "kpop": Genre.K_POP,
    "k pop": Genre.K_POP,
    "disco": Genre.DISCO,
    "new wave": Genre.NEW_WAVE,
    "new-wave": Genre.NEW_WAVE,
    # Blues
    "blues": Genre.BLUES,
    "delta blues": Genre.DELTA_BLUES,
    "chicago blues": Genre.CHICAGO_BLUES,
    "electric blues": Genre.CHICAGO_BLUES,
    # Jazz
    "jazz": Genre.JAZZ,
    "swing": Genre.SWING,
    "big band": Genre.SWING,
    "bebop": Genre.BEBOP,
    "bop": Genre.BEBOP,
    "cool jazz": Genre.COOL_JAZZ,
    "west coast jazz": Genre.COOL_JAZZ,
    "fusion": Genre.FUSION,
    "jazz fusion": Genre.FUSION,
    "jazz rock": Genre.FUSION,
    "smooth jazz": Genre.SMOOTH_JAZZ,
    "free jazz": Genre.FREE_JAZZ,
    "avant-garde jazz": Genre.FREE_JAZZ,
    "acid jazz": Genre.ACID_JAZZ,
    # Funk / Soul / R&B
    "funk": Genre.FUNK,
    "soul": Genre.SOUL,
    "r&b": Genre.RNB,
    "rnb": Genre.RNB,
    "r and b": Genre.RNB,
    "rhythm and blues": Genre.RNB,
    "neo soul": Genre.NEO_SOUL,
    "neo-soul": Genre.NEO_SOUL,
    "motown": Genre.MOTOWN,
    # Hip-hop
    "hip hop": Genre.HIP_HOP,
    "hip-hop": Genre.HIP_HOP,
    "hiphop": Genre.HIP_HOP,
    "rap": Genre.HIP_HOP,
    "trap": Genre.TRAP,
    "trap music": Genre.TRAP,
    "lo-fi": Genre.LO_FI_HIP_HOP,
    "lo fi": Genre.LO_FI_HIP_HOP,
    "lofi": Genre.LO_FI_HIP_HOP,
    "lo-fi hip hop": Genre.LO_FI_HIP_HOP,
    "lofi hip hop": Genre.LO_FI_HIP_HOP,
    "chillhop": Genre.LO_FI_HIP_HOP,
    "boom bap": Genre.BOOM_BAP,
    "boom-bap": Genre.BOOM_BAP,
    "old school hip hop": Genre.BOOM_BAP,
    # Electronic
    "electronic": Genre.ELECTRONIC,
    "edm": Genre.ELECTRONIC,
    "house": Genre.HOUSE,
    "house music": Genre.HOUSE,
    "deep house": Genre.DEEP_HOUSE,
    "tech house": Genre.TECH_HOUSE,
    "techno": Genre.TECHNO,
    "trance": Genre.TRANCE,
    "psytrance": Genre.TRANCE,
    "drum and bass": Genre.DRUM_AND_BASS,
    "drum n bass": Genre.DRUM_AND_BASS,
    "dnb": Genre.DRUM_AND_BASS,
    "d&b": Genre.DRUM_AND_BASS,
    "jungle": Genre.DRUM_AND_BASS,
    "dubstep": Genre.DUBSTEP,
    "brostep": Genre.DUBSTEP,
    "ambient": Genre.AMBIENT,
    "ambient music": Genre.AMBIENT,
    "synthwave": Genre.SYNTHWAVE,
    "retrowave": Genre.SYNTHWAVE,
    "outrun": Genre.SYNTHWAVE,
    "idm": Genre.IDM,
    "intelligent dance music": Genre.IDM,
    "chillwave": Genre.CHILLWAVE,
    "downtempo": Genre.DOWNTEMPO,
    "trip hop": Genre.DOWNTEMPO,
    "trip-hop": Genre.DOWNTEMPO,
    "uk garage": Genre.GARAGE_ELECTRONIC,
    "2 step": Genre.GARAGE_ELECTRONIC,
    "electro": Genre.ELECTRO,
    "vaporwave": Genre.VAPORWAVE,
    # Country / folk
    "country": Genre.COUNTRY,
    "country music": Genre.COUNTRY,
    "folk": Genre.FOLK,
    "folk music": Genre.FOLK,
    "singer-songwriter": Genre.FOLK,
    "bluegrass": Genre.BLUEGRASS,
    "americana": Genre.AMERICANA,
    "roots": Genre.AMERICANA,
    "celtic": Genre.CELTIC,
    "irish": Genre.CELTIC,
    "scottish": Genre.CELTIC,
    # Latin
    "latin": Genre.LATIN,
    "bossa nova": Genre.BOSSA_NOVA,
    "bossa": Genre.BOSSA_NOVA,
    "salsa": Genre.SALSA,
    "samba": Genre.SAMBA,
    "reggaeton": Genre.REGGAETON,
    "perreo": Genre.REGGAETON,
    "cumbia": Genre.CUMBIA,
    "tango": Genre.TANGO,
    # Caribbean
    "reggae": Genre.REGGAE,
    "roots reggae": Genre.REGGAE,
    "ska": Genre.SKA,
    "ska punk": Genre.SKA,
    "dub": Genre.DUB,
    "dancehall": Genre.DANCEHALL,
    "calypso": Genre.CALYPSO,
    "soca": Genre.CALYPSO,
    # African
    "afrobeat": Genre.AFROBEAT,
    "afrobeats": Genre.AFROBEAT,
    "highlife": Genre.HIGHLIFE,
    # Other world
    "flamenco": Genre.FLAMENCO,
    "middle eastern": Genre.MIDDLE_EASTERN,
    "arabic": Genre.MIDDLE_EASTERN,
    "bollywood": Genre.BOLLYWOOD,
    "indian": Genre.BOLLYWOOD,
    # Classical
    "classical": Genre.CLASSICAL,
    "orchestral": Genre.CLASSICAL,
    "baroque": Genre.BAROQUE,
    "romantic": Genre.ROMANTIC_ERA,
    "romantic era": Genre.ROMANTIC_ERA,
    "cinematic": Genre.CINEMATIC,
    "film score": Genre.CINEMATIC,
    "soundtrack": Genre.CINEMATIC,
    "epic": Genre.CINEMATIC,
    # Spiritual
    "gospel": Genre.GOSPEL,
    "worship": Genre.WORSHIP,
    "praise": Genre.WORSHIP,
    "christian": Genre.WORSHIP,
    # Experimental / other
    "noise": Genre.NOISE,
    "noise rock": Genre.NOISE,
    "math rock": Genre.MATH_ROCK,
    "math-rock": Genre.MATH_ROCK,
    "emo": Genre.EMO,
    "emo rock": Genre.EMO,
    "screamo": Genre.EMO,
    "post-punk": Genre.POST_PUNK,
    "post punk": Genre.POST_PUNK,
    "industrial": Genre.INDUSTRIAL,
    "ebm": Genre.INDUSTRIAL,
    "industrial metal": Genre.INDUSTRIAL,
}


def resolve_genre(text: str) -> Genre | None:
    """Resolve a free-form genre string to a canonical Genre.

    Checks the alias table first, then attempts a direct Enum match.
    Returns ``None`` when no match is found.
    """
    key = text.strip().lower().replace("-", " ").replace("_", " ")
    # Exact alias
    if key in GENRE_ALIASES:
        return GENRE_ALIASES[key]
    # Try underscored version against enum values
    enum_key = key.replace(" ", "_")
    try:
        return Genre(enum_key)
    except ValueError:
        pass
    return None
