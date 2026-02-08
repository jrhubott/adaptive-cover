"""The Coordinator for Adaptive Cover Pro."""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass
from typing import Any

import numpy as np
import pytz
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
)
from homeassistant.core import (
    Event,
    HomeAssistant,
    State,
    callback,
)

# EventStateChangedData was added in Home Assistant 2024.4+
# For backwards compatibility with older versions
try:
    from homeassistant.core import EventStateChangedData
except ImportError:
    # Fallback for older Home Assistant versions
    EventStateChangedData = dict  # type: ignore[misc,assignment]
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_time_interval,
)
from homeassistant.helpers.template import state_attr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .config_context_adapter import ConfigContextAdapter

from .calculation import (
    AdaptiveHorizontalCover,
    AdaptiveTiltCover,
    AdaptiveVerticalCover,
    ClimateCoverData,
    ClimateCoverState,
    NormalCoverState,
)
from .const import (
    _LOGGER,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CONF_AWNING_ANGLE,
    CONF_AZIMUTH,
    CONF_BLIND_SPOT_ELEVATION,
    CONF_BLIND_SPOT_LEFT,
    CONF_BLIND_SPOT_RIGHT,
    CONF_CLIMATE_MODE,
    CONF_DEFAULT_HEIGHT,
    CONF_DELTA_POSITION,
    CONF_DELTA_TIME,
    CONF_DISTANCE,
    CONF_WINDOW_DEPTH,
    CONF_ENABLE_BLIND_SPOT,
    CONF_ENABLE_DIAGNOSTICS,
    CONF_ENABLE_MAX_POSITION,
    CONF_ENABLE_MIN_POSITION,
    CONF_END_ENTITY,
    CONF_END_TIME,
    CONF_ENTITIES,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_HEIGHT_WIN,
    CONF_INTERP,
    CONF_INTERP_END,
    CONF_INTERP_LIST,
    CONF_INTERP_LIST_NEW,
    CONF_INTERP_START,
    CONF_INVERSE_STATE,
    CONF_IRRADIANCE_ENTITY,
    CONF_IRRADIANCE_THRESHOLD,
    CONF_LENGTH_AWNING,
    CONF_LUX_ENTITY,
    CONF_LUX_THRESHOLD,
    CONF_MANUAL_IGNORE_INTERMEDIATE,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MANUAL_OVERRIDE_RESET,
    CONF_MANUAL_THRESHOLD,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MIN_POSITION,
    CONF_OUTSIDE_THRESHOLD,
    CONF_OUTSIDETEMP_ENTITY,
    CONF_PRESENCE_ENTITY,
    CONF_RETURN_SUNSET,
    CONF_START_ENTITY,
    CONF_START_TIME,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_SUNSET_POS,
    CONF_TEMP_ENTITY,
    CONF_TEMP_HIGH,
    CONF_TEMP_LOW,
    CONF_TILT_DEPTH,
    CONF_TILT_DISTANCE,
    CONF_TILT_MODE,
    CONF_TRANSPARENT_BLIND,
    CONF_WEATHER_ENTITY,
    CONF_WEATHER_STATE,
    CONF_OPEN_CLOSE_THRESHOLD,
    DOMAIN,
    ControlStatus,
    LOGGER,
    MAX_POSITION_RETRIES,
    POSITION_CHECK_INTERVAL_MINUTES,
    POSITION_TOLERANCE_PERCENT,
    COMMAND_GRACE_PERIOD_SECONDS,
    STARTUP_GRACE_PERIOD_SECONDS,
)
from .helpers import (
    get_datetime_from_str,
    get_last_updated,
    get_safe_state,
    check_cover_features,
    get_open_close_state,
)


@dataclass
class StateChangedData:
    """StateChangedData class."""

    entity_id: str
    old_state: State | None
    new_state: State | None


@dataclass
class AdaptiveCoverData:
    """AdaptiveCoverData class."""

    climate_mode_toggle: bool
    states: dict
    attributes: dict
    diagnostics: dict | None = None


class AdaptiveDataUpdateCoordinator(DataUpdateCoordinator[AdaptiveCoverData]):
    """Adaptive cover data update coordinator."""

    config_entry: ConfigEntry

    # Default capabilities for covers when entity not ready
    _DEFAULT_CAPABILITIES = {
        "has_set_position": True,
        "has_set_tilt_position": False,
        "has_open": True,
        "has_close": True,
    }

    def __init__(self, hass: HomeAssistant) -> None:  # noqa: D107
        super().__init__(hass, LOGGER, name=DOMAIN)

        self.logger = ConfigContextAdapter(_LOGGER)
        self.logger.set_config_name(self.config_entry.data.get("name"))
        self._cover_type = self.config_entry.data.get("sensor_type")
        self._climate_mode = self.config_entry.options.get(CONF_CLIMATE_MODE, False)
        self._switch_mode = True if self._climate_mode else False
        self._inverse_state = self.config_entry.options.get(CONF_INVERSE_STATE, False)
        self._use_interpolation = self.config_entry.options.get(CONF_INTERP, False)
        self._track_end_time = self.config_entry.options.get(CONF_RETURN_SUNSET)
        self._temp_toggle = None
        self._automatic_control = None
        self._manual_toggle = None
        self._lux_toggle = None
        self._irradiance_toggle = None
        self._return_to_default_toggle = None
        self._start_time = None
        self._sun_end_time = None
        self._sun_start_time = None
        # self._end_time = None
        self.manual_reset = self.config_entry.options.get(
            CONF_MANUAL_OVERRIDE_RESET, False
        )
        self.manual_duration = self.config_entry.options.get(
            CONF_MANUAL_OVERRIDE_DURATION, {"minutes": 15}
        )
        self.state_change = False
        self.cover_state_change = False
        self.first_refresh = False
        self.timed_refresh = False
        self.climate_state = None
        self.climate_data = None  # Store climate_data for P1 diagnostics
        self.control_method = "intermediate"
        self.state_change_data: StateChangedData | None = None
        self.raw_calculated_position = 0  # Store raw position for diagnostics
        self.manager = AdaptiveCoverManager(self.hass, self.manual_duration, self.logger)
        self.wait_for_target = {}
        self.target_call = {}
        self.ignore_intermediate_states = self.config_entry.options.get(
            CONF_MANUAL_IGNORE_INTERMEDIATE, False
        )
        # Command grace period tracking
        self._command_grace_period_seconds = COMMAND_GRACE_PERIOD_SECONDS
        self._command_timestamps: dict[str, float] = {}
        self._grace_period_tasks: dict[str, asyncio.Task] = {}
        # Startup grace period tracking (global, not per-entity)
        self._startup_grace_period_seconds = STARTUP_GRACE_PERIOD_SECONDS
        self._startup_timestamp: float | None = None
        self._startup_grace_period_task: asyncio.Task | None = None
        self._update_listener = None
        self._scheduled_time = dt.datetime.now()

        self._cached_options = None
        self._open_close_threshold = self.config_entry.options.get(CONF_OPEN_CLOSE_THRESHOLD, 50)

        # Track last cover action for diagnostic sensor
        self.last_cover_action: dict[str, Any] = {
            "entity_id": None,
            "service": None,
            "position": None,
            "calculated_position": None,
            "threshold_used": None,
            "inverse_state_applied": False,
            "timestamp": None,
            "covers_controlled": 0,
        }

        # Position verification tracking
        self._position_check_interval = None  # async_track_time_interval listener
        self._retry_counts: dict[str, int] = {}  # entity_id → retry count
        self._last_verification: dict[str, dt.datetime] = {}  # entity_id → last check time
        self._check_interval_minutes = POSITION_CHECK_INTERVAL_MINUTES
        self._position_tolerance = POSITION_TOLERANCE_PERCENT
        self._max_retries = MAX_POSITION_RETRIES

        # Track entities that have never received commands (for cleaner logging)
        self._never_commanded: set[str] = set()

        # Track time window state transitions (for responsive end time handling)
        self._last_time_window_state: bool | None = None

        # Track sun validity transitions (for responsive sun in-front detection)
        self._last_sun_validity_state: bool | None = None

    def _get_cover_capabilities(self, entity: str) -> dict[str, bool]:
        """Get cover capabilities with fallback to safe defaults.

        Args:
            entity: The cover entity ID

        Returns:
            Dict of capabilities (has_set_position, has_set_tilt_position, has_open, has_close)

        """
        caps = check_cover_features(self.hass, entity)
        if caps is None:
            self.logger.debug("Cover %s not ready, using safe defaults", entity)
            return self._DEFAULT_CAPABILITIES.copy()
        return caps

    @property
    def is_tilt_cover(self) -> bool:
        """Check if this is a tilt cover."""
        return self._cover_type == "cover_tilt"

    @property
    def is_blind_cover(self) -> bool:
        """Check if this is a vertical blind."""
        return self._cover_type == "cover_blind"

    @property
    def is_awning_cover(self) -> bool:
        """Check if this is a horizontal awning."""
        return self._cover_type == "cover_awning"

    def _read_position_with_capabilities(
        self, entity: str, caps: dict[str, bool], state_obj: State | None = None
    ) -> int | None:
        """Read position based on cover type and capabilities.

        Args:
            entity: Entity ID
            caps: Capabilities dict
            state_obj: Optional state object (for event handling)

        Returns:
            Current position or None

        """
        if self.is_tilt_cover:
            if caps.get("has_set_tilt_position", True):
                if state_obj:
                    return state_obj.attributes.get("current_tilt_position")
                return state_attr(self.hass, entity, "current_tilt_position")
        else:
            if caps.get("has_set_position", True):
                if state_obj:
                    return state_obj.attributes.get("current_position")
                return state_attr(self.hass, entity, "current_position")

        return get_open_close_state(self.hass, entity)

    async def async_config_entry_first_refresh(self) -> None:
        """Config entry first refresh."""
        self.first_refresh = True
        await super().async_config_entry_first_refresh()
        self.logger.debug("Config entry first refresh")
        # Start startup grace period to prevent false manual override detection
        self._start_startup_grace_period()
        # Start position verification after first refresh
        self._start_position_verification()

    async def async_timed_refresh(self, event) -> None:
        """Control state at end time."""

        now = dt.datetime.now()
        if self.end_time is not None:
            time = self.end_time
        if self.end_time_entity is not None:
            time = get_safe_state(self.hass, self.end_time_entity)

        self.logger.debug("Checking timed refresh. End time: %s, now: %s", time, now)

        time_check = now - get_datetime_from_str(time)
        if time is not None and (time_check <= dt.timedelta(seconds=5)):
            self.timed_refresh = True
            self.logger.debug("Timed refresh triggered")
            await self.async_refresh()
        else:
            self.logger.debug("Timed refresh, but: not equal to end time")

    async def async_check_entity_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Fetch and process state change event."""
        self.logger.debug("Entity state change")
        self.state_change = True
        await self.async_refresh()

    async def async_check_cover_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Fetch and process state change event."""
        self.logger.debug("Cover state change")
        data = event.data
        if data["old_state"] is None:
            self.logger.debug("Old state is None")
            return
        self.state_change_data = StateChangedData(
            data["entity_id"], data["old_state"], data["new_state"]
        )
        if self.state_change_data.old_state.state != "unknown":
            self.cover_state_change = True
            self.process_entity_state_change()
            await self.async_refresh()
        else:
            self.logger.debug("Old state is unknown, not processing")

    def process_entity_state_change(self):
        """Process state change event."""
        event = self.state_change_data
        self.logger.debug("Processing state change event: %s", event)
        entity_id = event.entity_id
        if self.ignore_intermediate_states and event.new_state.state in [
            "opening",
            "closing",
        ]:
            self.logger.debug("Ignoring intermediate state change for %s", entity_id)
            return
        if self.wait_for_target.get(entity_id):
            # Check if still in grace period
            if self._is_in_grace_period(entity_id):
                self.logger.debug(
                    "Position change for %s ignored (in grace period)", entity_id
                )
                return  # Ignore ALL position changes during grace period

            # Grace period expired, check if we reached target
            caps = self._get_cover_capabilities(entity_id)

            # Get position based on capability
            position = self._read_position_with_capabilities(
                entity_id, caps, event.new_state
            )

            if position == self.target_call.get(entity_id):
                self.wait_for_target[entity_id] = False
                self.logger.debug("Position %s reached for %s", position, entity_id)
            self.logger.debug("Wait for target: %s", self.wait_for_target)
        else:
            self.logger.debug("No wait for target call for %s", entity_id)

    def _is_in_grace_period(self, entity_id: str) -> bool:
        """Check if entity is in command grace period.

        Args:
            entity_id: Entity to check

        Returns:
            True if in grace period, False otherwise

        """
        timestamp = self._command_timestamps.get(entity_id)
        if timestamp is None:
            return False

        elapsed = dt.datetime.now().timestamp() - timestamp
        return elapsed < self._command_grace_period_seconds

    def _start_grace_period(self, entity_id: str) -> None:
        """Start grace period for entity.

        Sets timestamp and schedules automatic clearing after grace period.

        Args:
            entity_id: Entity to start grace period for

        """
        # Cancel any existing grace period task
        self._cancel_grace_period(entity_id)

        # Record command timestamp
        now = dt.datetime.now().timestamp()
        self._command_timestamps[entity_id] = now

        # Schedule automatic grace period expiration
        task = asyncio.create_task(self._grace_period_timeout(entity_id))
        self._grace_period_tasks[entity_id] = task

        self.logger.debug(
            "Started %s second grace period for %s",
            self._command_grace_period_seconds,
            entity_id,
        )

    async def _grace_period_timeout(self, entity_id: str) -> None:
        """Clear grace period after timeout.

        Args:
            entity_id: Entity whose grace period expired

        """
        await asyncio.sleep(self._command_grace_period_seconds)

        # Clear tracking
        self._command_timestamps.pop(entity_id, None)
        self._grace_period_tasks.pop(entity_id, None)

        self.logger.debug("Grace period expired for %s", entity_id)

    def _cancel_grace_period(self, entity_id: str) -> None:
        """Cancel grace period task for entity.

        Args:
            entity_id: Entity whose grace period to cancel

        """
        task = self._grace_period_tasks.get(entity_id)
        if task and not task.done():
            task.cancel()

        self._grace_period_tasks.pop(entity_id, None)
        self._command_timestamps.pop(entity_id, None)

    def _is_in_startup_grace_period(self) -> bool:
        """Check if integration is in startup grace period.

        Returns:
            True if in startup grace period, False otherwise

        """
        if self._startup_timestamp is None:
            return False

        elapsed = dt.datetime.now().timestamp() - self._startup_timestamp
        return elapsed < self._startup_grace_period_seconds

    def _start_startup_grace_period(self) -> None:
        """Start startup grace period after first refresh.

        Sets timestamp and schedules automatic clearing after grace period.
        This prevents manual override detection during HA restart when covers
        may respond slowly due to system initialization.

        """
        # Cancel any existing grace period task
        if self._startup_grace_period_task and not self._startup_grace_period_task.done():
            self._startup_grace_period_task.cancel()

        # Record startup timestamp
        self._startup_timestamp = dt.datetime.now().timestamp()

        # Schedule automatic grace period expiration
        self._startup_grace_period_task = asyncio.create_task(
            self._startup_grace_period_timeout()
        )

        self.logger.info(
            "Started %s second startup grace period (manual override detection disabled)",
            self._startup_grace_period_seconds,
        )

    async def _startup_grace_period_timeout(self) -> None:
        """Clear startup grace period after timeout."""
        await asyncio.sleep(self._startup_grace_period_seconds)

        # Clear tracking
        self._startup_timestamp = None
        self._startup_grace_period_task = None

        self.logger.info(
            "Startup grace period expired (manual override detection enabled)"
        )

    @callback
    def _async_cancel_update_listener(self) -> None:
        """Cancel the scheduled update."""
        if self._update_listener:
            self._update_listener()
            self._update_listener = None

    async def async_timed_end_time(self) -> None:
        """Control state at end time."""
        self.logger.debug("Scheduling end time update at %s", self._end_time)
        self._async_cancel_update_listener()
        self.logger.debug(
            "End time: %s, Track end time: %s, Scheduled time: %s, Condition: %s",
            self._end_time,
            self._track_end_time,
            self._scheduled_time,
            self._end_time > self._scheduled_time,
        )
        self._update_listener = async_track_point_in_time(
            self.hass, self.async_timed_refresh, self._end_time
        )
        self._scheduled_time = self._end_time

    def _calculate_cover_state(self, cover_data, options) -> int:
        """Calculate cover state and update internal state.

        Args:
            cover_data: Cover calculation data object
            options: Configuration options

        Returns:
            Calculated state position

        """
        # Access climate data if climate mode is enabled
        if self._climate_mode:
            self.climate_mode_data(options, cover_data)
        else:
            self.logger.debug("Control method is %s", self.control_method)

        # Calculate the state of the cover
        self.normal_cover_state = NormalCoverState(cover_data)
        self.logger.debug(
            "Determined normal cover state to be %s", self.normal_cover_state
        )

        self.default_state = round(self.normal_cover_state.get_state())
        self.logger.debug("Determined default state to be %s", self.default_state)

        # Store raw calculated position for diagnostics (before min/max limits)
        # This is the pure geometric calculation
        if cover_data.direct_sun_valid:
            # Sun is in front - use raw calculated percentage
            self.raw_calculated_position = round(cover_data.calculate_percentage())
        else:
            # Sun not in front - use default position (no calculation)
            self.raw_calculated_position = cover_data.default
        self.logger.debug("Raw calculated position: %s", self.raw_calculated_position)

        return self.state

    async def _update_solar_times_if_needed(self, normal_cover) -> tuple[dt.datetime, dt.datetime]:
        """Update solar times if needed (first refresh or new day).

        Args:
            normal_cover: Cover object with solar_times method

        Returns:
            Tuple of (start_time, end_time)

        """
        if (
            self.first_refresh
            or self._sun_start_time is None
            or dt.datetime.now(pytz.UTC).date() != self._sun_start_time.date()
        ):
            self.logger.debug("Calculating solar times")
            loop = asyncio.get_event_loop()
            start, end = await loop.run_in_executor(None, normal_cover.solar_times)
            self._sun_start_time = start
            self._sun_end_time = end
            self.logger.debug("Sun start time: %s, Sun end time: %s", start, end)
            return start, end

        return self._sun_start_time, self._sun_end_time

    async def _async_update_data(self) -> AdaptiveCoverData:
        self.logger.debug("Updating data")
        if self.first_refresh:
            self._cached_options = self.config_entry.options

        options = self.config_entry.options
        self._update_options(options)

        # Get data for the blind and update manager
        cover_data = self.get_blind_data(options=options)
        self._update_manager_and_covers()

        # Calculate cover state
        state = self._calculate_cover_state(cover_data, options)
        await self.manager.reset_if_needed()

        # Schedule end time update if needed
        if (
            self._end_time
            and self._track_end_time
            and self._end_time > self._scheduled_time
        ):
            await self.async_timed_end_time()

        # Handle types of changes
        if self.state_change:
            await self.async_handle_state_change(state, options)
        if self.cover_state_change:
            await self.async_handle_cover_state_change(state)
        if self.first_refresh:
            await self.async_handle_first_refresh(state, options)
        if self.timed_refresh:
            await self.async_handle_timed_refresh(options)

        # Update solar times
        normal_cover = self.normal_cover_state.cover
        start, end = await self._update_solar_times_if_needed(normal_cover)

        # Build diagnostic data if enabled
        diagnostics = None
        if options.get(CONF_ENABLE_DIAGNOSTICS, False):
            diagnostics = self.build_diagnostic_data()

        return AdaptiveCoverData(
            climate_mode_toggle=self.switch_mode,
            states={
                "state": state,
                "start": start,
                "end": end,
                "control": self.control_method,
                "sun_motion": normal_cover.direct_sun_valid,
                "manual_override": self.manager.binary_cover_manual,
                "manual_list": self.manager.manual_controlled,
            },
            attributes={
                "default": options.get(CONF_DEFAULT_HEIGHT),
                "sunset_default": options.get(CONF_SUNSET_POS),
                "sunset_offset": options.get(CONF_SUNSET_OFFSET),
                "azimuth_window": options.get(CONF_AZIMUTH),
                "field_of_view": [
                    options.get(CONF_FOV_LEFT),
                    options.get(CONF_FOV_RIGHT),
                ],
                "blind_spot": options.get(CONF_BLIND_SPOT_ELEVATION),
            },
            diagnostics=diagnostics,
        )

    async def async_handle_state_change(self, state: int, options):
        """Handle state change from tracked entities."""
        if self.automatic_control:
            for cover in self.entities:
                await self.async_handle_call_service(cover, state, options)
        else:
            self.logger.debug("State change but control toggle is off")
        self.state_change = False
        self.logger.debug("State change handled")

    async def async_handle_cover_state_change(self, state: int):
        """Handle state change from assigned covers."""
        if self.manual_toggle and self.automatic_control:
            # Check startup grace period FIRST to prevent false manual override
            # detection during HA restart when covers respond slowly
            if self._is_in_startup_grace_period():
                entity_id = self.state_change_data.entity_id
                self.logger.debug(
                    "Position change for %s ignored (in startup grace period)",
                    entity_id,
                )
                self.cover_state_change = False
                return

            # Get the entity_id from state_change_data
            entity_id = self.state_change_data.entity_id

            # Use target_call if available (contains actual sent position),
            # otherwise fall back to calculated state.
            # This is critical for open/close-only covers where the calculated
            # state gets transformed (via threshold) to 0 or 100 before sending.
            expected_position = self.target_call.get(entity_id, state)

            self.manager.handle_state_change(
                self.state_change_data,
                expected_position,
                self._cover_type,
                self.manual_reset,
                self.wait_for_target,
                self.manual_threshold,
            )
        self.cover_state_change = False
        self.logger.debug("Cover state change handled")

    async def async_handle_first_refresh(self, state: int, options):
        """Handle first refresh."""
        if self.automatic_control:
            for cover in self.entities:
                # Always set target position for verification, even if we don't send command
                # This ensures position verification works after restart
                if self.check_adaptive_time and not self.manager.is_cover_manual(cover):
                    self.target_call[cover] = state
                    self.logger.debug(
                        "First refresh: Set target position %s for %s",
                        state,
                        cover
                    )

                    # Now check if we should actually send the command
                    if self.check_position_delta(cover, state, options):
                        await self.async_set_position(cover, state)
        else:
            self.logger.debug("First refresh but control toggle is off")
        self.first_refresh = False
        self.logger.debug("First refresh handled")

    async def async_handle_timed_refresh(self, options):
        """Handle timed refresh."""
        self.logger.debug(
            "This is a timed refresh, using sunset position: %s",
            options.get(CONF_SUNSET_POS),
        )
        if self.automatic_control:
            for cover in self.entities:
                await self.async_set_manual_position(
                    cover,
                    (
                        inverse_state(options.get(CONF_SUNSET_POS))
                        if self._inverse_state
                        else options.get(CONF_SUNSET_POS)
                    ),
                )
        else:
            self.logger.debug("Timed refresh but control toggle is off")
        self.timed_refresh = False
        self.logger.debug("Timed refresh handled")

    async def async_handle_call_service(self, entity, state: int, options):
        """Handle call service."""
        if (
            self.check_adaptive_time
            and self.check_position_delta(entity, state, options)
            and self.check_time_delta(entity)
            and not self.manager.is_cover_manual(entity)
        ):
            await self.async_set_position(entity, state)

    async def async_set_position(self, entity, state: int):
        """Call service to set cover position."""
        await self.async_set_manual_position(entity, state)

    def _prepare_position_service_call(
        self, entity: str, state: int, caps: dict[str, bool]
    ) -> tuple[str, dict, bool]:
        """Determine service and data based on capabilities.

        Args:
            entity: Entity ID
            state: Target position (0-100)
            caps: Cover capabilities dict

        Returns:
            Tuple of (service_name, service_data, supports_position)

        """
        # Determine if cover supports position control
        supports_position = False
        if self.is_tilt_cover:
            supports_position = caps.get("has_set_tilt_position", True)
        else:
            supports_position = caps.get("has_set_position", True)

        self.logger.debug(
            "Cover %s: supports_position=%s, caps=%s",
            entity,
            supports_position,
            caps,
        )

        if supports_position:
            # Use position control
            service = SERVICE_SET_COVER_POSITION
            service_data = {ATTR_ENTITY_ID: entity}

            if self.is_tilt_cover:
                service = SERVICE_SET_COVER_TILT_POSITION
                service_data[ATTR_TILT_POSITION] = state
            else:
                service_data[ATTR_POSITION] = state

            self.wait_for_target[entity] = True
            self.target_call[entity] = state
            self._start_grace_period(entity)
            self.logger.debug(
                "Set wait for target %s and target call %s",
                self.wait_for_target,
                self.target_call,
            )
        else:
            # Use open/close control
            has_open = caps.get("has_open", False)
            has_close = caps.get("has_close", False)

            if not has_open or not has_close:
                self.logger.warning(
                    "Cover %s does not support both open and close. Skipping.",
                    entity,
                )
                return None, None, False

            # Apply threshold
            if state >= self._open_close_threshold:
                service = "open_cover"
                self.target_call[entity] = 100
                self._never_commanded.discard(entity)  # Remove from never-commanded tracking
            else:
                service = "close_cover"
                self.target_call[entity] = 0
                self._never_commanded.discard(entity)  # Remove from never-commanded tracking

            service_data = {ATTR_ENTITY_ID: entity}
            self.wait_for_target[entity] = True
            self._start_grace_period(entity)

            self.logger.debug(
                "Using open/close control: state=%s, threshold=%s, service=%s",
                state,
                self._open_close_threshold,
                service,
            )

        return service, service_data, supports_position

    def _track_cover_action(
        self, entity: str, service: str, state: int, supports_position: bool
    ) -> None:
        """Track cover action for diagnostic sensor.

        Args:
            entity: Entity ID
            service: Service name called
            state: Requested position
            supports_position: Whether position control is used

        """
        self.last_cover_action = {
            "entity_id": entity,
            "service": service,
            "position": state if supports_position else self.target_call[entity],
            "calculated_position": state,
            "threshold_used": self._open_close_threshold if not supports_position else None,
            "inverse_state_applied": self._inverse_state,
            "timestamp": dt.datetime.now().isoformat(),
            "covers_controlled": 1,
        }

    async def async_set_manual_position(self, entity, state):
        """Call service to set cover position or open/close based on capability."""
        if not self.check_position(entity, state):
            return

        # Check capabilities and prepare service call
        caps = self._get_cover_capabilities(entity)
        service, service_data, supports_position = self._prepare_position_service_call(
            entity, state, caps
        )

        # Skip if service preparation failed (e.g., missing open/close capabilities)
        if service is None:
            return

        # Track action for diagnostic sensor
        self._track_cover_action(entity, service, state, supports_position)

        # Execute service call
        self.logger.debug("Run %s with data %s", service, service_data)
        await self.hass.services.async_call(COVER_DOMAIN, service, service_data)
        self.logger.debug("Successfully called service %s for %s", service, entity)

    def _update_options(self, options):
        """Update options."""
        self.entities = options.get(CONF_ENTITIES, [])
        self.min_change = options.get(CONF_DELTA_POSITION, 1)
        self.time_threshold = options.get(CONF_DELTA_TIME, 2)
        self.start_time = options.get(CONF_START_TIME)
        self.start_time_entity = options.get(CONF_START_ENTITY)
        self.end_time = options.get(CONF_END_TIME)
        self.end_time_entity = options.get(CONF_END_ENTITY)
        self.manual_reset = options.get(CONF_MANUAL_OVERRIDE_RESET, False)
        self.manual_duration = options.get(
            CONF_MANUAL_OVERRIDE_DURATION, {"minutes": 15}
        )
        self.manual_threshold = options.get(CONF_MANUAL_THRESHOLD)
        self.start_value = options.get(CONF_INTERP_START)
        self.end_value = options.get(CONF_INTERP_END)
        self.normal_list = options.get(CONF_INTERP_LIST)
        self.new_list = options.get(CONF_INTERP_LIST_NEW)
        self._open_close_threshold = options.get(CONF_OPEN_CLOSE_THRESHOLD, 50)

    def _update_manager_and_covers(self):
        self.manager.add_covers(self.entities)
        if not self._manual_toggle:
            for entity in self.manager.manual_controlled:
                self.manager.reset(entity)

    def get_blind_data(self, options):
        """Assign correct class for type of blind."""
        if self.is_blind_cover:
            cover_data = AdaptiveVerticalCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.vertical_data(options),
            )
        if self.is_awning_cover:
            cover_data = AdaptiveHorizontalCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.vertical_data(options),
                *self.horizontal_data(options),
            )
        if self.is_tilt_cover:
            cover_data = AdaptiveTiltCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.tilt_data(options),
            )
        return cover_data

    @property
    def check_adaptive_time(self):
        """Check if time is within start and end times."""
        if self._start_time and self._end_time and self._start_time > self._end_time:
            self.logger.error("Start time is after end time")
        return self.before_end_time and self.after_start_time

    @property
    def after_start_time(self):
        """Check if time is after start time."""
        now = dt.datetime.now()
        if self.start_time_entity is not None:
            time = get_datetime_from_str(
                get_safe_state(self.hass, self.start_time_entity)
            )
            self.logger.debug(
                "Start time: %s, now: %s, now >= time: %s ", time, now, now >= time
            )
            self._start_time = time
            return now >= time
        if self.start_time is not None:
            time = get_datetime_from_str(self.start_time)

            self.logger.debug(
                "Start time: %s, now: %s, now >= time: %s", time, now, now >= time
            )
            self._start_time
            return now >= time
        return True

    @property
    def _end_time(self) -> dt.datetime | None:
        """Get end time."""
        time = None
        if self.end_time_entity is not None:
            time = get_datetime_from_str(
                get_safe_state(self.hass, self.end_time_entity)
            )
        elif self.end_time is not None:
            time = get_datetime_from_str(self.end_time)
            if time.time() == dt.time(0, 0):
                time = time + dt.timedelta(days=1)
        return time

    @property
    def before_end_time(self):
        """Check if time is before end time."""
        if self._end_time is not None:
            now = dt.datetime.now()
            self.logger.debug(
                "End time: %s, now: %s, now < time: %s",
                self._end_time,
                now,
                now < self._end_time,
            )
            return now < self._end_time
        return True

    def _get_current_position(self, entity) -> int | None:
        """Get current position of cover.

        For position-capable covers, returns current_position or current_tilt_position.
        For open/close-only covers, maps state to 0 (closed) or 100 (open).
        """
        # Check capabilities on-demand
        caps = self._get_cover_capabilities(entity)

        # Read position based on cover type and capabilities
        return self._read_position_with_capabilities(entity, caps)

    def check_position(self, entity, state):
        """Check if position is different as state.

        Bypasses check if sun just came into field of view to ensure
        covers reposition even if calculated position equals current position
        (can happen when min/max limits clamp low-angle calculations).
        """
        position = self._get_current_position(entity)
        if position is not None:
            # Check if sun just came into field of view
            sun_just_appeared = self._check_sun_validity_transition()

            if sun_just_appeared:
                self.logger.debug(
                    "Bypassing position equality check: sun just came into field of view "
                    "(entity: %s, position: %s, state: %s)",
                    entity,
                    position,
                    state
                )
                return True  # Force repositioning on sun visibility transition

            # Normal check: only move if position changed
            return position != state

        self.logger.debug("Cover is already at position %s", state)
        return False

    def check_position_delta(self, entity, state: int, options):
        """Check cover positions to reduce calls."""
        position = self._get_current_position(entity)
        if position is not None:
            condition = abs(position - state) >= self.min_change

            # Get special positions for comparison
            default_height = options.get(CONF_DEFAULT_HEIGHT)
            sunset_pos = options.get(CONF_SUNSET_POS)
            special_positions = [0, 100]
            if default_height is not None:
                special_positions.append(default_height)
            if sunset_pos is not None:
                special_positions.append(sunset_pos)

            self.logger.debug(
                "Entity: %s, position: %s, state: %s, delta position: %s, min_change: %s, condition: %s",
                entity,
                position,
                state,
                abs(position - state),
                self.min_change,
                condition,
            )

            # Bypass delta check when moving TO special positions (existing logic)
            if state in special_positions:
                self.logger.debug(
                    "Bypassing delta check: moving TO special position %s", state
                )
                condition = True

            # Bypass delta check when moving FROM special positions (NEW logic)
            # This ensures covers reposition when sun transitions from "not in front" to "in front"
            elif position in special_positions:
                self.logger.debug(
                    "Bypassing delta check: moving FROM special position %s to calculated position %s",
                    position,
                    state
                )
                condition = True

            return condition
        return True

    def check_time_delta(self, entity):
        """Check if time delta is passed."""
        now = dt.datetime.now(dt.UTC)
        last_updated = get_last_updated(entity, self.hass)
        if last_updated is not None:
            condition = now - last_updated >= dt.timedelta(minutes=self.time_threshold)
            self.logger.debug(
                "Entity: %s, time delta: %s, threshold: %s, condition: %s",
                entity,
                now - last_updated,
                self.time_threshold,
                condition,
            )
            return condition
        return True

    @property
    def pos_sun(self):
        """Fetch information for sun position."""
        return [
            state_attr(self.hass, "sun.sun", "azimuth"),
            state_attr(self.hass, "sun.sun", "elevation"),
        ]

    def common_data(self, options):
        """Update shared parameters."""
        return [
            options.get(CONF_SUNSET_POS),
            options.get(CONF_SUNSET_OFFSET),
            options.get(CONF_SUNRISE_OFFSET, options.get(CONF_SUNSET_OFFSET)),
            self.hass.config.time_zone,
            options.get(CONF_FOV_LEFT),
            options.get(CONF_FOV_RIGHT),
            options.get(CONF_AZIMUTH),
            options.get(CONF_DEFAULT_HEIGHT),
            options.get(CONF_MAX_POSITION),
            options.get(CONF_MIN_POSITION),
            options.get(CONF_ENABLE_MAX_POSITION, False),
            options.get(CONF_ENABLE_MIN_POSITION, False),
            options.get(CONF_BLIND_SPOT_LEFT),
            options.get(CONF_BLIND_SPOT_RIGHT),
            options.get(CONF_BLIND_SPOT_ELEVATION),
            options.get(CONF_ENABLE_BLIND_SPOT, False),
            options.get(CONF_MIN_ELEVATION, None),
            options.get(CONF_MAX_ELEVATION, None),
        ]

    def get_climate_data(self, options):
        """Update climate data."""
        return [
            self.hass,
            self.logger,
            options.get(CONF_TEMP_ENTITY),
            options.get(CONF_TEMP_LOW),
            options.get(CONF_TEMP_HIGH),
            options.get(CONF_PRESENCE_ENTITY),
            options.get(CONF_WEATHER_ENTITY),
            options.get(CONF_WEATHER_STATE),
            options.get(CONF_OUTSIDETEMP_ENTITY),
            self._temp_toggle,
            self._cover_type,
            options.get(CONF_TRANSPARENT_BLIND),
            options.get(CONF_LUX_ENTITY),
            options.get(CONF_IRRADIANCE_ENTITY),
            options.get(CONF_LUX_THRESHOLD),
            options.get(CONF_IRRADIANCE_THRESHOLD),
            options.get(CONF_OUTSIDE_THRESHOLD),
            self._lux_toggle,
            self._irradiance_toggle,
        ]

    def climate_mode_data(self, options, cover_data):
        """Update climate mode data and control method."""
        climate = ClimateCoverData(*self.get_climate_data(options))
        self.climate_state = round(ClimateCoverState(cover_data, climate).get_state())
        climate_data = ClimateCoverState(cover_data, climate).climate_data
        self.climate_data = climate_data  # Store for P1 diagnostics
        if climate_data.is_summer and self.switch_mode:
            self.control_method = "summer"
        if climate_data.is_winter and self.switch_mode:
            self.control_method = "winter"
        self.logger.debug(
            "Climate mode control method was set to %s", self.control_method
        )

    def vertical_data(self, options):
        """Update data for vertical blinds."""
        return [
            options.get(CONF_DISTANCE),
            options.get(CONF_HEIGHT_WIN),
            options.get(CONF_WINDOW_DEPTH, 0.0),  # Default 0.0 for backward compatibility
        ]

    def horizontal_data(self, options):
        """Update data for horizontal blinds."""
        return [
            options.get(CONF_LENGTH_AWNING),
            options.get(CONF_AWNING_ANGLE),
        ]

    def tilt_data(self, options):
        """Update data for tilted blinds.

        Converts slat dimensions from centimeters (as entered in UI) to meters
        (as required by calculation formulas).
        """
        depth = options.get(CONF_TILT_DEPTH)
        distance = options.get(CONF_TILT_DISTANCE)

        # Warn if values are suspiciously small (likely already in meters)
        if depth < 0.1 or distance < 0.1:
            _LOGGER.warning(
                "Tilt cover '%s': slat dimensions are very small (depth=%s, distance=%s). "
                "If you previously entered values in METERS, please reconfigure and enter in CENTIMETERS. "
                "For example: 2.5cm slats should be entered as '2.5', not '0.025'.",
                self.config_entry.data.get("name"),
                depth,
                distance,
            )

        return [
            distance / 100,  # Convert cm to meters
            depth / 100,     # Convert cm to meters
            options.get(CONF_TILT_MODE),
        ]

    def _build_solar_diagnostics(self) -> dict:
        """Build solar position diagnostics."""
        diagnostics = {}
        sun_azimuth, sun_elevation = self.pos_sun
        diagnostics["sun_azimuth"] = sun_azimuth
        diagnostics["sun_elevation"] = sun_elevation

        # Gamma (surface solar azimuth)
        if self.normal_cover_state and hasattr(self.normal_cover_state.cover, "gamma"):
            diagnostics["gamma"] = self.normal_cover_state.cover.gamma

        return diagnostics

    def _build_position_diagnostics(self) -> dict:
        """Build calculated position diagnostics."""
        diagnostics = {}

        # Use raw calculated position (before min/max limits) for diagnostic
        diagnostics["calculated_position"] = self.raw_calculated_position

        if self.climate_state is not None:
            diagnostics["calculated_position_climate"] = self.climate_state

        # Control status determination
        control_status = self._determine_control_status()
        diagnostics["control_status"] = control_status

        return diagnostics

    def _build_time_window_diagnostics(self) -> dict:
        """Build time window diagnostics."""
        return {
            "time_window": {
                "check_adaptive_time": self.check_adaptive_time,
                "after_start_time": self.after_start_time,
                "before_end_time": self.before_end_time,
                "start_time": self._start_time,
                "end_time": self._end_time,
            }
        }

    def _build_sun_validity_diagnostics(self) -> dict:
        """Build sun validity diagnostics."""
        diagnostics = {}
        if self.normal_cover_state and self.normal_cover_state.cover:
            cover = self.normal_cover_state.cover
            diagnostics["sun_validity"] = {
                "valid": cover.valid,
                "valid_elevation": cover.valid_elevation,
                "in_blind_spot": getattr(cover, "in_blind_spot", None),
            }
        return diagnostics

    def _build_climate_diagnostics(self) -> dict:
        """Build climate mode diagnostics."""
        diagnostics = {}
        if self._climate_mode and self.climate_data is not None:
            diagnostics["climate_control_method"] = self.control_method

            # Active temperature and temperature details
            diagnostics["active_temperature"] = self.climate_data.get_current_temperature
            diagnostics["temperature_details"] = {
                "inside_temperature": self.climate_data.inside_temperature,
                "outside_temperature": self.climate_data.outside_temperature,
                "temp_switch": self.climate_data.temp_switch,
            }

            # Climate conditions
            diagnostics["climate_conditions"] = {
                "is_summer": self.climate_data.is_summer,
                "is_winter": self.climate_data.is_winter,
                "is_presence": self.climate_data.is_presence,
                "is_sunny": self.climate_data.is_sunny,
                "lux_active": self.climate_data.lux if self.climate_data._use_lux else None,
                "irradiance_active": self.climate_data.irradiance if self.climate_data._use_irradiance else None,
            }

        return diagnostics

    def _build_last_action_diagnostics(self) -> dict:
        """Build last cover action diagnostics."""
        diagnostics = {}
        if self.last_cover_action.get("entity_id"):
            diagnostics["last_cover_action"] = self.last_cover_action.copy()
        return diagnostics

    def build_diagnostic_data(self) -> dict:
        """Build diagnostic data for diagnostic sensors."""
        return {
            **self._build_solar_diagnostics(),
            **self._build_position_diagnostics(),
            **self._build_time_window_diagnostics(),
            **self._build_sun_validity_diagnostics(),
            **self._build_climate_diagnostics(),
            **self._build_last_action_diagnostics(),
        }

    def _determine_control_status(self) -> str:
        """Determine the current control status."""
        if not self.automatic_control:
            return ControlStatus.AUTOMATIC_CONTROL_OFF

        if self.manager.binary_cover_manual:
            return ControlStatus.MANUAL_OVERRIDE

        if not self.check_adaptive_time:
            return ControlStatus.OUTSIDE_TIME_WINDOW

        if self.normal_cover_state and not self.normal_cover_state.cover.valid:
            return ControlStatus.SUN_NOT_VISIBLE

        # For position/time delta, we'd need to check per-cover, so we default to active
        # if all other checks pass
        return ControlStatus.ACTIVE

    @property
    def state(self) -> int:
        """Handle the output of the state based on mode."""
        self.logger.debug(
            "Basic position: %s; Climate position: %s; Using climate position? %s",
            self.default_state,
            self.climate_state,
            self._switch_mode,
        )
        if self._switch_mode:
            state = self.climate_state
        else:
            state = self.default_state

        if self._use_interpolation:
            self.logger.debug("Interpolating position: %s", state)
            state = self.interpolate_states(state)

        if self._inverse_state and self._use_interpolation:
            self.logger.info(
                "Inverse state is not supported with interpolation, you can inverse the state by arranging the list from high to low"
            )

        if self._inverse_state and not self._use_interpolation:
            state = inverse_state(state)
            self.logger.debug("Inversed position: %s", state)

        self.logger.debug("Final position to use: %s", state)
        return state

    def interpolate_states(self, state):
        """Interpolate states."""
        normal_range = [0, 100]
        new_range = []
        if self.start_value is not None and self.end_value is not None:
            new_range = [self.start_value, self.end_value]
        if self.normal_list and self.new_list:
            normal_range = list(map(int, self.normal_list))
            new_range = list(map(int, self.new_list))
        if new_range:
            state = np.interp(state, normal_range, new_range)
        return state

    @property
    def switch_mode(self):
        """Let switch toggle climate mode."""
        return self._switch_mode

    @switch_mode.setter
    def switch_mode(self, value):
        self._switch_mode = value

    @property
    def temp_toggle(self):
        """Let switch toggle between inside or outside temperature."""
        return self._temp_toggle

    @temp_toggle.setter
    def temp_toggle(self, value):
        self._temp_toggle = value

    @property
    def automatic_control(self):
        """Toggle automation."""
        return self._automatic_control

    @automatic_control.setter
    def automatic_control(self, value):
        self._automatic_control = value

    @property
    def manual_toggle(self):
        """Toggle automation."""
        return self._manual_toggle

    @manual_toggle.setter
    def manual_toggle(self, value):
        self._manual_toggle = value

    @property
    def lux_toggle(self):
        """Toggle automation."""
        return self._lux_toggle

    @lux_toggle.setter
    def lux_toggle(self, value):
        self._lux_toggle = value

    @property
    def irradiance_toggle(self):
        """Toggle automation."""
        return self._irradiance_toggle

    @irradiance_toggle.setter
    def irradiance_toggle(self, value):
        self._irradiance_toggle = value

    @property
    def return_to_default_toggle(self):
        """Toggle return to default position on auto control off."""
        return self._return_to_default_toggle

    @return_to_default_toggle.setter
    def return_to_default_toggle(self, value):
        self._return_to_default_toggle = value

    async def _check_time_window_transition(self, now: dt.datetime) -> None:
        """Check if time window state has changed and trigger refresh if needed.

        This method detects when the operational time window changes state
        (e.g., when end time is reached) and triggers appropriate actions.
        Provides <1 minute response time for time window changes.
        """
        # Initialize tracking on first call
        if self._last_time_window_state is None:
            self._last_time_window_state = self.check_adaptive_time
            return

        current_state = self.check_adaptive_time

        # If state changed, trigger appropriate action
        if current_state != self._last_time_window_state:
            self.logger.info(
                "Time window state changed: %s → %s",
                "active" if self._last_time_window_state else "inactive",
                "active" if current_state else "inactive"
            )
            self._last_time_window_state = current_state

            # If we just left the time window, return covers to default position
            if not current_state and self._track_end_time:
                self.logger.info("End time reached, returning covers to default position")
                self.timed_refresh = True
                await self.async_refresh()

    def _check_sun_validity_transition(self) -> bool:
        """Check if sun validity state has changed from False to True.

        Returns True if sun just came into field of view, indicating
        covers should immediately reposition regardless of delta checks.
        """
        # Need cover data to check sun validity
        if not hasattr(self, 'normal_cover_state') or self.normal_cover_state is None:
            return False

        current_sun_valid = self.normal_cover_state.cover.direct_sun_valid

        # Initialize tracking on first call
        if self._last_sun_validity_state is None:
            self._last_sun_validity_state = current_sun_valid
            return False

        # Detect transition from not-in-front to in-front
        sun_just_appeared = (not self._last_sun_validity_state) and current_sun_valid

        # Update tracking
        self._last_sun_validity_state = current_sun_valid

        if sun_just_appeared:
            self.logger.info(
                "Sun visibility transition detected: OFF → ON (sun came into field of view)"
            )

        return sun_just_appeared

    async def async_periodic_position_check(self, now: dt.datetime) -> None:
        """Periodically verify cover positions match calculated positions."""
        # Check if time window state changed (e.g., passed end time)
        # This provides <1 minute response time for time window changes
        await self._check_time_window_transition(now)

        # Skip if not within operational time window
        if not self.check_adaptive_time:
            return

        # Skip if automatic control is disabled
        if not self.automatic_control:
            return

        for entity_id in self.entities:
            await self._verify_entity_position(entity_id, now)

    async def _verify_entity_position(self, entity_id: str, now: dt.datetime) -> None:
        """Verify a single entity's position and retry if needed."""
        # Update last verification time FIRST for diagnostic tracking
        check_time = now if isinstance(now, dt.datetime) else dt.datetime.now()
        self._last_verification[entity_id] = check_time

        # Skip if manual override active
        if self.manager.is_cover_manual(entity_id):
            self._reset_retry_count(entity_id)
            return

        # Skip if currently waiting for target (move in progress)
        if self.wait_for_target.get(entity_id, False):
            return

        # Get target position (the position we last sent to this cover)
        target_position = self.target_call.get(entity_id)
        if target_position is None:
            # Only log once when first encountered to avoid log spam
            if entity_id not in self._never_commanded:
                self._never_commanded.add(entity_id)
                self.logger.debug(
                    "No command sent to %s yet, position verification will begin after first command",
                    entity_id
                )
            return

        # Get actual position
        actual_position = self._get_current_position(entity_id)

        if actual_position is None:
            self.logger.debug("Cannot verify position for %s: position unavailable", entity_id)
            return

        # Check if positions match within tolerance
        # Compare to target_call (what we sent), not self.state (current calculation)
        # This prevents false mismatches when sun moves between command and verification
        position_delta = abs(target_position - actual_position)

        if position_delta <= self._position_tolerance:
            # Position is correct, reset retry count
            self._reset_retry_count(entity_id)
            return

        # Position mismatch detected - cover failed to reach target we sent
        retry_count = self._retry_counts.get(entity_id, 0)

        if retry_count >= self._max_retries:
            self.logger.warning(
                "Max retries exceeded for %s. Position mismatch: target=%s, actual=%s, delta=%s",
                entity_id,
                target_position,
                actual_position,
                position_delta,
            )
            return

        # Increment retry count and reposition
        self._retry_counts[entity_id] = retry_count + 1
        self.logger.info(
            "Position mismatch detected for %s (attempt %d/%d): target=%s, actual=%s, delta=%s. Repositioning...",
            entity_id,
            retry_count + 1,
            self._max_retries,
            target_position,
            actual_position,
            position_delta,
        )

        # Resend the same target position
        # Note: If sun has moved and changed the calculated position, the normal
        # update cycle will handle that separately. We only retry the last command.
        await self.async_set_position(entity_id, target_position)

    def _reset_retry_count(self, entity_id: str) -> None:
        """Reset retry count for an entity."""
        if entity_id in self._retry_counts:
            del self._retry_counts[entity_id]

    def _start_position_verification(self) -> None:
        """Start periodic position verification."""
        if self._position_check_interval is not None:
            return  # Already started

        interval = dt.timedelta(minutes=self._check_interval_minutes)
        self._position_check_interval = async_track_time_interval(
            self.hass,
            self.async_periodic_position_check,
            interval,
        )
        self.logger.debug("Started periodic position verification (interval: %s)", interval)

    def _stop_position_verification(self) -> None:
        """Stop periodic position verification."""
        if self._position_check_interval:
            self._position_check_interval()
            self._position_check_interval = None
            self.logger.debug("Stopped periodic position verification")

    async def async_shutdown(self) -> None:
        """Clean up resources on shutdown."""
        # Cancel all grace period tasks
        for entity_id in list(self._grace_period_tasks.keys()):
            self._cancel_grace_period(entity_id)

        # Stop position verification
        self._stop_position_verification()

        self.logger.debug("Coordinator shutdown complete")


class AdaptiveCoverManager:
    """Track position changes."""

    def __init__(self, hass: HomeAssistant, reset_duration: dict[str:int], logger) -> None:
        """Initialize the AdaptiveCoverManager."""
        self.hass = hass
        self.covers: set[str] = set()

        self.manual_control: dict[str, bool] = {}
        self.manual_control_time: dict[str, dt.datetime] = {}
        self.reset_duration = dt.timedelta(**reset_duration)
        self.logger = logger

    def add_covers(self, entity):
        """Update set with entities."""
        self.covers.update(entity)

    def handle_state_change(
        self,
        states_data,
        our_state,
        blind_type,
        allow_reset,
        wait_target_call,
        manual_threshold,
    ):
        """Process state change event."""
        event = states_data
        if event is None:
            return
        entity_id = event.entity_id
        if entity_id not in self.covers:
            return
        if wait_target_call.get(entity_id):
            return

        new_state = event.new_state

        if blind_type == "cover_tilt":
            new_position = new_state.attributes.get("current_tilt_position")
        else:
            new_position = new_state.attributes.get("current_position")

        # If position is None, try mapping from open/close state
        if new_position is None:
            new_position = get_open_close_state(self.hass, entity_id)

        if new_position != our_state:
            if (
                manual_threshold is not None
                and abs(our_state - new_position) < manual_threshold
            ):
                self.logger.debug(
                    "Position change is less than threshold %s for %s",
                    manual_threshold,
                    entity_id,
                )
                return
            self.logger.debug(
                "Manual change detected for %s. Our state: %s, new state: %s",
                entity_id,
                our_state,
                new_position,
            )
            self.logger.debug(
                "Set manual control for %s, for at least %s seconds, reset_allowed: %s",
                entity_id,
                self.reset_duration.total_seconds(),
                allow_reset,
            )
            self.mark_manual_control(entity_id)
            self.set_last_updated(entity_id, new_state, allow_reset)

    def set_last_updated(self, entity_id, new_state, allow_reset):
        """Set last updated time for manual control."""
        if entity_id not in self.manual_control_time or allow_reset:
            last_updated = new_state.last_updated
            self.manual_control_time[entity_id] = last_updated
            self.logger.debug(
                "Updating last updated for manual control to %s for %s. Allow reset:%s",
                last_updated,
                entity_id,
                allow_reset,
            )
        elif not allow_reset:
            self.logger.debug(
                "Already manual control time specified for %s, reset is not allowed by user setting:%s",
                entity_id,
                allow_reset,
            )

    def mark_manual_control(self, cover: str) -> None:
        """Mark cover as under manual control."""
        self.manual_control[cover] = True

    async def reset_if_needed(self):
        """Reset manual control state of the covers."""
        current_time = dt.datetime.now(dt.UTC)
        manual_control_time_copy = dict(self.manual_control_time)
        for entity_id, last_updated in manual_control_time_copy.items():
            if current_time - last_updated > self.reset_duration:
                self.logger.debug(
                    "Resetting manual override for %s, because duration has elapsed",
                    entity_id,
                )
                self.reset(entity_id)

    def reset(self, entity_id):
        """Reset manual control for a cover."""
        self.manual_control[entity_id] = False
        self.manual_control_time.pop(entity_id, None)
        self.logger.debug("Reset manual override for %s", entity_id)

    def is_cover_manual(self, entity_id):
        """Check if a cover is under manual control."""
        return self.manual_control.get(entity_id, False)

    @property
    def binary_cover_manual(self):
        """Check if any cover is under manual control."""
        return any(value for value in self.manual_control.values())

    @property
    def manual_controlled(self):
        """Get the list of covers under manual control."""
        return [k for k, v in self.manual_control.items() if v]


def inverse_state(state: int) -> int:
    """Inverse state."""
    return 100 - state
