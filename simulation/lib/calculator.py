"""Wrapper around Adaptive Cover Pro calculation engine."""

import logging
import sys
from pathlib import Path
from typing import Any

# Add custom_components to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from custom_components.adaptive_cover_pro.calculation import (
    AdaptiveHorizontalCover,
    AdaptiveTiltCover,
    AdaptiveVerticalCover,
    ClimateCoverState,
    NormalCoverState,
)


class MockHass:
    """Mock Home Assistant object for standalone calculations."""

    def __init__(self, latitude=0.0, longitude=0.0, timezone="UTC"):
        """Initialize mock."""
        self.states = {}
        self.data = {}
        self.config = type('obj', (object,), {
            'time_zone': timezone,
            'latitude': latitude,
            'longitude': longitude,
            'elevation': 0,
        })()


class MockLogger:
    """Mock logger for standalone calculations."""

    def __init__(self):
        """Initialize mock logger."""
        self.logger = logging.getLogger("simulation")
        self.logger.setLevel(logging.WARNING)  # Suppress debug logs

    def debug(self, msg, *args):
        """Debug log."""
        self.logger.debug(msg, *args)

    def info(self, msg, *args):
        """Info log."""
        self.logger.info(msg, *args)

    def warning(self, msg, *args):
        """Warning log."""
        self.logger.warning(msg, *args)

    def error(self, msg, *args):
        """Error log."""
        self.logger.error(msg, *args)


class CoverCalculator:
    """Wrapper for cover calculation logic."""

    def __init__(self):
        """Initialize calculator."""
        self.hass = None  # Will be created per-config
        self.logger = MockLogger()

    def create_cover(self, config: dict[str, Any], solar_azi: float, solar_elev: float):
        """
        Create appropriate cover instance based on configuration.

        Args:
            config: Cover configuration dictionary
            solar_azi: Solar azimuth in degrees
            solar_elev: Solar elevation in degrees

        Returns:
            Cover instance (Vertical, Horizontal, or Tilt)
        """
        cover_type = config["cover_type"]

        # Create MockHass with location from config
        hass = MockHass(
            latitude=config.get("latitude", 0.0),
            longitude=config.get("longitude", 0.0),
            timezone=config.get("timezone", "UTC"),
        )

        # Common parameters (must match AdaptiveGeneralCover dataclass order)
        common_params = [
            hass,
            self.logger,
            solar_azi,
            solar_elev,
            config.get("sunset_position", 0),
            config.get("sunset_offset", 0),
            config.get("sunrise_offset", 0),
            config.get("timezone", "UTC"),
            config.get("fov_left", 90),
            config.get("fov_right", 90),
            config.get("window_azimuth", 180),
            config.get("default_position", 60),
            config.get("max_position", 100),
            config.get("min_position", 0),
            config.get("enable_max_position", False),
            config.get("enable_min_position", False),
            config.get("blind_spot_left"),
            config.get("blind_spot_right"),
            config.get("blind_spot_elevation"),
            config.get("enable_blind_spot", False),
            config.get("min_elevation", 0),
            config.get("max_elevation", 90),
        ]

        # Type-specific parameters
        if cover_type == "cover_blind":
            vertical_params = [
                config.get("distance", 0.5),
                config.get("window_height", 2.1),
            ]
            return AdaptiveVerticalCover(*common_params, *vertical_params)

        elif cover_type == "cover_awning":
            vertical_params = [
                config.get("distance", 0.5),
                config.get("window_height", 2.1),
            ]
            horizontal_params = [
                config.get("length", 2.1),
                config.get("angle", 0),
            ]
            return AdaptiveHorizontalCover(*common_params, *vertical_params, *horizontal_params)

        elif cover_type == "cover_tilt":
            tilt_params = [
                config.get("slat_depth", 3),
                config.get("slat_distance", 2),
                config.get("inverse_state", False),
                config.get("tilt_mode", "mode2"),
            ]
            return AdaptiveTiltCover(*common_params, *tilt_params)

        else:
            msg = f"Unknown cover type: {cover_type}"
            raise ValueError(msg)

    def calculate_position(
        self,
        config: dict[str, Any],
        solar_azi: float,
        solar_elev: float,
    ) -> dict[str, Any]:
        """
        Calculate cover position for given solar position.

        Args:
            config: Cover configuration dictionary
            solar_azi: Solar azimuth in degrees
            solar_elev: Solar elevation in degrees

        Returns:
            Dictionary with position, control_method, sun_in_window
        """
        cover = self.create_cover(config, solar_azi, solar_elev)

        # Get state object and calculate position
        if config.get("climate_mode", False):
            state = ClimateCoverState(cover)
            position = state.get_state()
            control_method = "climate"
        else:
            state = NormalCoverState(cover)
            position = state.get_state()
            control_method = "normal"

        return {
            "position": position,
            "control_method": control_method,
            "sun_in_window": cover.direct_sun_valid,
        }
