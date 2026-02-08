# Adaptive Cover Pro - Architecture

## Overview

Adaptive Cover Pro is a Home Assistant custom integration that automatically controls blinds, awnings, and venetian blinds based on sun position, using the **Data Coordinator Pattern** for state management.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Home Assistant Core                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  Config Flow (UI Setup)                         │
│  - Multi-step wizard for vertical/horizontal/tilt covers       │
│  - Options flow for configuration updates                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              AdaptiveDataUpdateCoordinator                      │
│  - Central state management hub                                 │
│  - Tracks sun position, temperature, weather, presence          │
│  - Orchestrates position calculations                           │
│  - Detects manual overrides                                     │
│  - Calls cover services                                         │
└─────┬───────────────────┬───────────────────┬───────────────────┘
      │                   │                   │
┌─────▼─────┐   ┌─────────▼──────┐   ┌───────▼────────┐
│ Services  │   │  Calculation   │   │   Entities     │
│ Layer     │   │     Engine     │   │   (Platform)   │
└───────────┘   └────────────────┘   └────────────────┘
```

## Core Components

### 1. Coordinator (`coordinator.py`)

**Role:** Central orchestrator for state management and entity updates

**Responsibilities:**
- Registers listeners on sun, temperature, weather, presence entities
- Triggers calculations when state changes
- Detects manual override (user manually moved cover)
- Calls cover services to move blinds
- Manages automation schedules (start/end times)
- Provides diagnostic data

**Data Flow:**
```
Entity State Change → Listener → coordinator._async_update_data()
    → Calculate Position → Update coordinator.data
    → Entities auto-refresh → Call cover service (if enabled)
```

### 2. Services Layer (`services/`)

**Purpose:** Extract focused responsibilities from coordinator

**Services:**
- **ConfigurationService** - Parses config entries, extracts parameters
  - Handles vertical/horizontal/tilt-specific configuration
  - Converts units (cm → meters for tilt slats)
  - Provides climate mode configuration

*(Note: Additional services planned for future phases: temperature, presence, weather, capability detection, position verification)*

### 3. Calculation Engine (`calculation.py`)

**Purpose:** Calculate optimal cover positions based on sun geometry

**Classes:**

#### AdaptiveGeneralCover (Base Class)
- Shared sun position calculations
- Field of view (FOV) validation
- Elevation limits
- Blind spot detection
- Direct sun validity checks

#### AdaptiveVerticalCover
- **Purpose:** Up/down blinds (vertical movement)
- **Algorithm:** Projects sun rays to calculate required blind height
- **Features:**
  - Enhanced geometric accuracy with safety margins
  - Edge case handling (extreme angles)
  - Optional window depth support
- **Output:** Blind height in meters → converted to percentage

#### AdaptiveHorizontalCover
- **Purpose:** In/out awnings (horizontal projection)
- **Algorithm:** Uses vertical calculation + trigonometry for horizontal extension
- **Output:** Awning extension length → converted to percentage

#### AdaptiveTiltCover
- **Purpose:** Slat rotation for venetian blinds
- **Algorithm:** Calculates optimal slat angle to block sun while allowing light
- **Output:** Slat angle in degrees → converted to percentage

#### State Classes
- **NormalCoverState** - Basic sun position mode
- **ClimateCoverState** - Climate-aware mode (temperature, presence, weather)
  - Winter: Open for solar heating
  - Summer: Close for heat blocking
  - Presence-aware: Different strategies when home vs away

### 4. Utility Modules

#### `position_utils.py`
- **PositionConverter**: Unified percentage conversion and limit application
- Eliminates code duplication across cover types
- Handles min/max position constraints

#### `geometry.py`
- **SafetyMarginCalculator**: Angle-dependent safety margins
- **EdgeCaseHandler**: Safe fallbacks for extreme sun angles
- 100% test coverage

#### `enums.py`
- Type-safe enumerations (CoverType, TiltMode, ClimateStrategy, etc.)
- Replaces string comparisons
- Provides display names and utility methods

#### `const.py`
- Named constants for all magic numbers
- Geometric thresholds (2°, 85°, 88°)
- Safety margin multipliers (0.2, 0.15, 0.1)
- Climate defaults (45°, 80° tilt angles)

### 5. Entity Base Classes (`entity_base.py`)

**Purpose:** Eliminate duplication across platform files

**Classes:**
- **AdaptiveCoverBaseEntity** - Common device_info, coordinator handling
- **AdaptiveCoverSensorBase** - Base for sensors
- **AdaptiveCoverDiagnosticSensorBase** - Base for diagnostic sensors

**Benefit:** Single source of truth for device information and coordinator updates

### 6. Platform Entities

**Sensor Platform** (`sensor.py`):
- Cover Position (0-100%)
- Start/End Sun Times
- Control Method (direct/summer/winter/default)
- Diagnostic sensors (P0: sun azimuth/elevation, P1: advanced diagnostics)

**Switch Platform** (`switch.py`):
- Automatic Control (on/off)
- Climate Mode (on/off)
- Manual Override (on/off) + reset button

**Binary Sensor Platform** (`binary_sensor.py`):
- Sun Visibility (in window FOV)
- Position Mismatch (for diagnostics)

**Button Platform** (`button.py`):
- Manual Override Reset

## Data Flow

### 1. Initialization
```
Config Entry Created
    → coordinator.__init__()
        → ConfigurationService created
        → Register state listeners
        → Initial calculation
```

### 2. State Update Cycle
```
Sun moves OR Temperature changes OR Weather changes
    → Entity state change event
    → coordinator.async_check_entity_state_change()
        → coordinator._async_update_data()
            → Extract config with ConfigurationService
            → Calculate position with AdaptiveXXXCover
            → Apply limits with PositionConverter
            → Build diagnostic data
            → Return AdaptiveCoverData
        → coordinator.data updated
        → All entities notified via _handle_coordinator_update()
        → Entities call async_write_ha_state()
```

### 3. Cover Control
```
coordinator._async_update_data() completes
    → Check if automatic control enabled
    → Check if position delta sufficient
    → Check if time delta sufficient
    → Check if manual override active
    → If all checks pass:
        → coordinator.async_set_position()
            → Call cover.set_cover_position service
```

## Configuration Structure

### `config_entry.data` (Setup Phase)
- `name` - Instance name
- `sensor_type` - cover_blind/cover_awning/cover_tilt

### `config_entry.options` (User Configurable)

**Window Properties:**
- `set_azimuth` - Window facing direction (0-360°)
- `fov_left`, `fov_right` - Field of view
- `min_elevation`, `max_elevation` - Sun elevation limits
- `window_height`, `distance_shaded_area` - Dimensions
- `window_depth` - Optional reveal/frame depth (Phase 1 v2.7.0+)

**Position Limits:**
- `min_position`, `max_position` - Absolute boundaries (0-100%)
- `enable_min_position`, `enable_max_position` - When limits apply

**Automation:**
- `delta_position` - Minimum position change to trigger movement
- `delta_time` - Minimum time between movements
- `start_time`, `end_time` - Operational time windows
- `manual_override_duration` - How long to pause after manual change
- `manual_threshold` - Position difference to detect manual override

**Climate Mode:**
- `temp_entity`, `presence_entity`, `weather_entity` - Sensor entities
- `temp_low`, `temp_high` - Temperature thresholds
- `weather_state` - Sunny weather conditions list
- `lux_entity`, `lux_threshold` - Light level sensors
- `irradiance_entity`, `irradiance_threshold` - Solar irradiance sensors

**Blind Spots:**
- `blind_spot_left`, `blind_spot_right` - Area to ignore within FOV
- `blind_spot_elevation` - Maximum elevation for blind spot

## Extension Points

### Adding New Cover Types
1. Create new dataclass extending `AdaptiveGeneralCover`
2. Implement `calculate_position()` method
3. Implement `calculate_percentage()` method
4. Add CoverType enum value
5. Update coordinator to handle new type

### Adding New Climate Strategies
1. Create strategy class (future: when strategy pattern is extracted)
2. Implement `calculate_position()` logic
3. Register in ClimateStrategy enum

### Adding New Services
1. Create service class in `services/` directory
2. Inject into coordinator.__init__()
3. Update coordinator to use service methods
4. Add tests for service

## Testing Strategy

### Unit Tests
- **calculation.py**: 91% coverage, 146 tests
  - Position calculations
  - Percentage conversions
  - Safety margins
  - Edge cases
- **geometry.py**: 100% coverage
- **position_utils.py**: 100% coverage
- **helpers.py**: 100% coverage (inverse state tests)

### Integration Tests
- Manual override detection
- Climate mode behavior
- Time window validation
- Entity state updates

## Performance Considerations

1. **Calculation Efficiency**: Numpy operations for fast trigonometry
2. **State Caching**: Coordinator caches configuration to avoid repeated parsing
3. **Delta Checking**: Prevents unnecessary cover movements
4. **Async Architecture**: Non-blocking I/O for all state changes

## Future Architecture Improvements

### Phase 4: Coordinator Decomposition (Planned)
Extract remaining responsibilities into focused services:
- Cover capability detection
- Position verification
- Time window management
- State change handling

### Phase 5: Climate Data Decomposition (Planned)
Split ClimateCoverData into:
- Temperature service
- Presence service
- Weather/light service
- Climate facade

## Dependencies

**Core:**
- `homeassistant` - Home Assistant framework
- `pandas` - Solar data calculations
- `numpy` - Fast mathematical operations
- `astral` - Sun position/timing

**Development:**
- `pytest` - Testing framework
- `ruff` - Linting and formatting

## File Organization

```
adaptive-cover/
├── custom_components/adaptive_cover_pro/
│   ├── __init__.py              # Integration entry point
│   ├── coordinator.py           # Data coordinator (central hub)
│   ├── calculation.py           # Position calculation engine
│   ├── config_flow.py           # Configuration UI
│   │
│   ├── services/                # Service layer (Phase 6+)
│   │   ├── __init__.py
│   │   └── configuration_service.py
│   │
│   ├── entity_base.py           # Base entity classes (Phase 2)
│   ├── position_utils.py        # Position utilities (Phase 3)
│   ├── geometry.py              # Geometric utilities (Phase 3)
│   ├── enums.py                 # Type-safe enumerations (Phase 1)
│   ├── const.py                 # Constants (Phase 1)
│   │
│   ├── sensor.py                # Sensor platform
│   ├── switch.py                # Switch platform
│   ├── binary_sensor.py         # Binary sensor platform
│   ├── button.py                # Button platform
│   │
│   ├── sun.py                   # Solar calculations
│   ├── helpers.py               # Utility functions
│   └── manifest.json            # Integration metadata
│
├── tests/                       # Unit tests (239 tests)
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   ├── DEVELOPMENT.md           # Developer documentation
│   └── UNIT_TESTS.md            # Testing documentation
├── release_notes/               # Historical release notes
└── scripts/                     # Development scripts
```

## Version History

- **v2.7.0+**: Enhanced geometric accuracy, window depth support
- **v2.6.x**: Climate mode, manual override detection
- **v2.0.0**: Initial release with vertical/horizontal/tilt support

---

For more information, see:
- [DEVELOPMENT.md](DEVELOPMENT.md) - Developer guide
- [UNIT_TESTS.md](UNIT_TESTS.md) - Testing documentation
- [README.md](../README.md) - User documentation
