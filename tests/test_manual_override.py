"""Tests for manual override detection with grace period."""

import datetime as dt
from unittest.mock import MagicMock

import pytest


def test_is_in_grace_period_returns_false_when_no_timestamp():
    """Test that _is_in_grace_period returns False when no timestamp exists."""
    from custom_components.adaptive_cover_pro.const import COMMAND_GRACE_PERIOD_SECONDS

    # Create minimal mock coordinator
    coordinator = MagicMock()
    coordinator._command_grace_period_seconds = COMMAND_GRACE_PERIOD_SECONDS
    coordinator._command_timestamps = {}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call the method
    result = AdaptiveDataUpdateCoordinator._is_in_grace_period(
        coordinator, "cover.test"
    )

    assert result is False


def test_is_in_grace_period_returns_true_when_within_period():
    """Test that _is_in_grace_period returns True when within grace period."""
    from custom_components.adaptive_cover_pro.const import COMMAND_GRACE_PERIOD_SECONDS

    # Create minimal mock coordinator
    coordinator = MagicMock()
    coordinator._command_grace_period_seconds = COMMAND_GRACE_PERIOD_SECONDS
    now = dt.datetime.now().timestamp()
    coordinator._command_timestamps = {"cover.test": now}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call the method
    result = AdaptiveDataUpdateCoordinator._is_in_grace_period(
        coordinator, "cover.test"
    )

    assert result is True


def test_is_in_grace_period_returns_false_when_expired():
    """Test that _is_in_grace_period returns False when grace period expired."""
    from custom_components.adaptive_cover_pro.const import COMMAND_GRACE_PERIOD_SECONDS

    # Create minimal mock coordinator
    coordinator = MagicMock()
    coordinator._command_grace_period_seconds = COMMAND_GRACE_PERIOD_SECONDS
    # Set timestamp to 10 seconds ago (past the 5-second grace period)
    past = dt.datetime.now().timestamp() - 10
    coordinator._command_timestamps = {"cover.test": past}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call the method
    result = AdaptiveDataUpdateCoordinator._is_in_grace_period(
        coordinator, "cover.test"
    )

    assert result is False


@pytest.mark.asyncio
async def test_grace_period_timeout_clears_tracking():
    """Test that grace period timeout clears tracking data."""

    # Create minimal mock coordinator
    coordinator = MagicMock()
    coordinator._command_grace_period_seconds = 0.1  # Short period for testing
    coordinator._command_timestamps = {"cover.test": dt.datetime.now().timestamp()}
    coordinator._grace_period_tasks = {}
    coordinator.logger = MagicMock()

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call the timeout method
    await AdaptiveDataUpdateCoordinator._grace_period_timeout(
        coordinator, "cover.test"
    )

    # Verify tracking was cleared
    assert "cover.test" not in coordinator._command_timestamps
    assert "cover.test" not in coordinator._grace_period_tasks


def test_cancel_grace_period_removes_tracking():
    """Test that _cancel_grace_period removes all tracking data."""
    # Create minimal mock coordinator with active task
    coordinator = MagicMock()
    mock_task = MagicMock()
    mock_task.done.return_value = False
    coordinator._grace_period_tasks = {"cover.test": mock_task}
    coordinator._command_timestamps = {"cover.test": dt.datetime.now().timestamp()}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call cancel method
    AdaptiveDataUpdateCoordinator._cancel_grace_period(coordinator, "cover.test")

    # Verify task was cancelled
    mock_task.cancel.assert_called_once()

    # Verify tracking was cleared (the method modifies the dicts)
    assert "cover.test" not in coordinator._grace_period_tasks
    assert "cover.test" not in coordinator._command_timestamps


def test_cancel_grace_period_handles_completed_task():
    """Test that _cancel_grace_period handles already completed tasks."""
    # Create minimal mock coordinator with completed task
    coordinator = MagicMock()
    mock_task = MagicMock()
    mock_task.done.return_value = True  # Task already done
    coordinator._grace_period_tasks = {"cover.test": mock_task}
    coordinator._command_timestamps = {"cover.test": dt.datetime.now().timestamp()}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Call cancel method
    AdaptiveDataUpdateCoordinator._cancel_grace_period(coordinator, "cover.test")

    # Verify cancel was NOT called (task already done)
    mock_task.cancel.assert_not_called()

    # Verify tracking was still cleared
    assert "cover.test" not in coordinator._grace_period_tasks
    assert "cover.test" not in coordinator._command_timestamps


def test_cancel_grace_period_handles_missing_entity():
    """Test that _cancel_grace_period handles entities with no active grace period."""
    # Create minimal mock coordinator with empty tracking
    coordinator = MagicMock()
    coordinator._grace_period_tasks = {}
    coordinator._command_timestamps = {}

    # Import the method
    from custom_components.adaptive_cover_pro.coordinator import (
        AdaptiveDataUpdateCoordinator,
    )

    # Should not raise any exceptions
    AdaptiveDataUpdateCoordinator._cancel_grace_period(coordinator, "cover.test")

    # Tracking should still be empty
    assert "cover.test" not in coordinator._grace_period_tasks
    assert "cover.test" not in coordinator._command_timestamps
