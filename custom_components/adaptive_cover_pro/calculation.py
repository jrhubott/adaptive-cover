"""Generate values for all types of covers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import cast

import numpy as np
import pandas as pd
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import state_attr
from numpy import cos, sin, tan
from numpy import radians as rad

from .config_context_adapter import ConfigContextAdapter
from .const import (
    CLIMATE_DEFAULT_TILT_ANGLE,
    CLIMATE_SUMMER_TILT_ANGLE,
    POSITION_CLOSED,
    WINDOW_DEPTH_GAMMA_THRESHOLD,
)
from .enums import CoverType, TiltMode
from .geometry import EdgeCaseHandler, SafetyMarginCalculator
from .helpers import get_domain, get_safe_state
from .position_utils import PositionConverter
from .sun import SunData


@dataclass
class AdaptiveGeneralCover(ABC):
    """Collect common data."""

    hass: HomeAssistant
    logger: ConfigContextAdapter
    sol_azi: float
    sol_elev: float
    sunset_pos: int
    sunset_off: int
    sunrise_off: int
    timezone: str
    fov_left: int
    fov_right: int
    win_azi: int
    h_def: int
    max_pos: int
    min_pos: int
    max_pos_bool: bool
    min_pos_bool: bool
    blind_spot_left: int
    blind_spot_right: int
    blind_spot_elevation: int
    blind_spot_on: bool
    min_elevation: int
    max_elevation: int
    sun_data: SunData = field(init=False)

    def __post_init__(self) -> None:
        """Add solar data to dataset."""
        self.sun_data = SunData(self.timezone, self.hass)

    def solar_times(self) -> tuple[datetime | None, datetime | None]:
        """Determine start/end times."""
        df_today = pd.DataFrame(
            {
                "azimuth": self.sun_data.solar_azimuth,
                "elevation": self.sun_data.solar_elevation,
            }
        )
        solpos = df_today.set_index(self.sun_data.times)

        alpha = solpos["azimuth"]
        frame = (
            (alpha - self.azi_min_abs) % 360
            <= (self.azi_max_abs - self.azi_min_abs) % 360
        ) & (solpos["elevation"] > 0)

        if solpos[frame].empty:
            return None, None
        else:
            return (
                solpos[frame].index[0].to_pydatetime(),
                solpos[frame].index[-1].to_pydatetime(),
            )

    @property
    def _get_azimuth_edges(self) -> tuple[int, int]:
        """Calculate azimuth edges."""
        return (self.azi_min_abs, self.azi_max_abs)

    @property
    def is_sun_in_blind_spot(self) -> bool:
        """Check if sun is in blind spot."""
        if (
            self.blind_spot_left is not None
            and self.blind_spot_right is not None
            and self.blind_spot_on
        ):
            left_edge = self.fov_left - self.blind_spot_left
            right_edge = self.fov_left - self.blind_spot_right
            blindspot = (self.gamma <= left_edge) & (self.gamma >= right_edge)
            if self.blind_spot_elevation is not None:
                blindspot = blindspot & (self.sol_elev <= self.blind_spot_elevation)
            self.logger.debug("Is sun in blind spot? %s", blindspot)
            return blindspot
        return False

    @property
    def azi_min_abs(self) -> int:
        """Calculate min azimuth."""
        azi_min_abs = (self.win_azi - self.fov_left + 360) % 360
        return azi_min_abs

    @property
    def azi_max_abs(self) -> int:
        """Calculate max azimuth."""
        azi_max_abs = (self.win_azi + self.fov_right + 360) % 360
        return azi_max_abs

    @property
    def gamma(self) -> float:
        """Calculate Gamma."""
        # surface solar azimuth
        gamma = (self.win_azi - self.sol_azi + 180) % 360 - 180
        return gamma

    @property
    def valid_elevation(self) -> bool:
        """Check if elevation is within range."""
        if self.min_elevation is None and self.max_elevation is None:
            return self.sol_elev >= 0
        if self.min_elevation is None:
            return self.sol_elev <= self.max_elevation
        if self.max_elevation is None:
            return self.sol_elev >= self.min_elevation
        within_range = self.min_elevation <= self.sol_elev <= self.max_elevation
        self.logger.debug("elevation within range? %s", within_range)
        return within_range

    @property
    def valid(self) -> bool:
        """Determine if sun is in front of window."""
        # Use configured FOV values directly without clipping
        azi_min = self.fov_left
        azi_max = self.fov_right

        # valid sun positions are those within the blind's azimuth range and above the horizon (FOV)
        valid = (
            (self.gamma < azi_min) & (self.gamma > -azi_max) & (self.valid_elevation)
        )
        self.logger.debug("Sun in front of window (ignoring blindspot)? %s", valid)
        return valid

    @property
    def sunset_valid(self) -> bool:
        """Determine if it is after sunset plus offset."""
        sunset = self.sun_data.sunset().replace(tzinfo=None)
        sunrise = self.sun_data.sunrise().replace(tzinfo=None)
        after_sunset = datetime.utcnow() > (sunset + timedelta(minutes=self.sunset_off))
        before_sunrise = datetime.utcnow() < (
            sunrise + timedelta(minutes=self.sunrise_off)
        )
        self.logger.debug(
            "After sunset plus offset? %s", (after_sunset or before_sunrise)
        )
        return after_sunset or before_sunrise

    @property
    def default(self) -> float:
        """Change default position at sunset."""
        default = self.h_def
        if self.sunset_valid:
            default = self.sunset_pos
        return default

    def fov(self) -> list[int]:
        """Return field of view."""
        return [self.azi_min_abs, self.azi_max_abs]

    @property
    def apply_min_position(self) -> bool:
        """Check if min position is applied."""
        if self.min_pos is not None and self.min_pos != 0:
            if self.min_pos_bool:
                return self.direct_sun_valid
            return True
        return False

    @property
    def apply_max_position(self) -> bool:
        """Check if max position is applied."""
        if self.max_pos is not None and self.max_pos != 100:
            if self.max_pos_bool:
                return self.direct_sun_valid
            return True
        return False

    @property
    def direct_sun_valid(self) -> bool:
        """Check if sun is directly in front of window."""
        return (self.valid) & (not self.sunset_valid) & (not self.is_sun_in_blind_spot)

    @abstractmethod
    def calculate_position(self) -> float:
        """Calculate the position of the blind."""

    @abstractmethod
    def calculate_percentage(self) -> int:
        """Calculate percentage from position."""


@dataclass
class NormalCoverState:
    """Compute state for normal operation."""

    cover: AdaptiveGeneralCover

    def get_state(self) -> int:
        """Return state."""
        self.cover.logger.debug("Determining normal position")
        dsv = self.cover.direct_sun_valid
        self.cover.logger.debug(
            "Sun directly in front of window & before sunset + offset? %s", dsv
        )
        if dsv:
            state = self.cover.calculate_percentage()
            self.cover.logger.debug(
                "Yes sun in window: using calculated percentage (%s)", state
            )
        else:
            state = self.cover.default
            self.cover.logger.debug("No sun in window: using default value (%s)", state)

        # Apply position limits using utility
        return PositionConverter.apply_limits(
            int(state),
            self.cover.min_pos,
            self.cover.max_pos,
            self.cover.apply_min_position,
            self.cover.apply_max_position,
            dsv,
        )


@dataclass
class ClimateCoverData:
    """Fetch additional data."""

    hass: HomeAssistant
    logger: ConfigContextAdapter
    temp_entity: str
    temp_low: float
    temp_high: float
    presence_entity: str
    weather_entity: str
    weather_condition: list[str]
    outside_entity: str
    temp_switch: bool
    blind_type: str
    transparent_blind: bool
    lux_entity: str
    irradiance_entity: str
    lux_threshold: int
    irradiance_threshold: int
    temp_summer_outside: float
    _use_lux: bool
    _use_irradiance: bool

    @property
    def outside_temperature(self) -> str | float | None:
        """Get outside temperature."""
        temp = None
        if self.outside_entity:
            temp = get_safe_state(
                self.hass,
                self.outside_entity,
            )
        elif self.weather_entity:
            temp = state_attr(self.hass, self.weather_entity, "temperature")
        return temp

    @property
    def inside_temperature(self) -> str | float | None:
        """Get inside temp from entity."""
        if self.temp_entity is not None:
            if get_domain(self.temp_entity) != "climate":
                temp = get_safe_state(
                    self.hass,
                    self.temp_entity,
                )
            else:
                temp = state_attr(self.hass, self.temp_entity, "current_temperature")
            return temp
        return None

    @property
    def get_current_temperature(self) -> float | None:
        """Get temperature."""
        if self.temp_switch:
            if self.outside_temperature is not None:
                return float(self.outside_temperature)
        if self.inside_temperature is not None:
            return float(self.inside_temperature)
        return None

    @property
    def is_presence(self) -> bool:
        """Checks if people are present."""
        presence = None
        if self.presence_entity is not None:
            presence = get_safe_state(self.hass, self.presence_entity)
        # set to true if no sensor is defined
        if presence is not None:
            domain = get_domain(self.presence_entity)
            if domain == "device_tracker":
                return presence == "home"
            if domain == "zone":
                return int(presence) > 0
            if domain in ["binary_sensor", "input_boolean"]:
                return presence == "on"
        return True

    @property
    def is_winter(self) -> bool:
        """Check if temperature is below threshold."""
        if self.temp_low is not None and self.get_current_temperature is not None:
            is_it = self.get_current_temperature < self.temp_low
        else:
            is_it = False

        self.logger.debug(
            "is_winter(): current_temperature < temp_low: %s < %s = %s",
            self.get_current_temperature,
            self.temp_low,
            is_it,
        )
        return is_it

    @property
    def outside_high(self) -> bool:
        """Check if outdoor temperature is above threshold."""
        if self.temp_summer_outside is not None:
            temp = self.outside_temperature
            if temp is not None:
                return float(temp) > self.temp_summer_outside
        return True

    @property
    def is_summer(self) -> bool:
        """Check if temperature is over threshold."""
        if self.temp_high is not None and self.get_current_temperature is not None:
            is_it = self.get_current_temperature > self.temp_high and self.outside_high
        else:
            is_it = False

        self.logger.debug(
            "is_summer(): current_temp > temp_high and outside_high?: %s > %s and %s = %s",
            self.get_current_temperature,
            self.temp_high,
            self.outside_high,
            is_it,
        )
        return is_it

    @property
    def is_sunny(self) -> bool:
        """Check if condition can contain radiation in winter."""
        weather_state = None
        if self.weather_entity is not None:
            weather_state = get_safe_state(self.hass, self.weather_entity)
        else:
            self.logger.debug("is_sunny(): No weather entity defined")
            return True
        if self.weather_condition is not None:
            matches = weather_state in self.weather_condition
            self.logger.debug("is_sunny(): Weather: %s = %s", weather_state, matches)
            return matches
        # No weather condition defined, default to sunny
        self.logger.debug("is_sunny(): No weather condition defined")
        return True

    @property
    def lux(self) -> bool:
        """Get lux value and compare to threshold."""
        if not self._use_lux:
            return False
        if self.lux_entity is not None and self.lux_threshold is not None:
            value = get_safe_state(self.hass, self.lux_entity)
            if value is None:
                return False
            return float(value) <= self.lux_threshold
        return False

    @property
    def irradiance(self) -> bool:
        """Get irradiance value and compare to threshold."""
        if not self._use_irradiance:
            return False
        if self.irradiance_entity is not None and self.irradiance_threshold is not None:
            value = get_safe_state(self.hass, self.irradiance_entity)
            if value is None:
                return False
            return float(value) <= self.irradiance_threshold
        return False


@dataclass
class ClimateCoverState(NormalCoverState):
    """Compute state for climate control operation."""

    climate_data: ClimateCoverData

    def normal_type_cover(self) -> int:
        """Determine state for horizontal and vertical covers."""
        self.cover.logger.debug("Is presence? %s", self.climate_data.is_presence)

        if self.climate_data.is_presence:
            return self.normal_with_presence()

        return self.normal_without_presence()

    def normal_with_presence(self) -> int:
        """Determine state for horizontal and vertical covers with occupants."""

        is_summer = self.climate_data.is_summer

        # Priority 1: Winter mode for solar heating
        # If it's winter and sun is in front, open fully regardless of light conditions
        if self.climate_data.is_winter and self.cover.valid:
            self.cover.logger.debug(
                "n_w_p(): Winter mode active with sun in window = use 100 for solar heating"
            )
            return 100

        # Priority 2: Low light or non-sunny conditions
        # If it's not summer and light is low or weather is not sunny, use default
        if not is_summer and (
            self.climate_data.lux
            or self.climate_data.irradiance
            or not self.climate_data.is_sunny
        ):
            self.cover.logger.debug(
                "n_w_p(): Low light or not sunny = use default position"
            )
            return round(self.cover.default)

        # Priority 3: Summer with transparent blinds
        if is_summer and self.climate_data.transparent_blind:
            self.cover.logger.debug(
                "n_w_p(): Summer with transparent blind = close to 0"
            )
            return 0

        # Priority 4: Normal glare calculation
        self.cover.logger.debug("n_w_p(): Use calculated position for glare control")
        return super().get_state()

    def normal_without_presence(self) -> int:
        """Determine state for horizontal and vertical covers without occupants."""
        if self.cover.valid:
            if self.climate_data.is_summer:
                return 0
            if self.climate_data.is_winter:
                return 100
        return round(self.cover.default)

    def tilt_with_presence(self, degrees: int) -> int:
        """Determine state for tilted blinds with occupants."""

        # Priority 1: Climate-based decisions when sun is valid
        if self.cover.valid:
            # Summer: partial closure for heat blocking
            if self.climate_data.is_summer:
                self.cover.logger.debug(
                    "tilt_w_p(): Summer mode = %s degrees", CLIMATE_SUMMER_TILT_ANGLE
                )
                return round((CLIMATE_SUMMER_TILT_ANGLE / degrees) * 100)

            # Winter: Use calculated position for optimal light/heat
            if self.climate_data.is_winter:
                self.cover.logger.debug(
                    "tilt_w_p(): Winter mode = use calculated position"
                )
                return super().get_state()

            # Low light or not sunny: Use calculated position
            if (
                self.climate_data.lux
                or self.climate_data.irradiance
                or not self.climate_data.is_sunny
            ):
                self.cover.logger.debug(
                    "tilt_w_p(): Low light or not sunny = use calculated position"
                )
                return super().get_state()

        # Default: mostly open for natural light
        self.cover.logger.debug(
            "tilt_w_p(): Default = %s degrees", CLIMATE_DEFAULT_TILT_ANGLE
        )
        return round((CLIMATE_DEFAULT_TILT_ANGLE / degrees) * 100)

    def tilt_without_presence(self, degrees: int) -> int:
        """Determine state for tilted blinds without occupants."""
        tilt_cover = cast(AdaptiveTiltCover, self.cover)
        beta = np.rad2deg(tilt_cover.beta)
        if tilt_cover.valid:
            if self.climate_data.is_summer:
                # block out all light in summer
                return POSITION_CLOSED
            # Check for MODE2 (handles both string and enum)
            is_mode2 = (
                tilt_cover.mode == TiltMode.MODE2
                or tilt_cover.mode == TiltMode.MODE2.value
            )
            if self.climate_data.is_winter and is_mode2:
                # parallel to sun beams, not possible with single direction
                return round((beta + 90) / degrees * 100)
            return round((CLIMATE_DEFAULT_TILT_ANGLE / degrees) * 100)
        return super().get_state()

    def tilt_state(self) -> int:
        """Add tilt specific controls."""
        tilt_cover = cast(AdaptiveTiltCover, self.cover)
        # Check for MODE2 (handles both string and enum)
        is_mode2 = (
            tilt_cover.mode == TiltMode.MODE2 or tilt_cover.mode == TiltMode.MODE2.value
        )
        degrees = TiltMode.MODE2.max_degrees if is_mode2 else TiltMode.MODE1.max_degrees
        if self.climate_data.is_presence:
            return self.tilt_with_presence(degrees)
        return self.tilt_without_presence(degrees)

    def get_state(self) -> int:
        """Return state."""
        result = self.normal_type_cover()
        # Check if cover type is tilt (handles both string and enum)
        is_tilt = (
            self.climate_data.blind_type == CoverType.TILT
            or self.climate_data.blind_type == CoverType.TILT.value
        )
        if is_tilt:
            result = self.tilt_state()

        # Apply position limits using utility
        final_result = PositionConverter.apply_limits(
            result,
            self.cover.min_pos,
            self.cover.max_pos,
            self.cover.apply_min_position,
            self.cover.apply_max_position,
            self.cover.direct_sun_valid,
        )

        if final_result != result:
            self.cover.logger.debug(
                "Climate state: Position limit applied (%s -> %s)", result, final_result
            )

        return final_result


@dataclass
class AdaptiveVerticalCover(AdaptiveGeneralCover):
    """Calculate state for Vertical blinds."""

    distance: float
    h_win: float
    window_depth: float = (
        0.0  # Window reveal/frame depth (meters), default 0 = disabled
    )

    def _calculate_safety_margin(self, gamma: float, sol_elev: float) -> float:
        """Calculate angle-dependent safety margin multiplier (≥1.0).

        Delegates to SafetyMarginCalculator utility class.

        Args:
            gamma: Surface solar azimuth in degrees (-180 to 180)
            sol_elev: Sun elevation angle in degrees (0-90)

        Returns:
            Safety margin multiplier (1.0 to 1.45)

        """
        return SafetyMarginCalculator.calculate(gamma, sol_elev)

    def _handle_edge_cases(self) -> tuple[bool, float]:
        """Handle extreme angles with safe fallbacks.

        Delegates to EdgeCaseHandler utility class.

        Returns:
            Tuple of (is_edge_case: bool, position: float)
            - is_edge_case: True if edge case detected
            - position: Safe fallback position (only valid if is_edge_case=True)

        """
        return EdgeCaseHandler.check_and_handle(
            self.sol_elev, self.gamma, self.distance, self.h_win
        )

    def calculate_position(self) -> float:
        """Calculate blind height with enhanced geometric accuracy.

        Uses improved geometric model with:
        - Edge case handling for extreme sun angles
        - Angle-dependent safety margins for better sun blocking
        - Optional window depth consideration for advanced accuracy
        - Smooth transitions across all angles

        Returns:
            Blind height in meters (0 to h_win)

        """
        # Check edge cases first
        is_edge_case, edge_position = self._handle_edge_cases()
        if is_edge_case:
            return edge_position

        # Account for window depth at angles (creates additional shadow)
        effective_distance = self.distance
        if self.window_depth > 0 and abs(self.gamma) > WINDOW_DEPTH_GAMMA_THRESHOLD:
            # At angles, window depth creates additional horizontal offset
            depth_contribution = self.window_depth * sin(rad(abs(self.gamma)))
            effective_distance += depth_contribution

        # Base calculation: project glare zone to vertical blind height
        path_length = effective_distance / cos(rad(self.gamma))
        base_height = path_length * tan(rad(self.sol_elev))

        # Apply safety margin for extreme angles
        safety_margin = self._calculate_safety_margin(self.gamma, self.sol_elev)
        adjusted_height = base_height * safety_margin

        return np.clip(adjusted_height, 0, self.h_win)

    def calculate_percentage(self) -> float:
        """Convert blind height to percentage or default value."""
        position = self.calculate_position()
        self.logger.debug(
            "Converting height to percentage: %s / %s * 100", position, self.h_win
        )
        return PositionConverter.to_percentage(position, self.h_win)


@dataclass
class AdaptiveHorizontalCover(AdaptiveVerticalCover):
    """Calculate state for Horizontal blinds."""

    awn_length: float = 2.0  # Default awning length (meters)
    awn_angle: float = 0.0  # Default awning angle (degrees)

    def calculate_position(self) -> float:
        """Calculate awn length from blind height."""
        awn_angle = 90 - self.awn_angle
        a_angle = 90 - self.sol_elev
        c_angle = 180 - awn_angle - a_angle

        vertical_position = super().calculate_position()
        length = ((self.h_win - vertical_position) * sin(rad(a_angle))) / sin(
            rad(c_angle)
        )
        # return np.clip(length, 0, self.awn_length)
        return length

    def calculate_percentage(self) -> float:
        """Convert awn length to percentage or default value."""
        return PositionConverter.to_percentage(
            self.calculate_position(), self.awn_length
        )


@dataclass
class AdaptiveTiltCover(AdaptiveGeneralCover):
    """Calculate state for tilted blinds."""

    slat_distance: float
    depth: float
    mode: TiltMode | str  # Accept both TiltMode enum and string for backward compatibility

    @property
    def beta(self) -> float:
        """Calculate beta."""
        beta = np.arctan(tan(rad(self.sol_elev)) / cos(rad(self.gamma)))
        return beta

    def calculate_position(self) -> float:
        """Calculate position of venetian blinds.

        https://www.mdpi.com/1996-1073/13/7/1731
        """
        beta = self.beta

        slat = 2 * np.arctan(
            (
                tan(beta)
                + np.sqrt(
                    (tan(beta) ** 2) - ((self.slat_distance / self.depth) ** 2) + 1
                )
            )
            / (1 + self.slat_distance / self.depth)
        )
        result = np.rad2deg(slat)

        return result

    def calculate_percentage(self) -> float:
        """Convert tilt angle to percentages or default value."""
        # 0 degrees is closed, 90 degrees is open (mode1), 180 degrees is closed (mode2)
        position = self.calculate_position()

        # Handle both string and TiltMode enum for backward compatibility
        if isinstance(self.mode, TiltMode):
            max_degrees = self.mode.max_degrees
        else:
            # Convert string to TiltMode
            mode_enum = TiltMode(self.mode)
            max_degrees = mode_enum.max_degrees

        return PositionConverter.to_percentage(position, max_degrees)
