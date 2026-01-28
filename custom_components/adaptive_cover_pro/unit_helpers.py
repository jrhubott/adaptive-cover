"""Unit conversion helpers for Adaptive Cover Pro.

This module provides utilities for converting between metric and imperial/US customary
units based on Home Assistant's configured unit system. All values are stored internally
in metric units but displayed to users in their preferred unit system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import UnitOfLength, UnitOfTemperature
from homeassistant.util.unit_conversion import DistanceConverter, TemperatureConverter

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def is_metric(hass: HomeAssistant) -> bool:
    """Return True if Home Assistant is configured for metric units."""
    return hass.config.units.is_metric


def get_distance_unit(hass: HomeAssistant) -> str:
    """Get the distance unit for the current unit system (m or ft)."""
    return UnitOfLength.METERS if is_metric(hass) else UnitOfLength.FEET


def get_small_distance_unit(hass: HomeAssistant) -> str:
    """Get the small distance unit for the current unit system (cm or in)."""
    return UnitOfLength.CENTIMETERS if is_metric(hass) else UnitOfLength.INCHES


def get_temperature_unit(hass: HomeAssistant) -> str:
    """Get the temperature unit for the current unit system (°C or °F)."""
    return UnitOfTemperature.CELSIUS if is_metric(hass) else UnitOfTemperature.FAHRENHEIT


# Conversion functions for meters
def meters_to_display(hass: HomeAssistant, meters: float) -> float:
    """Convert meters to display units (meters or feet)."""
    if is_metric(hass):
        return meters
    return DistanceConverter.convert(
        meters, UnitOfLength.METERS, UnitOfLength.FEET
    )


def display_to_meters(hass: HomeAssistant, value: float) -> float:
    """Convert display units (meters or feet) to meters."""
    if is_metric(hass):
        return value
    return DistanceConverter.convert(
        value, UnitOfLength.FEET, UnitOfLength.METERS
    )


# Conversion functions for centimeters
def cm_to_display(hass: HomeAssistant, cm: float) -> float:
    """Convert centimeters to display units (centimeters or inches)."""
    if is_metric(hass):
        return cm
    return DistanceConverter.convert(
        cm, UnitOfLength.CENTIMETERS, UnitOfLength.INCHES
    )


def display_to_cm(hass: HomeAssistant, value: float) -> float:
    """Convert display units (centimeters or inches) to centimeters."""
    if is_metric(hass):
        return value
    return DistanceConverter.convert(
        value, UnitOfLength.INCHES, UnitOfLength.CENTIMETERS
    )


# Conversion functions for temperature
def celsius_to_display(hass: HomeAssistant, celsius: float) -> float:
    """Convert Celsius to display units (Celsius or Fahrenheit)."""
    if is_metric(hass):
        return celsius
    return TemperatureConverter.convert(
        celsius, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
    )


def display_to_celsius(hass: HomeAssistant, value: float) -> float:
    """Convert display units (Celsius or Fahrenheit) to Celsius."""
    if is_metric(hass):
        return value
    return TemperatureConverter.convert(
        value, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS
    )


# Configuration ranges for each field in metric units
METRIC_CONFIG = {
    "height": {"min": 0.1, "max": 6.0, "step": 0.1, "default": 2.1},
    "distance": {"min": 0.1, "max": 5.0, "step": 0.1, "default": 0.5},
    "length": {"min": 0.3, "max": 6.0, "step": 0.1, "default": 2.1},
    "slat_depth": {"min": 0.1, "max": 15.0, "step": 0.1, "default": 3.0},
    "slat_distance": {"min": 0.1, "max": 15.0, "step": 0.1, "default": 2.0},
    "temp_low": {"min": 0.0, "max": 86.0, "step": 0.5, "default": 21.0},
    "temp_high": {"min": 0.0, "max": 90.0, "step": 0.5, "default": 25.0},
}

# Configuration ranges for each field in imperial/US customary units
IMPERIAL_CONFIG = {
    "height": {"min": 0.3, "max": 20.0, "step": 0.1, "default": 7.0},
    "distance": {"min": 0.3, "max": 16.0, "step": 0.1, "default": 1.6},
    "length": {"min": 1.0, "max": 20.0, "step": 0.1, "default": 7.0},
    "slat_depth": {"min": 0.04, "max": 6.0, "step": 0.01, "default": 1.2},
    "slat_distance": {"min": 0.04, "max": 6.0, "step": 0.01, "default": 0.8},
    "temp_low": {"min": 32.0, "max": 187.0, "step": 1.0, "default": 70.0},
    "temp_high": {"min": 32.0, "max": 194.0, "step": 1.0, "default": 77.0},
}


def get_config_for_field(hass: HomeAssistant, field_name: str) -> dict[str, float]:
    """Get configuration ranges for a field based on the current unit system.

    Args:
        hass: Home Assistant instance
        field_name: One of: height, distance, length, slat_depth, slat_distance,
                   temp_low, temp_high

    Returns:
        Dictionary with keys: min, max, step, default

    """
    config = METRIC_CONFIG if is_metric(hass) else IMPERIAL_CONFIG
    if field_name not in config:
        msg = f"Unknown field name: {field_name}"
        raise ValueError(msg)
    return config[field_name]
