"""Musician agents for AI Music Studio."""

from .drummer import DrummerAgent
from .bassist import BassistAgent
from .guitarist import GuitaristAgent
from .keyboardist import KeyboardistAgent
from .strings import StringsAgent
from .brass import BrassAgent
from .synth import SynthAgent
from .percussion import PercussionAgent
from .lead_guitar import LeadGuitarAgent

__all__ = [
    "DrummerAgent",
    "BassistAgent",
    "GuitaristAgent",
    "KeyboardistAgent",
    "StringsAgent",
    "BrassAgent",
    "SynthAgent",
    "PercussionAgent",
    "LeadGuitarAgent",
]
