"""Gemini client wrapper — singleton access to the google-genai SDK."""
from __future__ import annotations

import logging
from typing import Optional

from audio_engineer.config.settings import get_settings

logger = logging.getLogger(__name__)

_client_instance = None


class GeminiClient:
    """Thin wrapper around ``google.genai.Client`` with lazy initialisation."""

    def __init__(self, api_key: Optional[str] = None):
        try:
            from google import genai  # noqa: F811
        except ImportError as exc:
            raise ImportError(
                "google-genai package is required for Gemini integration. "
                "Install with: pip install 'audio-engineer[gemini]'"
            ) from exc

        resolved_key = api_key or get_settings().gemini_api_key
        if not resolved_key:
            raise ValueError(
                "Gemini API key is required. Set AUDIO_ENGINEER_GEMINI_API_KEY "
                "or pass api_key explicitly."
            )

        self._genai = genai
        self._client = genai.Client(api_key=resolved_key)
        logger.info("Gemini client initialised")

    @property
    def raw(self):
        """Access the underlying ``genai.Client`` for advanced usage."""
        return self._client

    @property
    def types(self):
        """Convenience accessor for ``google.genai.types``."""
        if hasattr(self, "_types") and self._types is not None:
            return self._types
        from google.genai import types as _types
        return _types

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def generate_content(self, model: str, contents, **kwargs):
        """Proxy to ``client.models.generate_content``."""
        return self._client.models.generate_content(
            model=model, contents=contents, **kwargs
        )

    def close(self):
        """Release underlying HTTP resources."""
        try:
            self._client.close()
        except Exception:
            pass


def get_gemini_client(api_key: Optional[str] = None) -> GeminiClient:
    """Return a module-level singleton ``GeminiClient``."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GeminiClient(api_key=api_key)
    return _client_instance
