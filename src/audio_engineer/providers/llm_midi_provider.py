"""LLM-powered MIDI generation provider."""
from __future__ import annotations

import logging
from typing import Callable

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
    MidiTrackData,
)
from audio_engineer.core.constants import TICKS_PER_BEAT
from audio_engineer.core.llm_prompts import (
    build_midi_prompt,
    parse_midi_json,
    validate_midi_events,
    events_to_note_events,
)
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Channel assignments (mirrors midi_provider defaults)
_INSTRUMENT_CHANNELS: dict[str, int] = {
    "drums": 9,
    "bass": 1,
    "electric_guitar": 2,
    "acoustic_guitar": 2,
    "lead_guitar": 4,
    "keys": 3,
    "organ": 3,
    "strings": 5,
    "violin": 5,
    "brass": 6,
    "trumpet": 6,
    "saxophone": 6,
    "woodwinds": 6,
    "synthesizer": 7,
    "pad": 7,
}

# GM program suggestions per instrument name
_INSTRUMENT_PROGRAMS: dict[str, int] = {
    "drums": 0,
    "bass": 33,
    "electric_guitar": 29,
    "acoustic_guitar": 25,
    "lead_guitar": 30,
    "keys": 0,
    "organ": 18,
    "strings": 48,
    "violin": 40,
    "brass": 61,
    "trumpet": 56,
    "saxophone": 66,
    "woodwinds": 73,
    "synthesizer": 81,
    "pad": 89,
    "vibraphone": 11,
    "marimba": 12,
}


class LLMMidiProvider(AudioProvider):
    """Generate MIDI tracks by prompting an LLM and parsing the JSON response.

    The LLM callable should accept a single string prompt and return a string.
    Falls back to the built-in MidiProvider when the LLM is unavailable or
    when its output cannot be parsed.
    """

    def __init__(self, llm: Callable[[str], str] | None = None) -> None:
        self._llm = llm
        # Lazy import to avoid circular dependency
        self._fallback: AudioProvider | None = None

    # ------------------------------------------------------------------
    # AudioProvider interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "llm_midi"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.MIDI_GENERATION]

    def is_available(self) -> bool:
        return self._llm is not None

    def generate_track(self, request: TrackRequest) -> TrackResult:
        if not self.is_available():
            return TrackResult(
                track=None, success=False, provider_used=self.name,
                error="LLMMidiProvider: no LLM callable configured",
            )

        instrument = request.instrument or "keys"
        channel = _INSTRUMENT_CHANNELS.get(instrument, 0)
        program = _INSTRUMENT_PROGRAMS.get(instrument, 0)
        config = self._build_session_config(request)
        beats_per_bar = config.time_signature.numerator

        # Build sections from the session structure
        all_events = []
        bar_offset = 0
        ticks_per_bar = beats_per_bar * TICKS_PER_BEAT
        for section in config.structure:
            for _ in range(section.repeats):
                prompt = build_midi_prompt(request, beats_per_bar)
                # Generate one template bar at offset 0, then shift per-bar copy
                template_events = self._generate_bar(prompt, channel, beats_per_bar, 0)
                if template_events is None:
                    # LLM failed — fall back for this section
                    return self._fallback_result(request)
                # Repeat the pattern for each bar in the section at the correct tick offset
                for bar_idx in range(section.bars):
                    offset_ticks = (bar_offset + bar_idx) * ticks_per_bar
                    for ev in template_events:
                        all_events.append(
                            ev.model_copy(update={"start_tick": ev.start_tick + offset_ticks})
                        )
                bar_offset += section.bars

        if not all_events:
            return self._fallback_result(request)

        midi_data = MidiTrackData(
            name=request.track_name,
            instrument=Instrument(instrument) if instrument in [i.value for i in Instrument] else Instrument.KEYS,
            channel=channel,
            events=sorted(all_events, key=lambda e: e.start_tick),
            program=program,
        )

        track = AudioTrack(
            name=request.track_name,
            track_type=TrackType.MIDI,
            provider=self.name,
            midi_data=midi_data,
            tags=[instrument, request.genre or "unknown"],
        )
        return TrackResult(track=track, success=True, provider_used=self.name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_bar(
        self, prompt: str, channel: int, beats_per_bar: int, bar_offset: int
    ) -> list | None:
        """Call LLM and parse one bar of notes. Returns None on failure."""
        assert self._llm is not None
        try:
            response = self._llm(prompt)
        except Exception as exc:
            logger.warning("LLM call failed: %s", exc)
            return None

        raw = parse_midi_json(response)
        if raw is None:
            logger.warning("LLMMidiProvider: could not parse LLM JSON response")
            return None

        validated = validate_midi_events(raw, beats_per_bar=beats_per_bar)
        if not validated:
            logger.warning("LLMMidiProvider: no valid events after validation")
            return None

        bar_offset_ticks = bar_offset * TICKS_PER_BEAT * beats_per_bar
        return events_to_note_events(validated, channel=channel, bar_offset_ticks=bar_offset_ticks)

    def _fallback_result(self, request: TrackRequest) -> TrackResult:
        """Delegate to the built-in MidiProvider as a fallback."""
        if self._fallback is None:
            from audio_engineer.providers.midi_provider import MidiProvider
            self._fallback = MidiProvider(llm=None)
        logger.info("LLMMidiProvider: falling back to MidiProvider for '%s'", request.track_name)
        result = self._fallback.generate_track(request)
        # Override provider_used so callers know what happened
        return TrackResult(
            track=result.track,
            success=result.success,
            provider_used=f"{self.name}(fallback:{result.provider_used})",
            error=result.error,
        )

    @staticmethod
    def _build_session_config(request: TrackRequest) -> SessionConfig:
        """Convert a TrackRequest into a minimal SessionConfig."""
        # Parse genre
        genre = Genre.CLASSIC_ROCK
        if request.genre:
            try:
                genre = Genre(request.genre)
            except ValueError:
                pass

        # Parse key
        key_root = NoteName.C
        key_mode = Mode.MAJOR
        if request.key:
            parts = request.key.split()
            for n in NoteName:
                if n.value == parts[0]:
                    key_root = n
                    break
            if len(parts) > 1:
                for m in Mode:
                    if m.value == parts[1].lower():
                        key_mode = m
                        break

        instrument = Instrument.KEYS
        if request.instrument:
            try:
                instrument = Instrument(request.instrument)
            except ValueError:
                pass

        return SessionConfig(
            genre=genre,
            tempo=request.tempo or 120,
            key=KeySignature(root=key_root, mode=key_mode),
            band=BandConfig(members=[BandMemberConfig(instrument=instrument)]),
        )
