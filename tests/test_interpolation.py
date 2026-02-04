"""Tests for custom position interpolation feature."""

import pytest
from unittest.mock import MagicMock

from custom_components.adaptive_cover_pro.coordinator import (
    AdaptiveDataUpdateCoordinator,
)


def create_mock_coordinator(start=None, end=None, normal_list=None, new_list=None):
    """Create mock coordinator with interpolation config."""
    coordinator = MagicMock(spec=AdaptiveDataUpdateCoordinator)
    coordinator.start_value = start
    coordinator.end_value = end
    coordinator.normal_list = normal_list
    coordinator.new_list = new_list

    # Bind the actual method
    coordinator.interpolate_states = (
        AdaptiveDataUpdateCoordinator.interpolate_states.__get__(coordinator)
    )

    return coordinator


class TestInterpolationSimpleMode:
    """Test simple mode interpolation (start/end values)."""

    def test_limited_range_blind(self):
        """Test mapping [0,100] -> [10,90] for limited range covers."""
        coordinator = create_mock_coordinator(start=10, end=90)

        assert coordinator.interpolate_states(0) == 10
        assert coordinator.interpolate_states(100) == 90
        assert coordinator.interpolate_states(50) == 50
        assert coordinator.interpolate_states(25) == pytest.approx(30, abs=0.1)

    def test_inverted_operation(self):
        """Test mapping [0,100] -> [100,0] for inversion."""
        coordinator = create_mock_coordinator(start=100, end=0)

        assert coordinator.interpolate_states(0) == 100
        assert coordinator.interpolate_states(100) == 0
        assert coordinator.interpolate_states(50) == 50
        assert coordinator.interpolate_states(25) == 75

    def test_offset_range(self):
        """Test mapping [0,100] -> [20,80]."""
        coordinator = create_mock_coordinator(start=20, end=80)

        assert coordinator.interpolate_states(0) == 20
        assert coordinator.interpolate_states(100) == 80
        assert coordinator.interpolate_states(50) == 50


class TestInterpolationListMode:
    """Test list mode interpolation (advanced)."""

    def test_linear_mapping(self):
        """Test list mode with linear mapping."""
        coordinator = create_mock_coordinator(
            normal_list=[0, 50, 100], new_list=[0, 50, 100]
        )

        assert coordinator.interpolate_states(0) == 0
        assert coordinator.interpolate_states(50) == 50
        assert coordinator.interpolate_states(100) == 100

    def test_nonlinear_aggressive_closing(self):
        """Test non-linear mapping for aggressive closing behavior."""
        coordinator = create_mock_coordinator(
            normal_list=[0, 25, 50, 75, 100], new_list=[0, 15, 35, 60, 100]
        )

        assert coordinator.interpolate_states(0) == 0
        assert coordinator.interpolate_states(25) == 15
        assert coordinator.interpolate_states(50) == 35
        assert coordinator.interpolate_states(75) == 60
        assert coordinator.interpolate_states(100) == 100

    def test_inverted_list(self):
        """Test inverted list for reverse operation."""
        coordinator = create_mock_coordinator(
            normal_list=[0, 25, 50, 75, 100], new_list=[100, 75, 50, 25, 0]
        )

        assert coordinator.interpolate_states(0) == 100
        assert coordinator.interpolate_states(25) == 75
        assert coordinator.interpolate_states(50) == 50
        assert coordinator.interpolate_states(75) == 25
        assert coordinator.interpolate_states(100) == 0


class TestInterpolationEdgeCases:
    """Test edge cases and error conditions."""

    def test_no_interpolation_configured(self):
        """Test that empty range returns original value."""
        coordinator = create_mock_coordinator()
        assert coordinator.interpolate_states(50) == 50

    def test_intermediate_values(self):
        """Test interpolation between defined points."""
        coordinator = create_mock_coordinator(start=10, end=90)
        result = coordinator.interpolate_states(33)
        assert pytest.approx(result, abs=0.5) == 36.4
