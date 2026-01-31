"""Pytest fixtures for Adaptive Cover Pro tests."""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def hass():
    """Return a mock HomeAssistant instance."""
    hass_mock = MagicMock()
    hass_mock.states.get.return_value = None
    hass_mock.config.units.temperature_unit = "°C"
    return hass_mock


@pytest.fixture
def mock_logger():
    """Return a mock ConfigContextAdapter logger."""
    logger = MagicMock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_sun_data():
    """Return a mock SunData instance with predictable values."""
    sun_data = MagicMock()
    sun_data.sun_azimuth = 180.0
    sun_data.sun_elevation = 45.0
    sun_data.sun_position.return_value = (180.0, 45.0)
    return sun_data


@pytest.fixture
def sample_vertical_config():
    """Standard vertical cover configuration for testing."""
    return {
        "sol_azi": 180.0,
        "sol_elev": 45.0,
        "win_azi": 180,
        "fov_left": 45,
        "fov_right": 45,
        "win_elev": 90,
        "distance": 0.5,
        "h_def": 50,
        "d_top": 0.0,
        "d_bottom": 2.0,
        "max_pos": 100,
        "min_pos": 0,
        "blind_spot_config": {},
        "sunset_pos": 0,
        "sunset_off": 0,
    }


@pytest.fixture
def sample_horizontal_config():
    """Standard horizontal cover configuration for testing."""
    return {
        "sol_azi": 180.0,
        "sol_elev": 45.0,
        "win_azi": 180,
        "fov_left": 45,
        "fov_right": 45,
        "win_elev": 90,
        "distance": 0.5,
        "h_def": 100,
        "length": 2.0,
        "awning_angle": 0,
        "max_pos": 100,
        "min_pos": 0,
        "blind_spot_config": {},
        "sunset_pos": 0,
        "sunset_off": 0,
    }


@pytest.fixture
def sample_tilt_config():
    """Standard tilt cover configuration for testing."""
    return {
        "sol_azi": 180.0,
        "sol_elev": 45.0,
        "win_azi": 180,
        "fov_left": 45,
        "fov_right": 45,
        "win_elev": 90,
        "distance": 0.5,
        "h_def": 50,
        "slat_depth": 0.02,
        "slat_distance": 0.03,
        "tilt_mode": "mode1",
        "tilt_distance": 0.5,
        "max_pos": 100,
        "min_pos": 0,
        "blind_spot_config": {},
        "sunset_pos": 0,
        "sunset_off": 0,
    }


@pytest.fixture
def sample_climate_config():
    """Standard climate mode configuration for testing."""
    return {
        "temp_entity": "sensor.outside_temperature",
        "temp_low": 20.0,
        "temp_high": 25.0,
        "presence_entity": "binary_sensor.presence",
        "weather_entity": "weather.home",
        "weather_state": ["sunny", "partlycloudy"],
        "lux_entity": None,
        "lux_threshold": None,
        "irradiance_entity": None,
        "irradiance_threshold": None,
    }


@pytest.fixture
def mock_state():
    """Return a mock Home Assistant state object."""
    def _create_state(entity_id: str, state: str, attributes: dict | None = None):
        state_obj = MagicMock()
        state_obj.entity_id = entity_id
        state_obj.state = state
        state_obj.attributes = attributes or {}
        return state_obj
    return _create_state
