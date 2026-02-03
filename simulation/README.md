# Adaptive Cover Pro - Simulation Web Application

A lightweight Flask web application for testing and visualizing the Adaptive Cover Pro calculation algorithms.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd simulation
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the web interface:**
   Open your browser to http://localhost:5000

## Features

- **Interactive Configuration:** Create and save cover profiles with visual forms
- **Full Day Simulation:** Run simulations across entire days with configurable intervals
- **Interactive Charts:** Plotly-powered visualizations with zoom, pan, and hover
- **Export Results:** Download simulation data as CSV or JSON
- **No Database Required:** All configuration stored in simple JSON files

## Usage

### Creating a Profile

1. Navigate to the home page
2. Click "Create New Profile"
3. Fill out the configuration form:
   - **Cover Type:** Vertical blind, horizontal awning, or tilt/venetian
   - **Location:** Latitude, longitude, timezone
   - **Window Geometry:** Azimuth, field of view, dimensions
   - **Position Limits:** Min/max positions and when to apply them
4. Save the profile

### Running a Simulation

1. Select a saved profile from the home page
2. Choose a date for simulation
3. Click "Simulate"
4. View interactive charts showing:
   - Cover position over time
   - Solar azimuth and elevation
   - Sun path diagram

### Exporting Results

From the results page, click:
- **Export CSV** - Comma-separated values for spreadsheet analysis
- **Export JSON** - Structured data for programmatic use

## Configuration Files

Profiles are stored in `config/profiles.json`:

```json
{
  "living_room_vertical": {
    "name": "Living Room Vertical Blind",
    "cover_type": "cover_blind",
    "latitude": 51.8,
    "longitude": 5.8,
    "timezone": "Europe/Amsterdam",
    "window_azimuth": 180,
    "fov_left": 90,
    "fov_right": 90,
    "window_height": 2.0,
    "distance": 0.5,
    "default_position": 60,
    "min_position": 0,
    "max_position": 100,
    "enable_min_position": false,
    "enable_max_position": false
  }
}
```

## Architecture

- **app.py** - Main Flask application with all routes
- **lib/solar.py** - Solar position calculations using Astral
- **lib/calculator.py** - Wrapper around main calculation engine
- **lib/simulator.py** - Simulation execution engine
- **lib/charts.py** - Plotly chart generation
- **templates/** - Flask HTML templates with Bootstrap
- **static/** - CSS and JavaScript files

## Integration

This application imports the calculation logic directly from the main integration:

```python
from custom_components.adaptive_cover_pro.calculation import (
    AdaptiveVerticalCover,
    AdaptiveHorizontalCover,
    AdaptiveTiltCover,
)
```

This ensures the simulation uses the exact same algorithms as the production integration.

## Troubleshooting

**Server won't start:**
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify you're in the `simulation/` directory
- Check for port conflicts on port 5000

**Charts not displaying:**
- Check browser console for JavaScript errors
- Ensure Plotly CDN is accessible
- Try refreshing the page

**Incorrect calculations:**
- Verify latitude/longitude are correct
- Check timezone matches location
- Compare with Jupyter notebook results

## Development

To modify the calculation logic, edit files in:
```
custom_components/adaptive_cover_pro/calculation.py
```

The simulation app will automatically use the updated code.
