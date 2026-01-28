# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Adaptive Cover Pro** is a Home Assistant custom integration that automatically controls vertical blinds, horizontal awnings, and tilted/venetian blinds based on the sun's position. It calculates optimal positions to filter direct sunlight while maximizing natural light and supporting climate-aware operation.

**Language:** Python 3.11+
**Framework:** Home Assistant Core (async architecture)
**Version:** 2.0.1 (requires Home Assistant 2024.5.0+)

## Development Commands

### Setup
```bash
./scripts/setup              # Install dev dependencies and setup pre-commit hooks
```

### Linting
```bash
./scripts/lint               # Run ruff linting with auto-fix
ruff check . --fix           # Direct ruff invocation
ruff format .                # Format code
```

### Development Server
```bash
./scripts/develop            # Start Home Assistant in debug mode with this integration loaded
```

The development server:
- Creates `config/` directory if not present
- Sets `PYTHONPATH` to include `custom_components/`
- Starts Home Assistant with debug logging
- Uses `config/configuration.yaml` for test setup with mock entities

### Pre-commit
Pre-commit hooks run automatically on commit:
- Ruff linting and formatting
- Prettier for YAML/JSON
- Trailing whitespace cleanup

## Architecture

This integration follows Home Assistant's **Data Coordinator Pattern**:

### Core Components

**`coordinator.py` (939 lines)** - Central hub for all state management
- `AdaptiveDataUpdateCoordinator` manages async updates, entity listeners, and position calculations
- Tracks state changes from sun position, temperature, weather, presence entities
- Handles manual override detection and control
- Orchestrates position calculations and cover service calls

**`calculation.py` (596 lines)** - Position calculation algorithms
- `AdaptiveVerticalCover` - Up/down blind calculations
- `AdaptiveHorizontalCover` - In/out awning calculations
- `AdaptiveTiltCover` - Slat rotation calculations
- `NormalCoverState` - Basic sun position mode
- `ClimateCoverState` - Climate-aware mode with temperature/presence/weather

**`config_flow.py` (896 lines)** - Multi-step UI configuration
- Separate flows for vertical/horizontal/tilt cover types
- Common options, automation settings, climate mode, blind spots
- Option validation and context-aware forms

### Platform Files

Each platform file registers entities with Home Assistant:
- `sensor.py` - Position, control method, start/end sun times
- `switch.py` - Automatic control, climate mode, manual override detection
- `binary_sensor.py` - Sun visibility, manual override status
- `button.py` - Manual override reset

### Supporting Modules

- `sun.py` - Solar data using Astral library (azimuth, elevation, sunrise/sunset)
- `helpers.py` - State/attribute access utilities
- `config_context_adapter.py` - Logging with config context
- `const.py` - Constants and enums
- `diagnostics.py` - Diagnostics export

## Data Flow

1. **Initialization:** Config flow creates `ConfigEntry` → coordinator setup
2. **Listeners:** Coordinator registers listeners on sun, temperature, weather, presence entities
3. **State Change:** Entity change triggers `async_check_entity_state_change()`
4. **Calculation:** `_async_update_data()` calls appropriate cover class to calculate position
5. **Update:** Coordinator updates data → platform entities refresh
6. **Control:** If enabled and not manually overridden → calls cover service to move blinds

## Cover Types and Modes

### Cover Types
- **Vertical** (`cover_blind`) - Up/down movement
- **Horizontal** (`cover_awning`) - In/out movement
- **Tilt** (`cover_tilt`) - Slat rotation

### Operation Modes
- **Basic Mode** - Sun position-based calculation only
- **Climate Mode** - Enhanced with temperature, presence, weather
  - Winter strategy: Open fully when cold and sunny
  - Summer strategy: Close fully when hot
  - Intermediate: Use calculated position with weather awareness

## Configuration Structure

Config is stored in two layers:

**`config_entry.data`** (setup phase):
- `name` - Instance name
- `sensor_type` - cover_blind/cover_awning/cover_tilt

**`config_entry.options`** (configurable):
- Window azimuth, field of view, elevation limits
- Cover-specific dimensions (height, length, slat properties)
- Automation settings (delta position/time, start/end times, manual override)
- Climate settings (temperature entities/thresholds, presence, weather)
- Light settings (lux/irradiance entities and thresholds)
- Blind spot areas

## Key Design Patterns

1. **Async-first** - All I/O is async (state tracking, cover commands)
2. **State Listener Pattern** - Tracks external entity changes
3. **Manager Pattern** - `AdaptiveCoverManager` handles manual override tracking
4. **Entity Platform Pattern** - Separate platform files register entities
5. **Config Flow Pattern** - Multi-step UI-based configuration

## Testing

### Manual Testing
- Use `./scripts/develop` to start test instance
- Test config available in `config/configuration.yaml` with mock entities
- Access Home Assistant UI at http://localhost:8123

### Jupyter Notebooks
- `notebooks/test_env.ipynb` - Algorithm testing and visualization
- Requires matplotlib and pvlib for simulation plots

### Simulation
- `custom_components/adaptive_cover_pro/simulation/` contains simulation tools
- Generate position plots over time for different configurations

## File Organization

```
custom_components/adaptive_cover_pro/
├── __init__.py              # Integration entry point
├── coordinator.py           # Data coordinator (primary hub)
├── calculation.py           # Position calculation engine
├── config_flow.py           # Configuration UI
├── sensor.py                # Sensor platform
├── switch.py                # Switch platform
├── binary_sensor.py         # Binary sensor platform
├── button.py                # Button platform
├── sun.py                   # Solar calculations
├── helpers.py               # Utility functions
├── const.py                 # Constants
├── config_context_adapter.py # Logging adapter
├── diagnostics.py           # Diagnostics export
├── manifest.json            # Integration metadata
├── translations/            # i18n files (13 languages)
├── blueprints/              # Automation blueprints
└── simulation/              # Testing and simulation tools
```

## Dependencies

**Production:**
- `homeassistant~=2024.5` - Core framework
- `pandas~=2.2` - Solar data calculations
- `astral` - Sun position/timing

**Development:**
- `ruff~=0.4` - Linting and formatting (replaces black, isort, flake8)
- `pre-commit~=3.7` - Git hooks
- `pvlib~=0.11` - Photovoltaic simulations
- `matplotlib~=3.9` - Plotting for simulations

## Important Notes

### Ruff Configuration
Ruff is configured in `pyproject.toml` with:
- `select = ["ALL"]` - Enable all rules by default
- Specific ignores for formatter conflicts and false positives
- Home Assistant import conventions (cv, dr, er, ir, vol)
- Force sorting within sections for imports

### Home Assistant Patterns
- Never block the event loop - use async/await
- Use coordinator pattern for entity updates
- Follow entity naming: `{domain}.{type}_{description}_{name}`
- Store data in `coordinator.data` for entity access
- Use `_handle_coordinator_update()` in entities

### Manual Override Detection
The integration tracks when users manually change cover positions:
- Compares actual position to calculated position
- Configurable threshold and duration
- Option to reset timer on subsequent changes
- Reset button available to clear override status

### Climate Mode Weather States
Default sunny weather states: `sunny`, `windy`, `partlycloudy`, `cloudy`
- Configurable in weather options
- Used to determine if calculated position should be used vs. default
