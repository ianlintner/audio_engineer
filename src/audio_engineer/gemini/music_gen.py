"""Music generation via Google Lyria 3 models."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from audio_engineer.gemini.client import GeminiClient, get_gemini_client

logger = logging.getLogger(__name__)

# Lyria 3 model identifiers
LYRIA_CLIP_MODEL = "lyria-3-clip-preview"
LYRIA_PRO_MODEL = "lyria-3-pro-preview"


class MusicGenResult:
    """Container for a Lyria generation result."""

    def __init__(self, audio_data: bytes, lyrics: Optional[str], mime_type: str):
        self.audio_data = audio_data
        self.lyrics = lyrics
        self.mime_type = mime_type

    def save(self, path: str | Path) -> Path:
        """Write audio bytes to *path* and return the resolved ``Path``."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self.audio_data)
        logger.info("Saved generated audio to %s", out)
        return out


class MusicGenerationAgent:
    """Generate music clips or full songs using Google Lyria 3.

    Capabilities
    ------------
    * 30-second clips (``lyria-3-clip-preview``)
    * Full-length songs with structure (``lyria-3-pro-preview``)
    * Instrumental-only generation
    * Custom lyrics / section tags
    * Image-inspired composition
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        self._client = client or get_gemini_client()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_clip(
        self,
        prompt: str,
        *,
        instrumental: bool = False,
    ) -> MusicGenResult:
        """Generate a 30-second audio clip via Lyria 3 Clip.

        Parameters
        ----------
        prompt:
            Natural-language description (genre, instruments, mood, BPM …).
        instrumental:
            When *True*, appends "Instrumental only, no vocals." to the prompt.
        """
        if instrumental and "instrumental" not in prompt.lower():
            prompt = f"{prompt}\nInstrumental only, no vocals."

        return self._generate(LYRIA_CLIP_MODEL, prompt)

    def generate_song(
        self,
        prompt: str,
        *,
        output_format: str = "audio/mp3",
        instrumental: bool = False,
    ) -> MusicGenResult:
        """Generate a full-length song via Lyria 3 Pro.

        Parameters
        ----------
        prompt:
            Description **or** structured prompt with ``[Verse]``/``[Chorus]``
            tags and/or timestamps.
        output_format:
            ``"audio/mp3"`` (default) or ``"audio/wav"``.
        instrumental:
            When *True*, appends "Instrumental only, no vocals." to the prompt.
        """
        if instrumental and "instrumental" not in prompt.lower():
            prompt = f"{prompt}\nInstrumental only, no vocals."

        return self._generate(LYRIA_PRO_MODEL, prompt, mime_type=output_format)

    def generate_from_session(
        self,
        genre: str,
        key: str,
        tempo: int,
        structure: list,
        *,
        instruments: Optional[list[str]] = None,
        instrumental: bool = True,
        full_song: bool = False,
    ) -> MusicGenResult:
        """Build a Lyria prompt from session parameters and generate audio.

        This bridges the existing ``SessionConfig`` world into Lyria by
        converting structured data into a rich text prompt.
        """
        parts: list[str] = []
        parts.append(
            f"Create a {genre.replace('_', ' ')} track in {key} at {tempo} BPM."
        )

        if instruments:
            parts.append(f"Instruments: {', '.join(instruments)}.")

        # Map sections to timestamped structure hints
        for section in structure:
            if isinstance(section, dict):
                name = section.get("name", "section")
                bars = section.get("bars", 4)
                intensity = section.get("intensity", 0.7)
            else:
                name = str(section)
                bars = 4
                intensity = 0.7
            dynamic = "forte" if intensity > 0.7 else "piano" if intensity < 0.4 else "mezzo-forte"
            parts.append(f"[{name.capitalize()}] {bars} bars, {dynamic} dynamics.")

        if instrumental:
            parts.append("Instrumental only, no vocals.")

        prompt = "\n".join(parts)
        logger.debug("Lyria prompt:\n%s", prompt)

        model = LYRIA_PRO_MODEL if full_song else LYRIA_CLIP_MODEL
        return self._generate(model, prompt)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _generate(
        self, model: str, prompt: str, mime_type: str = "audio/mp3"
    ) -> MusicGenResult:
        """Call the Lyria model and parse response parts."""
        types = self._client.types

        config_kwargs: dict = {
            "response_modalities": ["AUDIO", "TEXT"],
        }
        if model == LYRIA_PRO_MODEL and mime_type:
            config_kwargs["response_mime_type"] = mime_type

        response = self._client.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        lyrics_parts: list[str] = []
        audio_data: bytes | None = None
        audio_mime: str = mime_type

        for part in response.parts:
            if part.text is not None:
                lyrics_parts.append(part.text)
            elif part.inline_data is not None:
                audio_data = part.inline_data.data
                if part.inline_data.mime_type:
                    audio_mime = part.inline_data.mime_type

        if audio_data is None:
            raise RuntimeError(
                "Lyria model returned no audio data. "
                "Check your prompt or API quota."
            )

        return MusicGenResult(
            audio_data=audio_data,
            lyrics="\n".join(lyrics_parts) if lyrics_parts else None,
            mime_type=audio_mime,
        )
