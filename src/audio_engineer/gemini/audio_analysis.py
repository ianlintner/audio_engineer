"""Audio analysis via Gemini multimodal understanding."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from audio_engineer.gemini.client import GeminiClient, get_gemini_client

logger = logging.getLogger(__name__)

# Any Gemini model that supports multimodal audio input
DEFAULT_ANALYSIS_MODEL = "gemini-2.5-flash"


class AudioSegment(BaseModel):
    """A single segment identified during analysis."""
    timestamp: str = ""
    description: str = ""
    emotion: str = ""


class AudioAnalysisResult(BaseModel):
    """Structured result from Gemini audio analysis."""
    summary: str = ""
    key_detected: str = ""
    tempo_estimate: str = ""
    genre_tags: list[str] = Field(default_factory=list)
    instruments_detected: list[str] = Field(default_factory=list)
    segments: list[AudioSegment] = Field(default_factory=list)
    mix_feedback: str = ""
    raw_text: str = ""


class AudioAnalysisAgent:
    """Analyse audio files using Gemini's multimodal understanding.

    Capabilities
    ------------
    * Describe / summarise audio content
    * Detect key, tempo, genre, instruments
    * Provide mix / mastering feedback
    * Transcribe speech segments with timestamps
    * Emotion detection in speech and music
    """

    def __init__(
        self,
        client: Optional[GeminiClient] = None,
        model: str = DEFAULT_ANALYSIS_MODEL,
    ):
        self._client = client or get_gemini_client()
        self._model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse_file(
        self, audio_path: str | Path, prompt: Optional[str] = None
    ) -> AudioAnalysisResult:
        """Upload an audio file and get structured analysis.

        Parameters
        ----------
        audio_path:
            Path to an audio file (wav, mp3, aiff, aac, ogg, flac).
        prompt:
            Optional custom prompt.  When *None*, a default music-analysis
            prompt is used.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        types = self._client.types
        mime = _mime_for(audio_path.suffix)

        with open(audio_path, "rb") as fh:
            audio_bytes = fh.read()

        contents = [
            prompt or _default_analysis_prompt(),
            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        ]

        response = self._client.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=AudioAnalysisResult.model_json_schema(),
            ),
        )

        text = response.text or "{}"
        try:
            data = json.loads(text)
            return AudioAnalysisResult(**data)
        except (json.JSONDecodeError, Exception):
            return AudioAnalysisResult(raw_text=text)

    def get_mix_feedback(
        self, audio_path: str | Path, genre: str = ""
    ) -> str:
        """Return plain-text mixing / mastering feedback for an audio file."""
        audio_path = Path(audio_path)
        types = self._client.types
        mime = _mime_for(audio_path.suffix)

        with open(audio_path, "rb") as fh:
            audio_bytes = fh.read()

        prompt = (
            "You are an experienced audio engineer. Listen to this track and "
            "provide concise, actionable feedback on the mix: levels, EQ balance, "
            "stereo image, dynamics, and any clipping or muddiness. "
        )
        if genre:
            prompt += f"The intended genre is {genre}. "
        prompt += "Be specific with frequency ranges and instrument names."

        contents = [
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        ]

        response = self._client.generate_content(
            model=self._model,
            contents=contents,
        )
        return response.text or ""

    def describe_audio(self, audio_path: str | Path) -> str:
        """Return a free-form description of the audio content."""
        audio_path = Path(audio_path)
        types = self._client.types
        mime = _mime_for(audio_path.suffix)

        with open(audio_path, "rb") as fh:
            audio_bytes = fh.read()

        response = self._client.generate_content(
            model=self._model,
            contents=[
                "Describe this audio clip in detail — instruments, mood, "
                "structure, tempo, key, and any notable production techniques.",
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
            ],
        )
        return response.text or ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".aiff": "audio/aiff",
    ".aif": "audio/aiff",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _mime_for(suffix: str) -> str:
    mime = _MIME_MAP.get(suffix.lower())
    if mime is None:
        raise ValueError(
            f"Unsupported audio format {suffix!r}. "
            f"Supported: {', '.join(sorted(_MIME_MAP))}"
        )
    return mime


def _default_analysis_prompt() -> str:
    return (
        "Analyse this audio track as a professional music producer. "
        "Return a JSON object with the following fields:\n"
        '  "summary": brief overall description,\n'
        '  "key_detected": musical key (e.g. "C major"),\n'
        '  "tempo_estimate": BPM estimate as string,\n'
        '  "genre_tags": list of genre labels,\n'
        '  "instruments_detected": list of instrument names,\n'
        '  "segments": list of {timestamp, description, emotion},\n'
        '  "mix_feedback": actionable mix/mastering notes.\n'
        "Be precise with timestamps (MM:SS format)."
    )
