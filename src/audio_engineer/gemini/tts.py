"""Text-to-Speech via Gemini TTS models."""
from __future__ import annotations

import io
import logging
import wave
from pathlib import Path
from typing import Optional

from audio_engineer.gemini.client import GeminiClient, get_gemini_client

logger = logging.getLogger(__name__)

# TTS models
FAST_TTS_MODEL = "gemini-2.5-flash-preview-tts"
PRO_TTS_MODEL = "gemini-2.5-pro-preview-tts"

# Prebuilt voice names (Gemini TTS)
VOICES = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir",
    "Leda", "Orus", "Aoede", "Callirhoe", "Autonoe",
    "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina",
    "Erinome", "Gacrux", "Laomedeia", "Pulcherrima", "Achernar",
    "Rasalgethi", "Sadachbia", "Sadaltager", "Sulafat", "Vindemiatrix",
    "Zubenelgenubi", "Zubeneschamali",
]

DEFAULT_VOICE = "Kore"


class TTSResult:
    """Container for generated speech audio."""

    def __init__(self, pcm_data: bytes, sample_rate: int = 24000, channels: int = 1):
        self.pcm_data = pcm_data
        self.sample_rate = sample_rate
        self.channels = channels

    @property
    def wav_bytes(self) -> bytes:
        """Return WAV-encoded bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(self.pcm_data)
        return buf.getvalue()

    def save(self, path: str | Path, fmt: str = "wav") -> Path:
        """Write the audio to disk.

        Parameters
        ----------
        path:
            Output file path.
        fmt:
            ``"wav"`` (default) writes standard WAV.
            ``"raw"`` writes raw PCM.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "raw":
            path.write_bytes(self.pcm_data)
        else:
            path.write_bytes(self.wav_bytes)
        logger.info("TTS audio saved to %s (%s)", path, fmt)
        return path


class TTSAgent:
    """Generate speech audio from text using Gemini TTS models.

    Features
    --------
    * Single-speaker synthesis with voice selection
    * Multi-speaker dialogue synthesis
    * Style / pace / accent control via prompt engineering
    * Vocal track generation from song lyrics
    """

    def __init__(
        self,
        client: Optional[GeminiClient] = None,
        model: str = FAST_TTS_MODEL,
        voice: str = DEFAULT_VOICE,
    ):
        self._client = client or get_gemini_client()
        self._model = model
        self._voice = voice

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
    ) -> TTSResult:
        """Synthesise speech from plain text.

        Parameters
        ----------
        text:
            The text to convert to speech.
        voice:
            Voice preset name (e.g. ``"Kore"``, ``"Puck"``).
        model:
            Override the TTS model.
        """
        voice = voice or self._voice
        model = model or self._model
        types = self._client.types

        response = self._client.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice,
                        )
                    )
                ),
            ),
        )

        return self._extract_audio(response)

    def speak_multi(
        self,
        script: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> TTSResult:
        """Synthesise multi-speaker dialogue.

        Parameters
        ----------
        script:
            List of ``{"voice": "Kore", "text": "Hello!"}`` dicts.
        model:
            Override the TTS model.
        """
        model = model or self._model
        types = self._client.types

        speaker_configs = []
        for turn in script:
            speaker_configs.append(
                types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=turn["voice"],
                        )
                    )
                )
            )

        # Build multi-speaker turn content as a combined prompt
        combined_text = "\n".join(
            f'[{turn["voice"]}]: {turn["text"]}' for turn in script
        )

        response = self._client.generate_content(
            model=model,
            contents=combined_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=script[0]["voice"]
                        )
                    )
                ),
            ),
        )

        return self._extract_audio(response)

    def generate_vocal_track(
        self,
        lyrics: str,
        voice: Optional[str] = None,
        style: str = "",
    ) -> TTSResult:
        """Generate a spoken/sung vocal track from lyrics.

        This uses TTS with style direction to create vocal tracks
        that can be layered with MIDI backing tracks.

        Parameters
        ----------
        lyrics:
            Song lyrics (verse/chorus labelled sections work best).
        voice:
            Voice preset.
        style:
            Style direction, e.g. ``"slow, breathy, emotional"``.
        """
        voice = voice or self._voice
        prompt = ""
        if style:
            prompt = f"(Read the following lyrics in a {style} style)\n\n"
        prompt += lyrics

        return self.speak(prompt, voice=voice)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_audio(self, response) -> TTSResult:  # noqa: ANN001
        """Pull raw PCM from the Gemini TTS response."""
        pcm_chunks: list[bytes] = []
        for part in (response.candidates[0].content.parts or []):
            if part.inline_data and part.inline_data.data:
                pcm_chunks.append(part.inline_data.data)

        if not pcm_chunks:
            raise RuntimeError("Gemini TTS returned no audio data")

        return TTSResult(pcm_data=b"".join(pcm_chunks))
