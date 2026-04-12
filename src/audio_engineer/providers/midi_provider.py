"""Provider that wraps the existing MIDI engine and musician agents."""
from __future__ import annotations

import logging
from typing import Any, Optional

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.models import (
    Genre,
    Instrument,
    KeySignature,
    Mode,
    NoteName,
    SessionConfig,
    BandConfig,
    BandMemberConfig,
)
from audio_engineer.core.music_theory import ChordProgression, ProgressionFactory
from audio_engineer.agents.base import BaseMusician, SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent
from audio_engineer.agents.musician.bassist import BassistAgent
from audio_engineer.agents.musician.guitarist import GuitaristAgent
from audio_engineer.agents.musician.keyboardist import KeyboardistAgent
from audio_engineer.agents.musician.strings import StringsAgent
from audio_engineer.agents.musician.brass import BrassAgent
from audio_engineer.agents.musician.synth import SynthAgent
from audio_engineer.agents.musician.percussion import PercussionAgent
from audio_engineer.agents.musician.lead_guitar import LeadGuitarAgent
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Map instrument name → (agent class, Instrument enum value to inject, or None to use agent default)
_INSTRUMENT_AGENTS: dict[str, tuple[type[BaseMusician], Instrument | None]] = {
    "drums": (DrummerAgent, None),
    "bass": (BassistAgent, None),
    "electric_guitar": (GuitaristAgent, None),
    # NOTE: GuitaristAgent currently hardcodes Instrument.ELECTRIC_GUITAR;
    # acoustic guitar timbres are not yet differentiated at the MIDI level.
    "acoustic_guitar": (GuitaristAgent, None),
    "lead_guitar": (LeadGuitarAgent, None),
    "keys": (KeyboardistAgent, None),
    "organ": (KeyboardistAgent, Instrument.ORGAN),
    "strings": (StringsAgent, None),
    "violin": (StringsAgent, Instrument.VIOLIN),
    "cello": (StringsAgent, Instrument.CELLO),
    "viola": (StringsAgent, Instrument.VIOLA),
    "contrabass": (StringsAgent, Instrument.CONTRABASS),
    "harp": (KeyboardistAgent, Instrument.HARP),
    "brass": (BrassAgent, None),
    "trumpet": (BrassAgent, Instrument.TRUMPET),
    "trombone": (BrassAgent, Instrument.TROMBONE),
    "french_horn": (BrassAgent, Instrument.FRENCH_HORN),
    "tuba": (BrassAgent, Instrument.TUBA),
    "saxophone": (BrassAgent, Instrument.SAXOPHONE),
    "woodwinds": (BrassAgent, Instrument.WOODWINDS),
    "flute": (BrassAgent, Instrument.FLUTE),
    "clarinet": (BrassAgent, Instrument.CLARINET),
    "oboe": (BrassAgent, Instrument.OBOE),
    "synthesizer": (SynthAgent, Instrument.SYNTHESIZER),
    "pad": (SynthAgent, Instrument.PAD),
    "vibraphone": (KeyboardistAgent, Instrument.VIBRAPHONE),
    "marimba": (KeyboardistAgent, Instrument.MARIMBA),
    "percussion": (PercussionAgent, None),
    "conga": (PercussionAgent, Instrument.CONGA),
    "bongo": (PercussionAgent, Instrument.BONGO),
    "djembe": (PercussionAgent, Instrument.DJEMBE),
    "tabla": (PercussionAgent, Instrument.TABLA),
    "banjo": (GuitaristAgent, None),
    "ukulele": (GuitaristAgent, None),
    "mandolin": (GuitaristAgent, None),
    "sitar": (KeyboardistAgent, Instrument.SITAR),
    "harmonica": (BrassAgent, Instrument.HARMONICA),
    "accordion": (KeyboardistAgent, Instrument.ACCORDION),
    "steel_drums": (PercussionAgent, Instrument.STEEL_DRUMS),
    "erhu": (StringsAgent, Instrument.ERHU),
    "koto": (KeyboardistAgent, Instrument.KOTO),
    "kalimba": (KeyboardistAgent, Instrument.KALIMBA),
    "bagpipe": (BrassAgent, Instrument.BAGPIPE),
    "fiddle": (StringsAgent, Instrument.FIDDLE),
    "electric_piano": (KeyboardistAgent, Instrument.ELECTRIC_PIANO),
}


class MidiProvider(AudioProvider):
    """Generates MIDI tracks using the built-in musician agents.

    This wraps the existing agent system as a pluggable provider so it
    can participate in the registry alongside AI audio providers.
    """

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm
        self._generated_tracks: dict[str, AudioTrack] = {}

    @property
    def name(self) -> str:
        return "midi_engine"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.MIDI_GENERATION]

    @property
    def supported_instruments(self) -> list[str]:
        return list(_INSTRUMENT_AGENTS.keys())

    def is_available(self) -> bool:
        return True

    def generate_track(self, request: TrackRequest) -> TrackResult:
        instrument = request.instrument
        if not instrument or instrument not in _INSTRUMENT_AGENTS:
            return TrackResult(
                track=None,
                success=False,
                provider_used=self.name,
                error=f"MIDI provider does not support instrument '{instrument}'. "
                      f"Supported: {self.supported_instruments}",
            )

        try:
            agent_cls, instr_override = _INSTRUMENT_AGENTS[instrument]
            if instr_override is not None:
                agent = agent_cls(llm=self._llm, instrument=instr_override)
            else:
                agent = agent_cls(llm=self._llm)
            context = self._build_context(request)
            midi_data = agent.generate_part(context)

            # Normalise the track name to match the request
            midi_data = midi_data.model_copy(update={"name": request.track_name})

            track = AudioTrack(
                name=request.track_name,
                track_type=TrackType.MIDI,
                provider=self.name,
                midi_data=midi_data,
                tags=[instrument, request.genre or "unknown"],
            )
            self._generated_tracks[request.track_name] = track
            return TrackResult(track=track, success=True, provider_used=self.name)

        except Exception as e:
            logger.error("MIDI generation failed for '%s': %s", request.track_name, e)
            return TrackResult(
                track=None, success=False, provider_used=self.name, error=str(e)
            )

    def _build_context(self, request: TrackRequest) -> SessionContext:
        """Build a SessionContext from a TrackRequest."""
        genre = self._parse_genre(request.genre)
        key_root, key_mode = self._parse_key(request.key)

        config = SessionConfig(
            genre=genre,
            tempo=request.tempo or 120,
            key=KeySignature(root=key_root, mode=key_mode),
            band=BandConfig(members=[
                BandMemberConfig(instrument=Instrument(request.instrument or "drums"))
            ]),
        )

        progressions = self._get_progressions(genre, key_root.value, key_mode.value)
        chord_progs: dict[str, ChordProgression] = {}
        for section in config.structure:
            section_name = section.name.lower()
            if section_name in ("chorus", "outro"):
                chord_progs[section_name] = progressions.get(
                    "chorus", progressions["verse"]
                )
            else:
                chord_progs[section_name] = progressions.get(
                    "verse", progressions["verse"]
                )

        # Inject reference tracks from previous generations
        existing: dict[str, Any] = {}
        for ref_name in request.reference_track_names:
            if ref_name in self._generated_tracks:
                ref = self._generated_tracks[ref_name]
                if ref.midi_data:
                    existing[ref.midi_data.instrument.value] = ref.midi_data
            else:
                logger.warning(
                    "Reference track '%s' not found in generated tracks", ref_name
                )

        return SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions=chord_progs,
            existing_tracks=existing,
        )

    @staticmethod
    def _parse_genre(genre: Optional[str]) -> Genre:
        if not genre:
            return Genre.CLASSIC_ROCK
        try:
            return Genre(genre)
        except ValueError:
            return Genre.CLASSIC_ROCK

    @staticmethod
    def _parse_key(key: Optional[str]) -> tuple[NoteName, Mode]:
        if not key:
            return NoteName.C, Mode.MAJOR
        parts = key.split()
        root = NoteName.C
        mode = Mode.MAJOR
        if parts:
            for n in NoteName:
                if n.value == parts[0]:
                    root = n
                    break
        if len(parts) > 1:
            for m in Mode:
                if m.value == parts[1].lower():
                    mode = m
                    break
        return root, mode

    @staticmethod
    def _get_progressions(
        genre: Genre,
        key_root: str,
        key_mode: str,
    ) -> dict[str, ChordProgression]:
        if genre == Genre.BLUES:
            return {
                "verse": ProgressionFactory.twelve_bar_blues(key_root),
                "chorus": ProgressionFactory.twelve_bar_blues(key_root),
            }
        elif genre in (Genre.DELTA_BLUES, Genre.CHICAGO_BLUES):
            return {
                "verse": ProgressionFactory.twelve_bar_blues(key_root),
                "chorus": ProgressionFactory.blues_jazz(key_root),
            }
        elif genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK, Genre.SURF_ROCK, Genre.SOUTHERN_ROCK):
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre in (Genre.GARAGE_ROCK, Genre.NOISE):
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.grunge_minor_vamp(key_root),
            }
        elif genre == Genre.GRUNGE:
            return {
                "verse": ProgressionFactory.grunge_minor_vamp(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre in (Genre.ALT_ROCK, Genre.INDIE_ROCK, Genre.EMO, Genre.POST_PUNK):
            return {
                "verse": ProgressionFactory.indie_I_vi_iii_IV(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.PROG_ROCK:
            return {
                "verse": ProgressionFactory.prog_rock_epic(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre == Genre.PSYCHEDELIC_ROCK:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.prog_rock_epic(key_root),
            }
        elif genre in (Genre.POST_ROCK, Genre.SHOEGAZE):
            return {
                "verse": ProgressionFactory.post_rock_ambient(key_root),
                "chorus": ProgressionFactory.indie_I_vi_iii_IV(key_root),
            }
        elif genre == Genre.SOFT_ROCK:
            return {
                "verse": ProgressionFactory.rock_ballad(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.MATH_ROCK:
            return {
                "verse": ProgressionFactory.math_rock_odd(key_root),
                "chorus": ProgressionFactory.prog_rock_epic(key_root),
            }
        elif genre == Genre.POP:
            return {
                "verse": ProgressionFactory.pop_I_V_vi_IV(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre in (Genre.SYNTH_POP, Genre.NEW_WAVE):
            return {
                "verse": ProgressionFactory.synthwave_i_III_VII_VI(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre in (Genre.INDIE_POP, Genre.DREAM_POP):
            return {
                "verse": ProgressionFactory.indie_I_vi_iii_IV(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.K_POP:
            return {
                "verse": ProgressionFactory.pop_I_V_vi_IV(key_root),
                "chorus": ProgressionFactory.disco_I_vi_ii_V(key_root),
            }
        elif genre == Genre.DISCO:
            return {
                "verse": ProgressionFactory.disco_I_vi_ii_V(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre in (Genre.JAZZ, Genre.SWING, Genre.BEBOP, Genre.COOL_JAZZ):
            return {
                "verse": ProgressionFactory.jazz_ii_V_I(key_root),
                "chorus": ProgressionFactory.jazz_turnaround(key_root),
            }
        elif genre == Genre.FUSION:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.jazz_turnaround(key_root),
            }
        elif genre == Genre.SMOOTH_JAZZ:
            return {
                "verse": ProgressionFactory.jazz_ii_V_I(key_root),
                "chorus": ProgressionFactory.bossa_nova(key_root),
            }
        elif genre == Genre.FREE_JAZZ:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.jazz_ii_V_I(key_root),
            }
        elif genre == Genre.ACID_JAZZ:
            return {
                "verse": ProgressionFactory.funk_I7_IV7(key_root),
                "chorus": ProgressionFactory.jazz_turnaround(key_root),
            }
        elif genre in (Genre.FUNK, Genre.RNB, Genre.SOUL, Genre.MOTOWN):
            return {
                "verse": ProgressionFactory.funk_I7_IV7(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.NEO_SOUL:
            return {
                "verse": ProgressionFactory.neo_soul_ii_V_I(key_root),
                "chorus": ProgressionFactory.jazz_turnaround(key_root),
            }
        elif genre in (Genre.LATIN, Genre.BOSSA_NOVA):
            return {
                "verse": ProgressionFactory.bossa_nova(key_root),
                "chorus": ProgressionFactory.jazz_ii_V_I(key_root),
            }
        elif genre == Genre.SALSA:
            return {
                "verse": ProgressionFactory.salsa_montuno(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre == Genre.SAMBA:
            return {
                "verse": ProgressionFactory.bossa_nova(key_root),
                "chorus": ProgressionFactory.disco_I_vi_ii_V(key_root),
            }
        elif genre == Genre.REGGAETON:
            return {
                "verse": ProgressionFactory.reggaeton_i_IV_V(key_root),
                "chorus": ProgressionFactory.trap_minor_vamp(key_root),
            }
        elif genre == Genre.CUMBIA:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.TANGO:
            return {
                "verse": ProgressionFactory.flamenco_phrygian(key_root),
                "chorus": ProgressionFactory.minor_i_VII_VI_VII(key_root),
            }
        elif genre == Genre.METAL:
            return {
                "verse": ProgressionFactory.metal_power_I_VII_VI(key_root),
                "chorus": ProgressionFactory.minor_i_VII_VI_VII(key_root),
            }
        elif genre in (Genre.THRASH_METAL, Genre.DEATH_METAL, Genre.BLACK_METAL, Genre.METALCORE):
            return {
                "verse": ProgressionFactory.metal_power_I_VII_VI(key_root),
                "chorus": ProgressionFactory.grunge_minor_vamp(key_root),
            }
        elif genre == Genre.DOOM_METAL:
            return {
                "verse": ProgressionFactory.minor_i_VII_VI_VII(key_root),
                "chorus": ProgressionFactory.metal_power_I_VII_VI(key_root),
            }
        elif genre in (Genre.POWER_METAL, Genre.PROGRESSIVE_METAL):
            return {
                "verse": ProgressionFactory.metal_power_I_VII_VI(key_root),
                "chorus": ProgressionFactory.prog_rock_epic(key_root),
            }
        elif genre == Genre.NU_METAL:
            return {
                "verse": ProgressionFactory.grunge_minor_vamp(key_root),
                "chorus": ProgressionFactory.metal_power_I_VII_VI(key_root),
            }
        elif genre == Genre.INDUSTRIAL:
            return {
                "verse": ProgressionFactory.industrial_power_riff(key_root),
                "chorus": ProgressionFactory.metal_power_I_VII_VI(key_root),
            }
        elif genre == Genre.HIP_HOP:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.TRAP:
            return {
                "verse": ProgressionFactory.trap_minor_vamp(key_root),
                "chorus": ProgressionFactory.minor_i_VII_VI_VII(key_root),
            }
        elif genre in (Genre.LO_FI_HIP_HOP, Genre.CHILLWAVE, Genre.DOWNTEMPO):
            return {
                "verse": ProgressionFactory.jazz_ii_V_I(key_root),
                "chorus": ProgressionFactory.neo_soul_ii_V_I(key_root),
            }
        elif genre == Genre.BOOM_BAP:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.funk_I7_IV7(key_root),
            }
        elif genre in (Genre.ELECTRONIC, Genre.HOUSE, Genre.DEEP_HOUSE, Genre.TECH_HOUSE, Genre.ELECTRO, Genre.GARAGE_ELECTRONIC):
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.TECHNO:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.synthwave_i_III_VII_VI(key_root),
            }
        elif genre == Genre.TRANCE:
            return {
                "verse": ProgressionFactory.trance_uplifting(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.DRUM_AND_BASS:
            return {
                "verse": ProgressionFactory.dnb_minor_tension(key_root),
                "chorus": ProgressionFactory.minor_i_VII_VI_VII(key_root),
            }
        elif genre == Genre.DUBSTEP:
            return {
                "verse": ProgressionFactory.dubstep_halftime(key_root),
                "chorus": ProgressionFactory.trap_minor_vamp(key_root),
            }
        elif genre in (Genre.AMBIENT, Genre.IDM, Genre.VAPORWAVE):
            return {
                "verse": ProgressionFactory.post_rock_ambient(key_root),
                "chorus": ProgressionFactory.modal_dorian(key_root),
            }
        elif genre == Genre.SYNTHWAVE:
            return {
                "verse": ProgressionFactory.synthwave_i_III_VII_VI(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.GOSPEL:
            return {
                "verse": ProgressionFactory.gospel_I_IV_I_V(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.WORSHIP:
            return {
                "verse": ProgressionFactory.worship_I_IV_vi_V(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.REGGAE:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.SKA:
            return {
                "verse": ProgressionFactory.ska_offbeat(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.DUB:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre == Genre.DANCEHALL:
            return {
                "verse": ProgressionFactory.reggaeton_i_IV_V(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.CALYPSO:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.disco_I_vi_ii_V(key_root),
            }
        elif genre == Genre.AFROBEAT:
            return {
                "verse": ProgressionFactory.afrobeat_vamp(key_root),
                "chorus": ProgressionFactory.funk_I7_IV7(key_root),
            }
        elif genre == Genre.HIGHLIFE:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.afrobeat_vamp(key_root),
            }
        elif genre == Genre.FLAMENCO:
            return {
                "verse": ProgressionFactory.flamenco_phrygian(key_root),
                "chorus": ProgressionFactory.flamenco_phrygian(key_root),
            }
        elif genre == Genre.MIDDLE_EASTERN:
            return {
                "verse": ProgressionFactory.middle_eastern_hijaz(key_root),
                "chorus": ProgressionFactory.flamenco_phrygian(key_root),
            }
        elif genre == Genre.BOLLYWOOD:
            return {
                "verse": ProgressionFactory.middle_eastern_hijaz(key_root),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre in (Genre.CLASSICAL, Genre.ROMANTIC_ERA):
            return {
                "verse": ProgressionFactory.classical_I_IV_V_I(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre == Genre.BAROQUE:
            return {
                "verse": ProgressionFactory.baroque_circle_of_fifths(key_root),
                "chorus": ProgressionFactory.classical_I_IV_V_I(key_root),
            }
        elif genre == Genre.CINEMATIC:
            return {
                "verse": ProgressionFactory.cinematic_epic(key_root),
                "chorus": ProgressionFactory.post_rock_ambient(key_root),
            }
        elif genre in (Genre.COUNTRY, Genre.AMERICANA):
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.FOLK:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.rock_ballad(key_root),
            }
        elif genre == Genre.BLUEGRASS:
            return {
                "verse": ProgressionFactory.bluegrass_I_IV_V(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        elif genre == Genre.CELTIC:
            return {
                "verse": ProgressionFactory.modal_dorian(key_root),
                "chorus": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
            }
        else:
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
