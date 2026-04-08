"""Rhythm and groove utilities."""

import random
from .constants import TICKS_PER_BEAT


class Groove:
    """Manages swing and groove feel."""

    def __init__(self, swing_amount: float = 0.0, push_pull: float = 0.0):
        """
        swing_amount: 0.0 = straight, 1.0 = full triplet swing
        push_pull: negative = behind the beat, positive = ahead
        """
        self.swing_amount = max(0.0, min(1.0, swing_amount))
        self.push_pull = max(-0.5, min(0.5, push_pull))

    def apply(self, tick: int, beat_position: float) -> int:
        """Apply groove to a tick position."""
        # Apply swing to offbeat 8th notes
        is_offbeat = (beat_position * 2) % 2 == 1
        offset = 0
        if is_offbeat and self.swing_amount > 0:
            swing_ticks = int(TICKS_PER_BEAT * self.swing_amount * 0.33)
            offset += swing_ticks
        # Apply push/pull
        offset += int(TICKS_PER_BEAT * self.push_pull * 0.1)
        return tick + offset


def humanize_timing(tick: int, max_deviation_ticks: int = 10) -> int:
    """Add human-like timing variation."""
    return tick + random.randint(-max_deviation_ticks, max_deviation_ticks)


def humanize_velocity(velocity: int, max_deviation: int = 8) -> int:
    """Add human-like velocity variation."""
    v = velocity + random.randint(-max_deviation, max_deviation)
    return max(1, min(127, v))
