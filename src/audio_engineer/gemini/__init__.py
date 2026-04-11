"""Google Gemini AI integration for advanced audio capabilities.

Provides music generation (Lyria 3), audio analysis, text-to-speech,
and Gemini-as-LLM-provider for agent reasoning.
"""

from .client import GeminiClient, get_gemini_client
from .music_gen import MusicGenerationAgent
from .audio_analysis import AudioAnalysisAgent
from .tts import TTSAgent

__all__ = [
    "GeminiClient",
    "get_gemini_client",
    "MusicGenerationAgent",
    "AudioAnalysisAgent",
    "TTSAgent",
]
