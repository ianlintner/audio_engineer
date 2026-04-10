"""Session Orchestrator - coordinates all agents to produce a complete session."""
from __future__ import annotations

import uuid
import logging
from pathlib import Path
from typing import Any

from audio_engineer.core.models import (
    Genre, Instrument, SessionConfig, SessionStatus, Session,
    MidiTrackData, SectionDef, MixConfig, RenderConfig,
)
from audio_engineer.core.music_theory import ChordProgression, ProgressionFactory
from audio_engineer.core.midi_engine import MidiEngine
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent
from audio_engineer.agents.musician.bassist import BassistAgent
from audio_engineer.agents.musician.guitarist import GuitaristAgent
from audio_engineer.agents.musician.keyboardist import KeyboardistAgent
from audio_engineer.agents.engineer.mixer import MixerAgent
from audio_engineer.agents.engineer.mastering import MasteringAgent
from audio_engineer.daw import get_backend

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
        self.mixer = MixerAgent(llm=llm)
        self.mastering = MasteringAgent(llm=llm)

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

            if Instrument.KEYS in enabled_instruments:
                logger.info("Generating keyboard track...")
                keys_track = self.keyboardist.generate_part(context)
                context.existing_tracks[Instrument.KEYS.value] = keys_track
                session.tracks["keys"] = keys_track

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
        elif genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK):
            return {
                "verse": ProgressionFactory.classic_rock_I_IV_V(key_root, key_mode),
                "chorus": ProgressionFactory.pop_I_V_vi_IV(key_root),
            }
        elif genre == Genre.POP:
            return {
                "verse": ProgressionFactory.pop_I_V_vi_IV(key_root),
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
                    audio_path = session_dir / f"{session.id}_full.wav"
                    backend.render_audio(midi_path, audio_path, RenderConfig())
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
