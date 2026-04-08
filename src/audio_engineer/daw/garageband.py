"""GarageBand backend (Tier 2) - macOS AppleScript integration.

NOT MVP - planned for Phase 2.

AppleScript template for future implementation:
    tell application "GarageBand"
        activate
        delay 2
        open POSIX file "{midi_path}"
        delay 5
        -- Export via Share > Export Song to Disk
        tell application "System Events"
            tell process "GarageBand"
                click menu item "Export Song to Disk..."
                    of menu "Share" of menu bar 1
                delay 2
                -- Set output path and format in the save dialog
                keystroke "g" using {{command down, shift down}}
                delay 1
                keystroke "{output_path}"
                delay 0.5
                keystroke return
            end tell
        end tell
    end tell
"""
from __future__ import annotations

import platform
from pathlib import Path

from ..core.models import RenderConfig
from .base import AudioFormat, DAWBackend, DAWInfo

_GARAGEBAND_PATH = Path("/Applications/GarageBand.app")


class GarageBandBackend(DAWBackend):
    """Tier 2 backend for GarageBand via AppleScript (macOS only).

    Not yet implemented - planned for Phase 2.
    """

    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        raise NotImplementedError("GarageBand integration planned for Phase 2")

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and _GARAGEBAND_PATH.exists()

    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.WAV, AudioFormat.AIFF, AudioFormat.MP3]

    def get_info(self) -> DAWInfo:
        return DAWInfo(
            name="GarageBand",
            tier=2,
            platform="darwin",
            available=self.is_available(),
        )
