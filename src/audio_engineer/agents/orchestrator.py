"""Session Orchestrator - coordinates all agents to produce a complete session."""
from __future__ import annotations

import uuid
import logging
from pathlib import Path
from typing import Any

from audio_engineer.core.models import (
    Genre, Instrument, SessionConfig, SessionStatus, Session,
    RenderConfig,
)
from audio_engineer.core.music_theory import ChordProgression, ProgressionFactory
from audio_engineer.core.midi_engine import MidiEngine
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent
from audio_engineer.agents.musician.bassist import BassistAgent
from audio_engineer.agents.musician.guitarist import GuitaristAgent
from audio_engineer.agents.musician.keyboardist import KeyboardistAgent
from audio_engineer.agents.musician.strings import StringsAgent
from audio_engineer.agents.musician.brass import BrassAgent
from audio_engineer.agents.musician.synth import SynthAgent
from audio_engineer.agents.musician.percussion import PercussionAgent
from audio_engineer.agents.musician.lead_guitar import LeadGuitarAgent
from audio_engineer.agents.engineer.mixer import MixerAgent
from audio_engineer.agents.engineer.mastering import MasteringAgent
from audio_engineer.daw import get_backend
from audio_engineer.providers import ProviderRegistry, MidiProvider, GeminiLyriaProvider, LLMMidiProvider

logger = logging.getLogger(__name__)


def _gemini_available() -> bool:
    """Check if the Gemini integration is importable."""
    try:
        import audio_engineer.gemini  # noqa: F401
        return True
    except Exception:
        return False


class SessionOrchestrator:
    """Coordinates musician and engineer agents for a complete session."""

    def __init__(self, llm: Any = None, output_dir: str | Path = "./output"):
        self.llm = llm
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.midi_engine = MidiEngine()

        # Initialize agents
        self.drummer = DrummerAgent(llm=llm)
        self.bassist = BassistAgent(llm=llm)
        self.guitarist = GuitaristAgent(llm=llm)
        self.keyboardist = KeyboardistAgent(llm=llm)
        self.strings_agent = StringsAgent(llm=llm)
        self.brass_agent = BrassAgent(llm=llm)
        self.synth_agent = SynthAgent(llm=llm)
        self.lead_guitar_agent = LeadGuitarAgent(llm=llm)
        self.percussion_agent = PercussionAgent(llm=llm)
        self.mixer = MixerAgent(llm=llm)
        self.mastering = MasteringAgent(llm=llm)

        # Provider registry
        self.provider_registry = ProviderRegistry()
        # LLMMidiProvider takes priority when LLM is configured
        if llm is not None:
            self.provider_registry.register(LLMMidiProvider(llm=llm))
        self.provider_registry.register(MidiProvider(llm=llm))
        self.provider_registry.register(GeminiLyriaProvider())

        # Optional Gemini agents (available when google-genai is installed)
        self._gemini_music: Any = None
        self._gemini_analysis: Any = None
        self._gemini_tts: Any = None
        if _gemini_available():
            try:
                from audio_engineer.gemini import (
                    MusicGenerationAgent,
                    AudioAnalysisAgent,
                    TTSAgent,
                )
                self._gemini_music = MusicGenerationAgent()
                self._gemini_analysis = AudioAnalysisAgent()
                self._gemini_tts = TTSAgent()
                logger.info("Gemini agents initialised")
            except Exception as exc:
                logger.debug("Gemini agents not available: %s", exc)

    def create_session(self, config: SessionConfig | None = None) -> Session:
        """Create a new session."""
        return Session(
            id=str(uuid.uuid4())[:8],
            config=config or SessionConfig(),
            status=SessionStatus.CREATED,
        )

    def run_session(
        self,
        session: Session,
        render_audio: bool = False,
        backend_name: str = "export",
    ) -> Session:
        """Run a complete session: plan -> generate -> mix -> export."""
        try:
            # 1. Planning phase
            session.status = SessionStatus.PLANNING
            logger.info(
                "Planning session %s: %s in %s %s",
                session.id,
                session.config.genre.value,
                session.config.key.root.value,
                session.config.key.mode.value,
            )

            context = self._build_context(session)

            # 2. Generation phase - sequential: drums -> bass -> guitar -> keys
            session.status = SessionStatus.GENERATING

            # Drums first (foundation)
            logger.info("Generating drum track...")
            drum_track = self.drummer.generate_part(context)
            context.existing_tracks[Instrument.DRUMS.value] = drum_track
            session.tracks["drums"] = drum_track

            # Bass locks to drums
            logger.info("Generating bass track...")
            bass_track = self.bassist.generate_part(context)
            context.existing_tracks[Instrument.BASS.value] = bass_track
            session.tracks["bass"] = bass_track

            # Guitar fits around rhythm section
            enabled_instruments = {
                m.instrument for m in session.config.band.members if m.enabled
            }

            if Instrument.ELECTRIC_GUITAR in enabled_instruments or Instrument.ACOUSTIC_GUITAR in enabled_instruments:
                logger.info("Generating guitar track...")
                guitar_track = self.guitarist.generate_part(context)
                instr_key = self.guitarist.instrument.value
                context.existing_tracks[instr_key] = guitar_track
                session.tracks["guitar"] = guitar_track

            if Instrument.LEAD_GUITAR in enabled_instruments:
                logger.info("Generating lead guitar track...")
                lead_track = self.lead_guitar_agent.generate_part(context)
                context.existing_tracks[Instrument.LEAD_GUITAR.value] = lead_track
                session.tracks["lead_guitar"] = lead_track

            if Instrument.KEYS in enabled_instruments:
                logger.info("Generating keyboard track...")
                keys_track = self.keyboardist.generate_part(context)
                context.existing_tracks[Instrument.KEYS.value] = keys_track
                session.tracks["keys"] = keys_track

            if Instrument.ORGAN in enabled_instruments:
                logger.info("Generating organ track...")
                organ_agent = KeyboardistAgent(llm=self.llm, instrument=Instrument.ORGAN)
                organ_track = organ_agent.generate_part(context)
                organ_key = organ_track.instrument.value
                context.existing_tracks[organ_key] = organ_track
                session.tracks[organ_key] = organ_track

            if Instrument.STRINGS in enabled_instruments or Instrument.VIOLIN in enabled_instruments:
                # VIOLIN takes precedence over STRINGS when both are enabled
                strings_instr = (
                    Instrument.VIOLIN if Instrument.VIOLIN in enabled_instruments
                    else Instrument.STRINGS
                )
                logger.info("Generating %s track...", strings_instr.value)
                strings_agent = StringsAgent(llm=self.llm, instrument=strings_instr)
                strings_track = strings_agent.generate_part(context)
                context.existing_tracks[strings_instr.value] = strings_track
                session.tracks[strings_instr.value] = strings_track

            if Instrument.BRASS in enabled_instruments or Instrument.TRUMPET in enabled_instruments or Instrument.SAXOPHONE in enabled_instruments:
                # Priority order: TRUMPET > SAXOPHONE > BRASS (one track per session)
                brass_instrument = Instrument.BRASS
                if Instrument.TRUMPET in enabled_instruments:
                    brass_instrument = Instrument.TRUMPET
                elif Instrument.SAXOPHONE in enabled_instruments:
                    brass_instrument = Instrument.SAXOPHONE
                logger.info("Generating %s track...", brass_instrument.value)
                brass_agent = BrassAgent(llm=self.llm, instrument=brass_instrument)
                brass_track = brass_agent.generate_part(context)
                context.existing_tracks[brass_instrument.value] = brass_track
                session.tracks[brass_instrument.value] = brass_track

            if Instrument.SYNTHESIZER in enabled_instruments or Instrument.PAD in enabled_instruments:
                synth_instr = (
                    Instrument.SYNTHESIZER if Instrument.SYNTHESIZER in enabled_instruments
                    else Instrument.PAD
                )
                logger.info("Generating %s track...", synth_instr.value)
                synth_agent = SynthAgent(llm=self.llm, instrument=synth_instr)
                synth_track = synth_agent.generate_part(context)
                context.existing_tracks[synth_instr.value] = synth_track
                session.tracks[synth_instr.value] = synth_track

            if Instrument.PERCUSSION in enabled_instruments or Instrument.CONGA in enabled_instruments or Instrument.BONGO in enabled_instruments or Instrument.DJEMBE in enabled_instruments:
                logger.info("Generating percussion track...")
                perc_instr = next(
                    (i for i in enabled_instruments if i in (Instrument.CONGA, Instrument.BONGO, Instrument.DJEMBE, Instrument.PERCUSSION)),
                    Instrument.PERCUSSION,
                )
                perc_agent = PercussionAgent(llm=self.llm, instrument=perc_instr)
                perc_track = perc_agent.generate_part(context)
                perc_key = perc_track.instrument.value
                context.existing_tracks[perc_key] = perc_track
                session.tracks[perc_key] = perc_track

            # 3. Mixing phase
            session.status = SessionStatus.MIXING
            logger.info("Mixing tracks...")
            all_tracks = list(session.tracks.values())
            mix_config = self.mixer.process(all_tracks, context)
            session.mix = mix_config

            # Mastering
            master_info = self.mastering.process(all_tracks, context)
            logger.info("Mastering: %s", master_info)

            # 4. Export phase
            logger.info("Exporting...")
            output_files = self._export(session, backend_name, render_audio)
            session.output_files = [str(f) for f in output_files]

            session.status = SessionStatus.COMPLETE
            logger.info("Session %s complete! Files: %s", session.id, session.output_files)
            return session

        except Exception as e:
            session.status = SessionStatus.ERROR
            logger.error("Session %s failed: %s", session.id, e)
            raise

    def _build_context(self, session: Session) -> SessionContext:
        """Build session context with chord progressions for each section."""
        config = session.config
        key_root = config.key.root.value
        key_mode = config.key.mode.value

        # Select progression based on genre
        progressions = self._get_genre_progressions(config.genre, key_root, key_mode)

        # Map progressions to sections
        chord_progs: dict[str, ChordProgression] = {}
        for section in config.structure:
            section_name = section.name.lower()
            if section_name in ("chorus", "outro"):
                chord_progs[section_name] = progressions.get("chorus", progressions["verse"])
            else:
                chord_progs[section_name] = progressions.get("verse", progressions["verse"])

        return SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions=chord_progs,
            existing_tracks={},
        )

    def _get_genre_progressions(
        self, genre: Genre, key_root: str, key_mode: str
    ) -> dict[str, ChordProgression]:
        """Get appropriate chord progressions for a genre."""
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

    def _export(self, session: Session, backend_name: str, render_audio: bool) -> list[Path]:
        """Export session to files."""
        output_files: list[Path] = []
        session_dir = self.output_dir / session.id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Export combined MIDI
        all_tracks = list(session.tracks.values())
        midi_file = self.midi_engine.merge_tracks(all_tracks, session.config.tempo)
        midi_path = session_dir / f"{session.id}_full.mid"
        self.midi_engine.export_midi(midi_file, midi_path)
        output_files.append(midi_path)

        # Export individual tracks
        for name, track in session.tracks.items():
            track_path = session_dir / f"{session.id}_{name}.mid"
            self.midi_engine.export_track(track, track_path, session.config.tempo)
            output_files.append(track_path)

        # Render audio if requested
        if render_audio:
            try:
                backend = get_backend(backend_name)
                if backend.is_available():
                    render_cfg = RenderConfig()
                    audio_ext = f".{render_cfg.format}"
                    audio_path = session_dir / f"{session.id}_full{audio_ext}"
                    backend.render_audio(midi_path, audio_path, render_cfg)
                    output_files.append(audio_path)
                else:
                    logger.warning("Backend '%s' not available, skipping audio render", backend_name)
            except Exception as e:
                logger.warning("Audio render failed: %s", e)

        # Generate Lyria audio rendition if Gemini music agent is available
        if self._gemini_music is not None:
            try:
                config = session.config
                instr_names = [
                    m.instrument.value
                    for m in config.band.members if m.enabled
                ]
                result = self._gemini_music.generate_from_session(
                    genre=config.genre.value,
                    key=f"{config.key.root.value} {config.key.mode.value}",
                    tempo=config.tempo,
                    structure=[s.name for s in config.structure],
                    instruments=instr_names,
                    instrumental=True,
                )
                lyria_path = session_dir / f"{session.id}_lyria.mp3"
                result.save(lyria_path)
                output_files.append(lyria_path)
            except Exception as e:
                logger.warning("Lyria music generation skipped: %s", e)

        # Export session config as JSON
        config_path = session_dir / f"{session.id}_config.json"
        config_path.write_text(session.config.model_dump_json(indent=2))
        output_files.append(config_path)

        return output_files
