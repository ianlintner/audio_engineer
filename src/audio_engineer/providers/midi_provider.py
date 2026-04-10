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
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.drummer import DrummerAgent
from audio_engineer.agents.musician.bassist import BassistAgent
from audio_engineer.agents.musician.guitarist import GuitaristAgent
from audio_engineer.agents.musician.keyboardist import KeyboardistAgent
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Map instrument name strings to agent constructors
_INSTRUMENT_AGENTS: dict[str, type] = {
    "drums": DrummerAgent,
    "bass": BassistAgent,
    "electric_guitar": GuitaristAgent,
    "acoustic_guitar": GuitaristAgent,
    "keys": KeyboardistAgent,
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
            agent_cls = _INSTRUMENT_AGENTS[instrument]
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
