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
