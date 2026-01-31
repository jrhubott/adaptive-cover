# P1 Diagnostic Sensors Testing Guide

## Summary

This document provides a testing guide for the Priority 1 (P1) diagnostic sensors added in v2.5.0-beta.4.

## What Was Implemented

### P0 Sensors (Already in v2.5.0-beta.3)
These are **enabled by default** when diagnostics is enabled:
- Sun Azimuth (°)
- Sun Elevation (°)
- Gamma (°)
- Control Status (enum)
- Calculated Position (%)

### P1 Sensors (New in v2.5.0-beta.4)
These are **disabled by default** when diagnostics is enabled (users must enable individually):
- Active Temperature (°C/°F) - *Only created if climate mode enabled*
- Climate Conditions (enum) - *Only created if climate mode enabled*
- Time Window Status (enum)
- Sun Validity Status (enum)

## Testing Steps

### Phase 1: Verify P1 Sensor Creation

1. **Enable Diagnostics:**
   - Go to integration configuration
   - Enable "Enable Diagnostic Sensors" toggle
   - Reload integration

2. **Verify P0 Sensors (Enabled by Default):**
   - Go to device entity list
   - Confirm 5 P0 sensors are visible and **enabled**:
     - Sun Azimuth
     - Sun Elevation
     - Gamma
     - Control Status
     - Calculated Position

3. **Verify P1 Sensors (Disabled by Default):**
   - Go to device entity list
   - Show disabled entities
   - Confirm P1 sensors are created but **disabled**:
     - Time Window Status (always created)
     - Sun Validity Status (always created)
     - Active Temperature (only if climate mode enabled)
     - Climate Conditions (only if climate mode enabled)

### Phase 2: Test Active Temperature Sensor (Climate Mode Required)

1. Enable "Active Temperature" sensor manually
2. Verify it shows current temperature value
3. Check attributes show:
   - `inside_temperature`: Value from temp_entity
   - `outside_temperature`: Value from outside_entity or weather
   - `temp_switch`: true/false
4. Verify unit matches Home Assistant configuration (°C or °F)
5. Test temperature updates in real-time
6. Test switching between inside/outside temperature (if configured)

### Phase 3: Test Climate Conditions Sensor (Climate Mode Required)

1. Enable "Climate Conditions" sensor manually
2. Verify state shows: "Summer Mode", "Winter Mode", or "Intermediate"
3. Check attributes show:
   - `is_summer`: true/false
   - `is_winter`: true/false
   - `is_presence`: true/false
   - `is_sunny`: true/false
   - `lux_active`: true/false/null (if lux entity configured)
   - `irradiance_active`: true/false/null (if irradiance entity configured)
4. Trigger summer conditions (high temp) and verify state changes to "Summer Mode"
5. Trigger winter conditions (low temp) and verify state changes to "Winter Mode"
6. Check intermediate state when temp is between thresholds

### Phase 4: Test Time Window Status Sensor

1. Enable "Time Window Status" sensor manually
2. Verify state shows "Active" or "Outside Window"
3. Check attributes show:
   - `check_adaptive_time`: true/false
   - `after_start_time`: true/false
   - `before_end_time`: true/false
   - `start_time`: configured start time or null
   - `end_time`: configured end time or null
4. If time window is configured:
   - Change time to be outside window and verify state updates to "Outside Window"
   - Change time to be inside window and verify state updates to "Active"

### Phase 5: Test Sun Validity Status Sensor

1. Enable "Sun Validity Status" sensor manually
2. Verify state shows one of:
   - "Valid" - Sun is in FOV and within elevation range
   - "In Blind Spot" - Sun is in configured blind spot
   - "Invalid Elevation" - Sun elevation is outside range
   - "Invalid" - Sun is not in FOV
3. Check attributes show:
   - `valid`: true/false
   - `valid_elevation`: true/false
   - `in_blind_spot`: true/false (if blind spot configured)
4. Wait for sun to move and verify state changes appropriately

### Phase 6: Integration Testing

1. **Climate Mode Disabled:**
   - Disable climate mode in config
   - Reload integration
   - Verify temperature and climate condition sensors are NOT created
   - Verify time window and sun validity sensors ARE still created (but disabled)

2. **Diagnostics Disabled:**
   - Disable diagnostics toggle
   - Reload integration
   - Verify ALL diagnostic sensors (P0 and P1) are removed

3. **Entity Registry Persistence:**
   - Enable a P1 sensor
   - Reload integration
   - Verify sensor stays enabled after reload
   - Disable the P1 sensor
   - Verify sensor stays disabled after reload

4. **Dashboard Integration:**
   - Add enabled P1 sensors to dashboard
   - Verify real-time updates work
   - Check history graphs display correctly
   - Test sensors work in automations

## Expected Behavior

### Disabled by Default
- P1 sensors appear in entity list but are disabled
- They don't consume resources or appear in dashboards until manually enabled
- This reduces overhead for users who only need P0 sensors

### Climate Mode Conditional
- Active Temperature and Climate Conditions sensors only exist if climate mode is enabled
- If you don't use climate mode, these sensors won't be created at all

### Temperature Unit Handling
- Active Temperature sensor uses `SensorDeviceClass.TEMPERATURE`
- Home Assistant automatically handles unit display based on user preferences
- Temperature values come directly from climate_data without conversion

### Human-Readable States
- Time Window: Shows "Active" or "Outside Window" instead of raw boolean
- Sun Validity: Shows descriptive text like "In Blind Spot" instead of validation details
- Climate Conditions: Shows "Summer Mode", "Winter Mode", or "Intermediate"

### Diagnostic Entity Category
- All sensors (P0 and P1) use `EntityCategory.DIAGNOSTIC`
- They appear in the diagnostic section of the device page
- They don't clutter the main entity list

## Last Cover Action Sensor (P0)

**Purpose:** Shows the most recent cover action performed by the integration. This is a P0 sensor, enabled by default when diagnostics are enabled.

### Setup
1. Enable diagnostics in automation settings (sensor will be automatically enabled)
2. Enable automatic control
3. Trigger position changes (wait for sun to move or use Developer Tools to change sun sensor)

### Expected Behavior

**Position-Capable Covers:**
- Sensor state: `"set_cover_position → [entity] at 14:30:45"`
- Attributes show exact position sent

**Open/Close-Only Covers:**
- Sensor state: `"open_cover → [entity] at 14:30:45"` or `"close_cover → ..."`
- Attributes show threshold comparison details
- Example: `calculated_position: 30`, `threshold_used: 50`, `threshold_comparison: "30 >= 50"`

**After Integration Reload:**
- Sensor shows: `"No action recorded"`
- Updates after first action

### Testing Checklist
- [ ] Sensor enabled by default when diagnostics enabled (P0 diagnostic)
- [ ] Shows correct service name (open_cover, close_cover, set_cover_position, set_cover_tilt_position)
- [ ] Timestamp updates on each action
- [ ] Attributes include all relevant data
- [ ] Works with multiple covers (tracks last action)
- [ ] Works with inverse_state enabled/disabled
- [ ] Handles integration reload gracefully

## Common Issues

### Sensors Not Created
- **Check diagnostics is enabled** in automation settings
- **Check climate mode is enabled** (for temperature/climate sensors)
- **Reload integration** after enabling diagnostics

### Temperature Shows "Unknown"
- **Check temperature entities** are configured and working
- **Verify climate mode is enabled** and working
- **Check attributes** for more details (inside_temperature, outside_temperature)

### Climate Conditions Shows Wrong Mode
- **Check temperature thresholds** in climate settings
- **Verify temperature values** are being read correctly
- **Check weather entity** if configured (for is_sunny)
- **Review attributes** to see individual condition flags

### Time Window Not Updating
- **Check time window is configured** (start/end time)
- **Verify current time** is within expected range
- **Check attributes** for detailed time information

### Sun Validity Always Invalid
- **Verify sun is in FOV** (check azimuth and FOV settings)
- **Check elevation constraints** (min/max elevation)
- **Review blind spot configuration** if applicable

## Verification Checklist

- [ ] P0 sensors are enabled by default when diagnostics enabled
- [ ] P1 sensors are disabled by default when diagnostics enabled
- [ ] Last cover action sensor is P0 (enabled by default when diagnostics enabled)
- [ ] Temperature sensor only created when climate mode enabled
- [ ] Climate conditions sensor only created when climate mode enabled
- [ ] Time window sensor always created when diagnostics enabled
- [ ] Sun validity sensor always created when diagnostics enabled
- [ ] Temperature sensor shows correct unit (°C or °F)
- [ ] Temperature attributes show inside/outside/switch values
- [ ] Climate conditions state shows Summer/Winter/Intermediate
- [ ] Climate conditions attributes show all condition flags
- [ ] Time window state shows Active/Outside Window
- [ ] Time window attributes show time details
- [ ] Sun validity state shows Valid/In Blind Spot/Invalid
- [ ] Sun validity attributes show validation details
- [ ] Last cover action sensor shows "No action recorded" initially
- [ ] Last cover action sensor updates after first cover action
- [ ] Last cover action attributes show service, position, timestamp
- [ ] Last cover action attributes show threshold details for open/close-only covers
- [ ] Sensors stay enabled/disabled after reload
- [ ] All sensors appear in diagnostic entity category
- [ ] Sensors work in dashboards and automations
- [ ] Linting passes without errors

## Code Changes Summary

### coordinator.py
- Line 169: Added `self.climate_data = None` instance variable
- Line 779: Store climate_data in `climate_mode_data()`
- Lines 851-870: Expanded `build_diagnostic_data()` to include P1 data

### sensor.py
- Lines 22-26: Added `CONF_CLIMATE_MODE` import
- Lines 498-551: Added `AdaptiveCoverAdvancedDiagnosticSensor` class
- Lines 554-590: Added `AdaptiveCoverAdvancedDiagnosticEnumSensor` class
- Lines 153-220: Added P1 sensor creation in `async_setup_entry()`

### README.md
- Lines 78-91: Added diagnostic sensors feature to Features section
- Lines 484-495: Added diagnostic sensors table to Entities section

## References

- Plan: `/Users/jasonrhubottom/Repositories/adaptive-cover/PLAN.md`
- CLAUDE.md: Lines documenting P0/P1 sensor implementation
- Commit: `0fb3ef9` - feat: Add Priority 1 diagnostic sensors
