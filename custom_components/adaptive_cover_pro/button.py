"""Button platform for the Adaptive Cover Pro integration."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import _LOGGER, CONF_ENTITIES, DOMAIN
from .coordinator import AdaptiveDataUpdateCoordinator
from .entity_base import AdaptiveCoverBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: AdaptiveDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    reset_manual = AdaptiveCoverButton(
        config_entry.entry_id, hass, config_entry, coordinator
    )

    buttons = []

    entities = config_entry.options.get(CONF_ENTITIES, [])
    if len(entities) >= 1:
        buttons = [reset_manual]

    async_add_entities(buttons)


class AdaptiveCoverButton(AdaptiveCoverBaseEntity, ButtonEntity):
    """Representation of a adaptive cover button."""

    _attr_icon = "mdi:cog-refresh-outline"

    def __init__(
        self,
        entry_id: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: AdaptiveDataUpdateCoordinator,
    ) -> None:
        """Initialize the button."""
        super().__init__(entry_id, hass, config_entry, coordinator)
        self._attr_unique_id = f"{entry_id}_Reset Manual Override"
        self._button_name = "Reset Manual Override"
        self._entities = config_entry.options.get(CONF_ENTITIES, [])

    @property
    def name(self):
        """Name of the entity."""
        return self._button_name

    async def async_press(self) -> None:
        """Handle the button press."""
        for entity in self._entities:
            if self.coordinator.manager.is_cover_manual(entity):
                _LOGGER.debug("Resetting manual override for: %s", entity)

                # Check if delta is sufficient before moving
                target_position = self.coordinator.state
                options = self.coordinator.config_entry.options
                if self.coordinator.check_position_delta(
                    entity, target_position, options
                ):
                    await self.coordinator.async_set_position(entity, target_position)
                    while self.coordinator.wait_for_target.get(entity):
                        await asyncio.sleep(1)
                else:
                    _LOGGER.debug(
                        "Manual override reset: delta too small for %s, skipping position change",
                        entity,
                    )

                self.coordinator.manager.reset(entity)
            else:
                _LOGGER.debug(
                    "Resetting manual override for %s is not needed since it is already auto-controlled",
                    entity,
                )
        await self.coordinator.async_refresh()
