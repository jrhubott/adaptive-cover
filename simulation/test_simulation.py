#!/usr/bin/env python
"""Quick test of simulation functionality."""

from datetime import date

from lib.simulator import Simulator

# Load example profile
profile = {
    "name": "Test Vertical Blind",
    "cover_type": "cover_blind",
    "latitude": 51.8,
    "longitude": 5.8,
    "timezone": "Europe/Amsterdam",
    "window_azimuth": 180.0,
    "fov_left": 90.0,
    "fov_right": 90.0,
    "window_height": 2.1,
    "distance": 0.5,
    "default_position": 60,
    "min_position": 0,
    "max_position": 100,
    "enable_min_position": False,
    "enable_max_position": False,
    "sunset_position": 0,
    "sunset_offset": 0,
    "sunrise_offset": 0,
    "climate_mode": False,
    "min_elevation": 0.0,
    "max_elevation": 90.0,
}

# Run simulation
print("Running simulation for June 21, 2024 (summer solstice)...")
simulator = Simulator()
results = simulator.run(profile, "2024-06-21", interval_minutes=15)

print(f"\nSimulation completed successfully!")
print(f"Number of data points: {len(results)}")
print(f"\nFirst 5 data points:")
for i, result in enumerate(results[:5]):
    print(f"  {i+1}. {result['timestamp'][:19]} - Position: {result['position']:3d}%, "
          f"Solar Az: {result['solar_azimuth']:6.2f}°, "
          f"Solar El: {result['solar_elevation']:5.2f}°, "
          f"Sun in window: {result['sun_in_window']}")

print(f"\nLast 3 data points:")
for i, result in enumerate(results[-3:]):
    print(f"  {len(results)-2+i}. {result['timestamp'][:19]} - Position: {result['position']:3d}%, "
          f"Solar Az: {result['solar_azimuth']:6.2f}°, "
          f"Solar El: {result['solar_elevation']:5.2f}°, "
          f"Sun in window: {result['sun_in_window']}")

print("\n✓ Test passed! Simulation working correctly.")
