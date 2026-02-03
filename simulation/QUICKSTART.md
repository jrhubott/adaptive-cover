# Flask Simulation - Quick Start Guide

## Installation

```bash
cd simulation
source ../venv/bin/activate  # Use project's virtual environment
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

Then open your browser to: http://localhost:5000

## What's Included

The application comes with 3 pre-configured example profiles:

1. **Living Room Vertical Blind** (South-facing, Nijmegen, Netherlands)
2. **Patio Horizontal Awning** (West-facing, Nijmegen, Netherlands)
3. **Bedroom Venetian Blinds** (East-facing, Nijmegen, Netherlands)

## Quick Test

To verify the simulation engine works correctly:

```bash
python test_simulation.py
```

This runs a summer solstice simulation and displays sample results.

## Usage Workflow

1. **View Profiles**: Home page lists all saved profiles
2. **Create/Edit**: Click "Create New Profile" or "Edit" on existing profile
3. **Run Simulation**: Click "Simulate" button, choose date and interval
4. **View Results**: Interactive Plotly charts show:
   - Cover position over time
   - Solar azimuth and elevation
   - Sun path diagram (polar chart)
   - Combined overview
5. **Export Data**: Download CSV or JSON for further analysis

## Features

- **No Database**: All profiles stored in `config/profiles.json`
- **Fast**: Uses same calculation engine as Home Assistant integration
- **Interactive**: Zoom, pan, and hover on charts
- **Three Cover Types**: Vertical blinds, horizontal awnings, tilt/venetian
- **Flexible Intervals**: 1, 5, 10, 15, or 30 minute data points
- **Full Day Coverage**: Automatically calculates from sunrise to sunset

## Configuration

Profiles support all integration parameters:
- Location (lat/long, timezone)
- Window geometry (azimuth, field of view)
- Cover-specific dimensions
- Position limits (min/max with optional sun-tracking mode)
- Elevation limits
- Sun timing offsets
- Climate mode (basic support)

## File Structure

```
simulation/
├── app.py                   # Main Flask application
├── requirements.txt         # Dependencies (Flask, Plotly, Astral, Pandas)
├── config/
│   └── profiles.json        # Saved profiles
├── lib/
│   ├── calculator.py        # Calculation engine wrapper
│   ├── solar.py             # Solar position calculations
│   ├── simulator.py         # Simulation execution
│   └── charts.py            # Plotly chart generation
└── templates/               # HTML templates
```

## Troubleshooting

**Port already in use:**
```bash
# Change port in app.py line: app.run(debug=True, port=5000)
```

**Import errors:**
```bash
# Make sure you're using the project's venv
source ../venv/bin/activate
pip install -r requirements.txt
```

**Incorrect calculations:**
- Verify latitude/longitude are correct
- Check timezone matches location
- Compare with Jupyter notebook for validation

## Next Steps

- Add more profiles for your specific locations
- Test different dates (solstices, equinoxes)
- Export data for comparison with actual cover behavior
- Use results to tune integration parameters
