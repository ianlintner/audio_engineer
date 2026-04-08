"""DAW integration layer - backend discovery and audio rendering."""
from .base import AudioFormat, DAWBackend, DAWInfo
from .export import FileExportBackend
from .fluidsynth import FluidSynthBackend
from .timidity import TiMidityBackend
from .garageband import GarageBandBackend
from .logic_pro import LogicProBackend

_BACKENDS: dict[str, type[DAWBackend]] = {
    "export": FileExportBackend,
    "fluidsynth": FluidSynthBackend,
    "timidity": TiMidityBackend,
    "garageband": GarageBandBackend,
    "logic_pro": LogicProBackend,
}


def get_backend(name: str) -> DAWBackend:
    """Create a DAW backend by name.

    Args:
        name: One of 'export', 'fluidsynth', 'timidity', 'garageband', 'logic_pro'.

    Returns:
        An instance of the requested backend.

    Raises:
        ValueError: If the backend name is unknown.
    """
    cls = _BACKENDS.get(name.lower())
    if cls is None:
        available = ", ".join(sorted(_BACKENDS))
        raise ValueError(f"Unknown backend {name!r}. Available: {available}")
    return cls()


__all__ = [
    "AudioFormat",
    "DAWBackend",
    "DAWInfo",
    "FileExportBackend",
    "FluidSynthBackend",
    "TiMidityBackend",
    "GarageBandBackend",
    "LogicProBackend",
    "get_backend",
]
