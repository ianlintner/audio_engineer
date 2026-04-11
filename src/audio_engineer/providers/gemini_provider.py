"""Provider wrapping Google Gemini Lyria for AI audio generation."""
from __future__ import annotations

import logging
from typing import Any

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)

# Duration threshold: above this, use full-song model instead of clip
_FULL_SONG_THRESHOLD_SECONDS = 45.0


def _gemini_importable() -> bool:
    try:
        import audio_engineer.gemini  # noqa: F401
        return True
    except Exception:
        return False


class GeminiLyriaProvider(AudioProvider):
    """Generate audio tracks via Google Lyria 3 models.

    Falls back gracefully when google-genai is not installed.
    Uses clip model for short segments, pro model for full songs.
    """

    def __init__(self) -> None:
        self._music_agent: Any = None
        self._available = False

        if _gemini_importable():
            try:
                from audio_engineer.gemini import MusicGenerationAgent
                self._music_agent = MusicGenerationAgent()
                self._available = True
                logger.info("Gemini Lyria provider initialized")
            except Exception as exc:
                logger.debug("Gemini Lyria init failed: %s", exc)

    @property
    def name(self) -> str:
        return "gemini_lyria"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [
            ProviderCapability.AUDIO_GENERATION,
            ProviderCapability.VOCALS,
            ProviderCapability.TEXT_TO_SPEECH,
        ]

    def is_available(self) -> bool:
        return self._available

    def generate_track(self, request: TrackRequest) -> TrackResult:
        if not self._available or self._music_agent is None:
            return TrackResult(
                track=None, success=False, provider_used=self.name,
                error="Gemini Lyria is not available (google-genai not installed or no API key)",
            )

        try:
            prompt = self._build_prompt(request)
            use_full_song = (
                request.duration_seconds is not None
                and request.duration_seconds > _FULL_SONG_THRESHOLD_SECONDS
            )

            if use_full_song:
                gen_result = self._music_agent.generate_song(
                    prompt, instrumental=True
                )
            else:
                gen_result = self._music_agent.generate_clip(
                    prompt, instrumental=True
                )

            track = AudioTrack(
                name=request.track_name,
                track_type=TrackType.AUDIO,
                provider=self.name,
                audio_data=gen_result.audio_data,
                mime_type=gen_result.mime_type,
                duration_seconds=request.duration_seconds,
                tags=request.style_hints[:],
            )

            return TrackResult(track=track, success=True, provider_used=self.name)

        except Exception as e:
            logger.error("Gemini Lyria generation failed: %s", e)
            return TrackResult(
                track=None, success=False, provider_used=self.name, error=str(e),
            )

    def _build_prompt(self, request: TrackRequest) -> str:
        """Construct a Lyria-friendly prompt from the track request."""
        parts: list[str] = [request.description]

        if request.genre:
            parts.append(f"Genre: {request.genre.replace('_', ' ')}.")
        if request.key:
            parts.append(f"Key: {request.key}.")
        if request.tempo:
            parts.append(f"Tempo: {request.tempo} BPM.")
        if request.style_hints:
            parts.append(f"Style: {', '.join(request.style_hints)}.")

        return " ".join(parts)
