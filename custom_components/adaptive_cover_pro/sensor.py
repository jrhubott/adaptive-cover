"""Sensor platform for Adaptive Cover Pro integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CLIMATE_MODE,
    CONF_ENABLE_DIAGNOSTICS,
    CONF_SENSOR_TYPE,
    DOMAIN,
)
from .coordinator import AdaptiveDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Adaptive Cover Pro config entry."""

    name = config_entry.data["name"]
    coordinator: AdaptiveDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    # Standard sensors
    entities.append(
        AdaptiveCoverSensorEntity(
            config_entry.entry_id, hass, config_entry, name, coordinator
        )
    )
    entities.append(
        AdaptiveCoverTimeSensorEntity(
            config_entry.entry_id,
            hass,
            config_entry,
            name,
            "Start Sun",
            "start",
            "mdi:sun-clock-outline",
            coordinator,
        )
    )
    entities.append(
        AdaptiveCoverTimeSensorEntity(
            config_entry.entry_id,
            hass,
            config_entry,
            name,
            "End Sun",
            "end",
            "mdi:sun-clock",
            coordinator,
        )
    )
    entities.append(
        AdaptiveCoverControlSensorEntity(
            config_entry.entry_id, hass, config_entry, name, coordinator
        )
    )

    # Diagnostic sensors (if enabled)
    if config_entry.options.get(CONF_ENABLE_DIAGNOSTICS, False):
        # P0: Solar position sensors
        entities.append(
            AdaptiveCoverDiagnosticSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Sun Azimuth",
                "sun_azimuth",
                "°",
                "mdi:compass-outline",
                SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            AdaptiveCoverDiagnosticSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Sun Elevation",
                "sun_elevation",
                "°",
                "mdi:angle-acute",
                SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            AdaptiveCoverDiagnosticSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Gamma",
                "gamma",
                "°",
                "mdi:angle-right",
                SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            AdaptiveCoverDiagnosticEnumSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Control Status",
                "control_status",
                "mdi:information-outline",
            )
        )
        entities.append(
            AdaptiveCoverDiagnosticSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Calculated Position",
                "calculated_position",
                PERCENTAGE,
                "mdi:calculator",
                SensorStateClass.MEASUREMENT,
            )
        )

        # P0: Last Cover Action
        entities.append(
            AdaptiveCoverLastActionSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
            )
        )

        # P1: Position Verification sensors (disabled by default)
        entities.append(
            AdaptiveCoverLastVerificationSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
            )
        )
        entities.append(
            AdaptiveCoverRetryCountSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
            )
        )

        # P1: Advanced diagnostic sensors (disabled by default)
        # Only add climate-specific sensors if climate mode is enabled
        if config_entry.options.get(CONF_CLIMATE_MODE, False):
            # Active Temperature sensor
            entities.append(
                AdaptiveCoverAdvancedDiagnosticSensor(
                    config_entry.entry_id,
                    hass,
                    config_entry,
                    name,
                    coordinator,
                    "Active Temperature",
                    "active_temperature",
                    None,  # Unit will be determined by HA
                    "mdi:thermometer",
                    SensorStateClass.MEASUREMENT,
                    SensorDeviceClass.TEMPERATURE,
                )
            )

            # Climate Conditions sensor
            entities.append(
                AdaptiveCoverAdvancedDiagnosticEnumSensor(
                    config_entry.entry_id,
                    hass,
                    config_entry,
                    name,
                    coordinator,
                    "Climate Conditions",
                    "climate_conditions",
                    "mdi:weather-partly-cloudy",
                )
            )

        # Time Window Status sensor (always created if diagnostics enabled)
        entities.append(
            AdaptiveCoverAdvancedDiagnosticEnumSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Time Window Status",
                "time_window",
                "mdi:clock-check-outline",
            )
        )

        # Sun Validity Status sensor (always created if diagnostics enabled)
        entities.append(
            AdaptiveCoverAdvancedDiagnosticEnumSensor(
                config_entry.entry_id,
                hass,
                config_entry,
                name,
                coordinator,
                "Sun Validity Status",
                "sun_validity",
                "mdi:weather-sunny-alert",
            )
        )

    async_add_entities(entities)


class AdaptiveCoverSensorEntity(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], SensorEntity
):
    """Adaptive Cover Pro Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:sun-compass"
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        hass,
        config_entry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ) -> None:
        """Initialize adaptive_cover Sensor."""
        super().__init__(coordinator=coordinator)
        self.type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        self.coordinator = coordinator
        self.data = self.coordinator.data
        self._sensor_name = "Cover Position"
        self._attr_unique_id = f"{unique_id}_{self._sensor_name}"
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self._device_name = self.type[self.config_entry.data[CONF_SENSOR_TYPE]]
        self._device_id = unique_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.data = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return self._sensor_name

    @property
    def native_value(self) -> str | None:
        """Handle when entity is added."""
        return self.data.states["state"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_id)},
            name=self._name,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:  # noqa: D102
        return self.data.attributes


class AdaptiveCoverTimeSensorEntity(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], SensorEntity
):
    """Adaptive Cover Pro Time Sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        hass,
        config_entry,
        name: str,
        sensor_name: str,
        key: str,
        icon: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ) -> None:
        """Initialize adaptive_cover Sensor."""
        super().__init__(coordinator=coordinator)
        self.type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        self._attr_icon = icon
        self.key = key
        self.coordinator = coordinator
        self.data = self.coordinator.data
        self._attr_unique_id = f"{unique_id}_{sensor_name}"
        self._device_id = unique_id
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self._cover_type = self.config_entry.data["sensor_type"]
        self._sensor_name = sensor_name
        self._device_name = self.type[config_entry.data[CONF_SENSOR_TYPE]]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.data = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return self._sensor_name

    @property
    def native_value(self) -> str | None:
        """Handle when entity is added."""
        return self.data.states[self.key]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_id)},
            name=self._name,
        )


class AdaptiveCoverControlSensorEntity(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], SensorEntity
):
    """Adaptive Cover Pro Control method Sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "control"

    def __init__(
        self,
        unique_id: str,
        hass,
        config_entry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ) -> None:
        """Initialize adaptive_cover Sensor."""
        super().__init__(coordinator=coordinator)
        self.type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        self.coordinator = coordinator
        self.data = self.coordinator.data
        self._sensor_name = "Control Method"
        self._attr_unique_id = f"{unique_id}_{self._sensor_name}"
        self._device_id = unique_id
        self.id = unique_id
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self._cover_type = self.config_entry.data["sensor_type"]
        self._device_name = self.type[config_entry.data[CONF_SENSOR_TYPE]]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.data = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return self._sensor_name

    @property
    def native_value(self) -> str | None:
        """Handle when entity is added."""
        return self.data.states["control"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_id)},
            name=self._name,
        )


class AdaptiveCoverDiagnosticSensor(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], SensorEntity
):
    """Adaptive Cover Pro Diagnostic Sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
        sensor_name: str,
        diagnostic_key: str,
        unit: str | None,
        icon: str,
        state_class: SensorStateClass | None = None,
    ) -> None:
        """Initialize diagnostic sensor."""
        super().__init__(coordinator=coordinator)
        self.coordinator = coordinator
        self.data = self.coordinator.data
        self._sensor_name = sensor_name
        self._diagnostic_key = diagnostic_key
        self._attr_unique_id = f"{unique_id}_{diagnostic_key}"
        self._device_id = unique_id
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_state_class = state_class
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self.type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        self._device_name = self.type[config_entry.data[CONF_SENSOR_TYPE]]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.data = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._sensor_name

    @property
    def native_value(self) -> float | int | None:
        """Return sensor value."""
        if self.data.diagnostics is None:
            return None
        return self.data.diagnostics.get(self._diagnostic_key)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_id)},
            name=self._name,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes for complex diagnostic data."""
        if self.data.diagnostics is None:
            return None

        # For sensors that have nested dict data, expose as attributes
        if self._diagnostic_key in ["time_window", "sun_validity"]:
            return self.data.diagnostics.get(self._diagnostic_key)

        return None


class AdaptiveCoverDiagnosticEnumSensor(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], SensorEntity
):
    """Adaptive Cover Pro Diagnostic Enum Sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
        sensor_name: str,
        diagnostic_key: str,
        icon: str,
    ) -> None:
        """Initialize diagnostic enum sensor."""
        super().__init__(coordinator=coordinator)
        self.coordinator = coordinator
        self.data = self.coordinator.data
        self._sensor_name = sensor_name
        self._diagnostic_key = diagnostic_key
        self._attr_unique_id = f"{unique_id}_{diagnostic_key}"
        self._device_id = unique_id
        self._attr_icon = icon
        self.hass = hass
        self.config_entry = config_entry
        self._name = name
        self.type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        self._device_name = self.type[config_entry.data[CONF_SENSOR_TYPE]]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.data = self.coordinator.data
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._sensor_name

    @property
    def native_value(self) -> str | None:
        """Return sensor value."""
        if self.data.diagnostics is None:
            return None
        return self.data.diagnostics.get(self._diagnostic_key)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._device_id)},
            name=self._name,
        )


class AdaptiveCoverAdvancedDiagnosticSensor(AdaptiveCoverDiagnosticSensor):
    """Advanced diagnostic sensor (P1 - disabled by default)."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        unique_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
        sensor_name: str,
        diagnostic_key: str,
        unit: str | None,
        icon: str,
        state_class: SensorStateClass | None = None,
        device_class: SensorDeviceClass | None = None,
    ) -> None:
        """Initialize advanced diagnostic sensor."""
        super().__init__(
            unique_id, hass, config_entry, name, coordinator,
            sensor_name, diagnostic_key, unit, icon, state_class
        )
        if device_class:
            self._attr_device_class = device_class

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
        if self.data.diagnostics is None:
            return None

        # For temperature sensor, add temperature details
        if self._diagnostic_key == "active_temperature":
            return self.data.diagnostics.get("temperature_details")

        return None


class AdaptiveCoverAdvancedDiagnosticEnumSensor(AdaptiveCoverDiagnosticEnumSensor):
    """Advanced diagnostic enum sensor (P1 - disabled by default)."""

    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> str | None:
        """Return computed state from dict data."""
        if self.data.diagnostics is None:
            return None

        data = self.data.diagnostics.get(self._diagnostic_key)
        if data is None:
            return None

        # Compute human-readable state from dict
        if self._diagnostic_key == "time_window":
            return "Active" if data.get("check_adaptive_time") else "Outside Window"
        elif self._diagnostic_key == "sun_validity":
            if not data.get("valid"):
                if data.get("in_blind_spot"):
                    return "In Blind Spot"
                elif not data.get("valid_elevation"):
                    return "Invalid Elevation"
                return "Invalid"
            return "Valid"
        elif self._diagnostic_key == "climate_conditions":
            if data.get("is_summer"):
                return "Summer Mode"
            elif data.get("is_winter"):
                return "Winter Mode"
            return "Intermediate"

        return str(data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return dict data as attributes."""
        if self.data.diagnostics is None:
            return None
        return self.data.diagnostics.get(self._diagnostic_key)


class AdaptiveCoverLastActionSensor(AdaptiveCoverAdvancedDiagnosticSensor):
    """Sensor showing the last cover action performed."""

    # Override parent class to enable by default (matches P0 classification and docs)
    _attr_entity_registry_enabled_default = True

    # Exclude from logbook/history to prevent clutter (diagnostic data, not activity tracking)
    _attr_native_unit_of_measurement = ""  # Empty string triggers logbook exclusion

    def __init__(
        self,
        config_entry_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ):
        """Initialize the sensor."""
        super().__init__(
            config_entry_id,
            hass,
            config_entry,
            name,
            coordinator,
            "Last Cover Action",
            "last_cover_action",
            None,  # unit (text sensor has no unit)
            "mdi:history",
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if not self.data or not self.data.diagnostics:
            return None

        action = self.data.diagnostics.get("last_cover_action")
        if not action or not action.get("entity_id"):
            return "No action recorded"

        # Format: "service → entity at timestamp"
        service = action.get("service", "unknown")
        entity = action.get("entity_id", "unknown")
        timestamp_str = action.get("timestamp", "")

        # Parse and format timestamp to be more readable
        if timestamp_str:
            try:
                from homeassistant import util as dt_util

                ts = dt_util.parse_datetime(timestamp_str)
                if ts:
                    time_str = ts.strftime("%H:%M:%S")
                    return f"{service} → {entity.split('.')[-1]} at {time_str}"
            except (ValueError, AttributeError):
                pass

        return f"{service} → {entity.split('.')[-1]}"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if not self.data or not self.data.diagnostics:
            return None

        action = self.data.diagnostics.get("last_cover_action")
        if not action or not action.get("entity_id"):
            return None

        attrs = {
            "entity_id": action.get("entity_id"),
            "service": action.get("service"),
            "position": action.get("position"),
            "calculated_position": action.get("calculated_position"),
            "inverse_state_applied": action.get("inverse_state_applied", False),
            "timestamp": action.get("timestamp"),
            "covers_controlled": action.get("covers_controlled", 1),
        }

        # Only include threshold for open/close-only covers
        if action.get("threshold_used") is not None:
            attrs["threshold_used"] = action.get("threshold_used")
            attrs["threshold_comparison"] = (
                f"{action.get('calculated_position')} >= {action.get('threshold_used')}"
            )

        return attrs


class AdaptiveCoverLastVerificationSensor(AdaptiveCoverAdvancedDiagnosticSensor):
    """Sensor showing when position was last verified."""

    _attr_entity_registry_enabled_default = False  # P1 sensor
    _attr_native_unit_of_measurement = ""  # Exclude from logbook

    def __init__(
        self,
        config_entry_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ):
        """Initialize the sensor."""
        super().__init__(
            config_entry_id,
            hass,
            config_entry,
            name,
            coordinator,
            "Last Position Verification",
            "last_position_verification",
            None,
            "mdi:clock-check-outline",
            None,
            SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self):
        """Return last verification time."""
        # Return the most recent verification time from all entities
        if not self.coordinator._last_verification:
            return None
        return max(self.coordinator._last_verification.values())

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator._last_verification:
            return None

        return {
            "per_entity": {
                entity_id: time.isoformat()
                for entity_id, time in self.coordinator._last_verification.items()
            }
        }


class AdaptiveCoverRetryCountSensor(AdaptiveCoverAdvancedDiagnosticSensor):
    """Sensor showing current retry count for position verification."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False  # P1 sensor
    _attr_native_unit_of_measurement = ""  # Exclude from logbook

    def __init__(
        self,
        config_entry_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ):
        """Initialize the sensor."""
        super().__init__(
            config_entry_id,
            hass,
            config_entry,
            name,
            coordinator,
            "Position Verification Retries",
            "position_verification_retries",
            None,
            "mdi:refresh",
        )

    @property
    def native_value(self):
        """Return retry count."""
        # Return the maximum retry count from all entities
        if not self.coordinator._retry_counts:
            return 0
        return max(self.coordinator._retry_counts.values())

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional attributes."""
        return {
            "max_retries": self.coordinator._max_retries,
            "retries_remaining": max(
                0,
                self.coordinator._max_retries
                - max(self.coordinator._retry_counts.values(), default=0),
            ),
            "per_entity": dict(self.coordinator._retry_counts),
        }
