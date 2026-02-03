"""Solar position calculations using Astral library."""

from datetime import datetime, timedelta

from astral import LocationInfo
from astral import sun as astral_sun


def get_solar_position(latitude: float, longitude: float, dt: datetime) -> tuple[float, float]:
    """
    Calculate solar azimuth and elevation for a specific time.

    Args:
        latitude: Location latitude in degrees
        longitude: Location longitude in degrees
        dt: Datetime with timezone info

    Returns:
        Tuple of (azimuth, elevation) in degrees
    """
    location = LocationInfo(latitude=latitude, longitude=longitude)
    observer = location.observer

    solar_azimuth = astral_sun.azimuth(observer, dt)
    solar_elevation = astral_sun.elevation(observer, dt)

    return solar_azimuth, solar_elevation


def get_day_positions(
    latitude: float,
    longitude: float,
    date: datetime,
    interval_minutes: int = 5,
) -> list[dict]:
    """
    Calculate solar positions for an entire day.

    Args:
        latitude: Location latitude in degrees
        longitude: Location longitude in degrees
        date: Date to calculate (time component ignored)
        interval_minutes: Minutes between data points

    Returns:
        List of dicts with timestamp, azimuth, elevation
    """
    location = LocationInfo(latitude=latitude, longitude=longitude)
    observer = location.observer

    # Get sunrise and sunset for this date
    try:
        sunrise_time = astral_sun.sunrise(observer, date)
        sunset_time = astral_sun.sunset(observer, date)
    except Exception:
        # If sunrise/sunset calculation fails (polar regions), use full day
        sunrise_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        sunset_time = date.replace(hour=23, minute=59, second=59, microsecond=0)

    positions = []
    current_time = sunrise_time

    while current_time <= sunset_time:
        solar_azimuth, solar_elevation = get_solar_position(latitude, longitude, current_time)

        positions.append({
            "timestamp": current_time,
            "azimuth": solar_azimuth,
            "elevation": solar_elevation,
        })

        current_time += timedelta(minutes=interval_minutes)

    return positions


def get_sunrise_sunset(latitude: float, longitude: float, date: datetime) -> tuple[datetime, datetime]:
    """
    Get sunrise and sunset times for a location and date.

    Args:
        latitude: Location latitude in degrees
        longitude: Location longitude in degrees
        date: Date to calculate

    Returns:
        Tuple of (sunrise, sunset) datetime objects
    """
    location = LocationInfo(latitude=latitude, longitude=longitude)
    observer = location.observer

    sunrise_time = astral_sun.sunrise(observer, date)
    sunset_time = astral_sun.sunset(observer, date)

    return sunrise_time, sunset_time
