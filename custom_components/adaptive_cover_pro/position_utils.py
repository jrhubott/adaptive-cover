"""Position calculation utilities for Adaptive Cover Pro."""

from __future__ import annotations

import numpy as np


class PositionConverter:
    """Handles position-to-percentage conversions and limit application."""

    @staticmethod
    def to_percentage(position: float, max_value: float) -> int:
        """Convert position to percentage.

        Args:
            position: Position value (height, length, angle, etc.)
            max_value: Maximum possible value (window height, awning length, max degrees)

        Returns:
            Percentage value (0-100), rounded to nearest integer

        """
        percentage = (position / max_value) * 100
        return round(percentage)

    @staticmethod
    def apply_limits(
        value: int,
        min_pos: int | None,
        max_pos: int | None,
        apply_min: bool,
        apply_max: bool,
        sun_valid: bool,
    ) -> int:
        """Apply min/max position limits.

        Args:
            value: Position value to constrain (0-100)
            min_pos: Minimum position limit
            max_pos: Maximum position limit
            apply_min: Whether min limit applies (when False, always apply)
            apply_max: Whether max limit applies (when False, always apply)
            sun_valid: Whether sun is in valid position (direct sunlight)

        Returns:
            Constrained position value (0-100)

        Note:
            When apply_min/apply_max is False, limits are always enforced.
            When True, limits only apply during direct sun tracking (sun_valid=True).

        """
        # First clip to valid range
        result = np.clip(value, 0, 100)

        # Apply max position limit
        if max_pos is not None and max_pos != 100:
            # Always apply if enable flag is False, or if sun is valid
            if not apply_max or sun_valid:
                result = min(result, max_pos)

        # Apply min position limit
        if min_pos is not None and min_pos != 0:
            # Always apply if enable flag is False, or if sun is valid
            if not apply_min or sun_valid:
                result = max(result, min_pos)

        return int(result)
