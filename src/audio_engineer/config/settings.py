"""Application settings via pydantic-settings."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class AudioEngineerSettings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "openai"  # openai, anthropic, gemini, local
    llm_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"

    # Audio
    soundfont_path: Optional[str] = None
    default_sample_rate: int = 44100
    audio_format: str = "wav"  # wav, mp3
    mp3_bitrate: str = "192k"
    output_dir: str = "./output"

    # DAW
    preferred_backend: str = "fluidsynth"  # fluidsynth, timidity, export

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "AUDIO_ENGINEER_", "env_file": ".env"}


def get_settings() -> AudioEngineerSettings:
    return AudioEngineerSettings()
