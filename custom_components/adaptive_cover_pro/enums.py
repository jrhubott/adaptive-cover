"""Enums for Adaptive Cover Pro integration."""

from enum import Enum


class CoverType(str, Enum):
    """Cover type enumeration."""

    BLIND = "cover_blind"
    AWNING = "cover_awning"
    TILT = "cover_tilt"

    @property
    def display_name(self) -> str:
        """Return human-readable display name."""
        return {
            self.BLIND: "Vertical Cover",
            self.AWNING: "Horizontal Cover",
            self.TILT: "Tilt Cover",
        }[self]


class TiltMode(str, Enum):
    """Tilt mode enumeration for venetian blinds."""

    MODE1 = "mode1"  # Single direction (0-90°)
    MODE2 = "mode2"  # Bi-directional (0-180°)

    @property
    def max_degrees(self) -> int:
        """Return maximum degrees for this mode."""
        return 90 if self == self.MODE1 else 180


class TemperatureSource(Enum):
    """Temperature source for climate mode."""

    INSIDE = "inside"
    OUTSIDE = "outside"


class PresenceDomain(str, Enum):
    """Supported presence entity domains."""

    DEVICE_TRACKER = "device_tracker"
    ZONE = "zone"
    BINARY_SENSOR = "binary_sensor"
    INPUT_BOOLEAN = "input_boolean"


class ClimateStrategy(Enum):
    """Climate control strategies."""

    WINTER_HEATING = "winter_heating"  # Open for solar heating
    SUMMER_COOLING = "summer_cooling"  # Close for heat blocking
    LOW_LIGHT = "low_light"  # Use default position
    GLARE_CONTROL = "glare_control"  # Use calculated position


class ControlState(str, Enum):
    """Control status states for diagnostic sensor."""

    ACTIVE = "active"
    OUTSIDE_TIME_WINDOW = "outside_time_window"
    POSITION_DELTA_TOO_SMALL = "position_delta_too_small"
    TIME_DELTA_TOO_SMALL = "time_delta_too_small"
    MANUAL_OVERRIDE = "manual_override"
    AUTOMATIC_CONTROL_OFF = "automatic_control_off"
    SUN_NOT_VISIBLE = "sun_not_visible"
