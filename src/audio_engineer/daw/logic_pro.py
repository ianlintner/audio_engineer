"""Logic Pro backend (Tier 2) - macOS AppleScript integration.

NOT MVP - planned for Phase 2.
"""
from __future__ import annotations

import platform
from pathlib import Path

from ..core.models import RenderConfig
from .base import AudioFormat, DAWBackend, DAWInfo

_LOGIC_PRO_PATH = Path("/Applications/Logic Pro.app")


class LogicProBackend(DAWBackend):
    """Tier 2 backend for Logic Pro via AppleScript (macOS only).

    Not yet implemented - planned for Phase 2.
    """

    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        raise NotImplementedError("Logic Pro integration planned for Phase 2")

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and _LOGIC_PRO_PATH.exists()

    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.WAV, AudioFormat.AIFF, AudioFormat.MP3]

    def get_info(self) -> DAWInfo:
        return DAWInfo(
            name="Logic Pro",
            tier=2,
            platform="darwin",
            available=self.is_available(),
        )
