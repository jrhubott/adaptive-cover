"""Simulation execution engine."""

import csv
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .calculator import CoverCalculator
from .solar import get_day_positions


class Simulator:
    """Execute full day simulations."""

    def __init__(self):
        """Initialize simulator."""
        self.calculator = CoverCalculator()
        self.results = []
        self.profile = None
        self.date = None

    def run(
        self,
        profile: dict,
        date_str: str,
        interval_minutes: int = 5,
    ) -> list[dict]:
        """
        Run simulation for a full day.

        Args:
            profile: Cover profile configuration
            date_str: Date string in YYYY-MM-DD format
            interval_minutes: Minutes between data points

        Returns:
            List of simulation data points
        """
        self.profile = profile
        self.date = date_str

        # Parse date and set timezone
        timezone = profile.get("timezone", "UTC")
        date = datetime.fromisoformat(date_str).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=ZoneInfo(timezone),
        )

        # Get solar positions for the day
        solar_positions = get_day_positions(
            profile["latitude"],
            profile["longitude"],
            date,
            interval_minutes,
        )

        # Calculate cover position for each solar position
        self.results = []
        for solar_pos in solar_positions:
            calc_result = self.calculator.calculate_position(
                profile,
                solar_pos["azimuth"],
                solar_pos["elevation"],
            )

            data_point = {
                "timestamp": solar_pos["timestamp"].isoformat(),
                "solar_azimuth": round(solar_pos["azimuth"], 2),
                "solar_elevation": round(solar_pos["elevation"], 2),
                "position": calc_result["position"],
                "sun_in_window": calc_result["sun_in_window"],
                "control_method": calc_result["control_method"],
            }

            self.results.append(data_point)

        return self.results

    def get_results(self) -> list[dict]:
        """Get simulation results."""
        return self.results

    def export_csv(self) -> str:
        """
        Export results as CSV string.

        Returns:
            CSV formatted string
        """
        if not self.results:
            return ""

        output = io.StringIO()
        fieldnames = self.results[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(self.results)

        return output.getvalue()

    def export_json(self) -> str:
        """
        Export results as JSON string.

        Returns:
            JSON formatted string
        """
        return json.dumps(
            {
                "profile": self.profile,
                "date": self.date,
                "results": self.results,
            },
            indent=2,
        )
