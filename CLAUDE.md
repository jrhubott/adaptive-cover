# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For comprehensive developer documentation, see [DEVELOPMENT.md](DEVELOPMENT.md)** - This file contains instructions for Claude Code specifically, while DEVELOPMENT.md is the human-readable developer guide.

## Project Overview

**Adaptive Cover Pro** is a Home Assistant custom integration that automatically controls vertical blinds, horizontal awnings, and tilted/venetian blinds based on the sun's position. It calculates optimal positions to filter direct sunlight while maximizing natural light and supporting climate-aware operation.

**Language:** Python 3.11+
**Framework:** Home Assistant Core (async architecture)
**Current Version:** v2.6.8
**Requires:** Home Assistant 2024.5.0+

## Architecture Overview

This integration follows Home Assistant's **Data Coordinator Pattern**:

### Core Components

**`coordinator.py`** - Central hub for all state management
- `AdaptiveDataUpdateCoordinator` manages async updates, entity listeners, and position calculations
- Tracks state changes from sun position, temperature, weather, presence entities
- Handles manual override detection and control
- Orchestrates position calculations and cover service calls

**`calculation.py`** - Position calculation algorithms
- `AdaptiveVerticalCover` - Up/down blind calculations
- `AdaptiveHorizontalCover` - In/out awning calculations
- `AdaptiveTiltCover` - Slat rotation calculations
- `NormalCoverState` - Basic sun position mode
- `ClimateCoverState` - Climate-aware mode with temperature/presence/weather

**`config_flow.py`** - Multi-step UI configuration
- Separate flows for vertical/horizontal/tilt cover types
- Common options, automation settings, climate mode, blind spots
- Option validation and context-aware forms

### Platform Files

- `sensor.py` - Position, control method, start/end sun times
- `switch.py` - Automatic control, climate mode, manual override detection
- `binary_sensor.py` - Sun visibility, manual override status
- `button.py` - Manual override reset

### Data Flow

1. **Initialization:** Config flow creates `ConfigEntry` → coordinator setup
2. **Listeners:** Coordinator registers listeners on sun, temperature, weather, presence entities
3. **State Change:** Entity change triggers `async_check_entity_state_change()`
4. **Calculation:** `_async_update_data()` calls appropriate cover class to calculate position
5. **Update:** Coordinator updates data → platform entities refresh
6. **Control:** If enabled and not manually overridden → calls cover service to move blinds

## Development Environment

### Setup

```bash
./scripts/setup              # Install dev dependencies and setup pre-commit hooks
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

### Linting

```bash
./scripts/lint               # Run ruff linting with auto-fix
ruff check . --fix           # Direct ruff invocation
ruff format .                # Format code
```

Pre-commit hooks run automatically on commit:
- Ruff linting and formatting
- Prettier for YAML/JSON
- Trailing whitespace cleanup

## ⚠️ CRITICAL: Git & GitHub Workflow

### Branch Strategy

**BEFORE MAKING ANY CODE CHANGES:**

1. **Check current branch:** `git branch --show-current`
2. **Create feature branch from main** (REQUIRED)

```bash
# ALWAYS branch from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b <prefix>/<description>
```

**Branch Naming Conventions:**

| Type | Prefix | Example |
|------|--------|---------|
| New feature | `feature/` | `feature/add-shade-control` |
| Bug fix | `fix/` | `fix/climate-mode-bug` |
| Documentation | `docs/` | `docs/update-readme` |
| GitHub issue (bug) | `fix/issue-NNN-` | `fix/issue-123-sensor-unavailable` |
| GitHub issue (feature) | `feature/issue-NNN-` | `feature/issue-67-entity-picture` |

**Rules:**
- ✅ ALWAYS create a feature branch FIRST (before any edits)
- ✅ ALWAYS branch from `main` (never from other feature branches)
- ✅ Keep commits atomic and focused
- ✅ Test changes on the feature branch
- ❌ NEVER commit directly to `main` branch
- ❌ NEVER skip feature branches "because it's a small change"

### Working with GitHub Issues

When the user says "fix issue #123" or references an issue number:

**Step 1: Fetch Issue Details**
```bash
gh issue view 123
```

Read and understand:
- What the problem is
- Steps to reproduce (if bug)
- Expected vs actual behavior
- Labels or priority indicators

**Step 2: Create Appropriately Named Branch**
```bash
# For bugs
git checkout -b fix/issue-123-short-description

# For feature requests
git checkout -b feature/issue-123-short-description
```

**Step 3: Make Changes and Commit with Issue Reference**

Use keywords that auto-close issues when merged to main:
- `Fixes #123` - Closes the issue
- `Closes #123` - Closes the issue
- `Resolves #123` - Closes the issue

Non-closing references:
- `Part of #123` - References without closing
- `Related to #123` - Links to related issue

Example commit:
```bash
git commit -m "fix: Resolve sensor unavailable error

Changed coordinator._entities to coordinator.entities to fix
AttributeError that caused sensor to become unavailable.

Fixes #123"
```

**Step 4: Push and Merge**
```bash
# Push feature branch
git push -u origin fix/issue-123-sensor-unavailable

# Merge to main (after testing)
git checkout main
git merge fix/issue-123-sensor-unavailable
git push origin main

# Issue auto-closes when pushed to main
```

**gh CLI Quick Reference:**

| Task | Command |
|------|---------|
| View issue | `gh issue view 123` |
| List open issues | `gh issue list` |
| List by label | `gh issue list --label bug` |
| Add comment | `gh issue comment 123 --body "Message"` |
| Close manually | `gh issue close 123 --comment "Fixed in v2.6.8"` |
| Create PR | `gh pr create --title "Fix: Description (#123)"` |

### Commit Message Guidelines

**CRITICAL:** Git commits must NOT include Claude attribution:
- ❌ NEVER add `Co-Authored-By: Claude` lines
- ❌ NEVER add `Generated with Claude Code`
- ✅ Commit messages should only describe the changes made

This applies to ALL commits (regular commits, merge commits, etc.) and release notes.

### Release Strategy

**Feature Branch:**
- Create BETA releases: `./scripts/release beta --notes /tmp/release_notes.md --yes`
- Beta version format: `v2.7.0-beta.1`
- Mark as prerelease for testing

**Main Branch:**
- Create STABLE releases: `./scripts/release patch` (or minor/major)
- Only merge to main AFTER successful beta testing
- Stable version format: `v2.7.0`

**⚠️ CRITICAL:** Only create releases when explicitly requested by the user.
- ❌ NEVER create a release proactively
- ✅ ONLY create releases when user explicitly asks

## Testing

**For comprehensive testing documentation, see [UNIT_TESTS.md](UNIT_TESTS.md)**

### Running Tests

**IMPORTANT:** Always activate the virtual environment first:

```bash
# Activate virtual environment (REQUIRED)
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_calculation.py -v

# Run with coverage
python -m pytest tests/ --cov=custom_components/adaptive_cover_pro --cov-report=term

# One-liner (activate + run)
source venv/bin/activate && python -m pytest tests/ -v
```

### Test Coverage Status

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| calculation.py | 91% | 135 | ✅ Comprehensive |
| helpers.py | 100% | 29 | ✅ Complete |
| inverse_state behavior | 100% | 14 | ✅ Complete |
| **Total** | **28%** | **178** | 🔄 In progress |

### When to Add Tests

**CRITICAL: Always add or update tests when making code changes.**

**Add new tests when:**
- Adding new features or functionality
- Adding new classes, methods, or functions
- Implementing new calculation logic
- Adding climate mode features

**Update existing tests when:**
- Changing calculation algorithms
- Modifying state determination logic
- Changing default behaviors
- Fixing bugs (add regression test)

**Testing checklist:**
1. ✅ Write tests for new code before committing
2. ✅ Ensure all tests pass: `source venv/bin/activate && python -m pytest tests/ -v`
3. ✅ Check coverage for modified files
4. ✅ Aim for 90%+ coverage for calculation logic
5. ✅ Follow existing patterns in test files

## Release Process

### Creating Releases

**CRITICAL: Only create releases when explicitly requested by the user.**

### Version Numbering

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Beta releases: `MAJOR.MINOR.PATCH-beta.N`
- Update version in `custom_components/adaptive_cover_pro/manifest.json`

### Release Workflow (Automated)

**1. Generate release notes:**
```bash
cat > /tmp/release_notes.md << 'EOF'
## 🎯 Release Title

Release description here...

### ✨ Features
- Feature 1

### 🐛 Bug Fixes
- Fix 1

### 🧪 Testing
- Tested with Python 3.11 and 3.12
- Home Assistant 2024.5.0+
EOF
```

**2. Create release:**
```bash
# From feature branch (beta)
./scripts/release beta --notes /tmp/release_notes.md --yes

# From main branch (stable)
./scripts/release patch --notes /tmp/release_notes.md --yes  # or minor/major
```

The script automatically:
- Updates version in manifest.json
- Creates git commit and annotated tag
- Pushes to GitHub and triggers workflow
- Edits GitHub release with notes
- Verifies ZIP asset creation

### Release Notes Guidelines

- **NEVER** include `Co-Authored-By:` or Claude attributions
- **ALWAYS** generate notes in `/tmp/release_notes.md` and use `--notes` parameter
- **NEVER** use `--editor` parameter (avoids interactive editor)
- Use clear, user-friendly language with emoji section headers
- Include: Features, Bug Fixes, Documentation, Technical Details, Installation, Testing
- For beta releases, mark as prerelease and include testing guidance

### Determining Release Type by Branch

| Branch Type | Release Type | Example |
|-------------|--------------|---------|
| `feature/*`, `fix/*` | Beta (prerelease) | `v2.7.0-beta.1` |
| `main` | Stable (production) | `v2.7.0` |

**⚠️ WARNING:** If you're creating a beta release from main, STOP! You should have created a feature branch first.

## Documentation Guidelines

### README.md Updates

**CRITICAL:** Always update README.md when adding new features or making user-visible changes.

**Required Updates:**
1. **Features Section** - Add bullet points describing the new feature
2. **Entities Section** - Add new entities to appropriate table
3. **Variables Section** - Document new configuration variables (if applicable)
4. **Known Limitations** - Document limitations or edge cases (if applicable)

### DEVELOPMENT.md Updates

**CRITICAL:** Always update DEVELOPMENT.md when making changes that affect the development process.

**When to Update:**
- New development scripts
- Changes to release process
- Architecture changes
- New testing strategies
- Code standards changes
- Project structure changes
- Debugging tools/techniques

### Features Planned Section (README.md)

Check the "Features Planned" section in README.md when asked to add new functionality:
1. Check if feature is already listed
2. Implement the feature
3. Mark as completed: `~~Completed feature~~`
4. Mention in commit and release notes

## Code Standards & Patterns

### Home Assistant Patterns

- **Async-first** - All I/O is async (state tracking, cover commands)
- **Never block the event loop** - Use async/await
- **Coordinator pattern** - Use for entity updates
- **Entity naming** - `{domain}.{type}_{description}_{name}`
- **Store data** - In `coordinator.data` for entity access
- **Update handler** - Use `_handle_coordinator_update()` in entities

### Diagnostic Sensor Guidelines

When creating diagnostic sensors:

```python
class MyDiagnosticSensor(AdaptiveCoverDiagnosticSensor):
    """Diagnostic sensor description."""

    # For text/status sensors: empty unit excludes from logbook
    _attr_native_unit_of_measurement = ""  # Prevents activity log entries

    # For numeric sensors: MUST have proper unit for statistics
    _attr_native_unit_of_measurement = "retries"  # Enables statistics tracking

    # For P0 sensors (basic diagnostics), enable by default
    _attr_entity_registry_enabled_default = True
```

**Rules:**
- ✅ Text/status sensors → empty unit `""` to exclude from logbook
- ✅ Numeric sensors → proper unit (`"retries"`, `"°"`, `PERCENTAGE`) for statistics
- ✅ History is still recorded for debugging
- ❌ Don't use empty unit for numeric sensors (breaks statistics)

### Inverse State Behavior

**CRITICAL: Do Not Change This Behavior**

The `inverse_state` feature handles covers that don't follow Home Assistant guidelines (0=closed, 100=open):

**For Position-Capable Covers:**
- Calculated position is inverted: `state = 100 - state`
- Inverted position is sent to the cover entity

**For Open/Close-Only Covers:**
- Calculated position is inverted: `state = 100 - state`
- Inverted position is compared to threshold

**Code Flow:**
1. Calculate position
2. Invert (if enabled and interpolation not used)
3. Apply threshold (for open/close-only covers)

**NEVER:**
- Change the order of inverse_state application and threshold checking
- Skip inverse_state for open/close-only covers when enabled
- Apply inverse_state after the threshold check

## Configuration Structure

**`config_entry.data`** (setup phase):
- `name` - Instance name
- `sensor_type` - cover_blind/cover_awning/cover_tilt

**`config_entry.options`** (configurable):
- Window azimuth, field of view, elevation limits
- Cover-specific dimensions (height, length, slat properties)
- Position limits:
  - `min_position` / `max_position` - Absolute position boundaries (0-99%, 1-100%)
  - `enable_min_position` / `enable_max_position` - When limits apply:
    - False (default): Limits always enforced
    - True: Limits only during direct sun tracking
- Automation settings (delta position/time, start/end times, manual override)
- Climate settings (temperature entities/thresholds, presence, weather)
- Light settings (lux/irradiance entities and thresholds)
- Blind spot areas

## Manual Testing

- Use `./scripts/develop` to start test instance
- Test config available in `config/configuration.yaml` with mock entities
- Access Home Assistant UI at http://localhost:8123
- `notebooks/test_env.ipynb` - Algorithm testing and visualization
- `custom_components/adaptive_cover_pro/simulation/` - Simulation tools

## File Organization

```
adaptive-cover/
├── custom_components/adaptive_cover_pro/
│   ├── __init__.py              # Integration entry point
│   ├── coordinator.py           # Data coordinator (primary hub)
│   ├── calculation.py           # Position calculation engine
│   ├── config_flow.py           # Configuration UI
│   ├── sensor.py                # Sensor platform
│   ├── switch.py                # Switch platform
│   ├── binary_sensor.py         # Binary sensor platform
│   ├── button.py                # Button platform
│   ├── sun.py                   # Solar calculations
│   ├── helpers.py               # Utility functions
│   ├── const.py                 # Constants
│   ├── manifest.json            # Integration metadata
│   └── translations/            # i18n files (13 languages)
├── scripts/
│   ├── setup                    # Development environment setup
│   ├── develop                  # Start Home Assistant dev server
│   ├── lint                     # Run linting
│   └── release                  # Create releases (automated)
├── tests/                       # Unit tests (178 tests)
│   ├── conftest.py              # Shared fixtures
│   ├── test_calculation.py      # 129 tests, 91% coverage
│   ├── test_helpers.py          # 29 tests, 100% coverage
│   └── test_inverse_state.py    # 14 tests, 100% coverage
├── DEVELOPMENT.md               # Developer documentation
├── UNIT_TESTS.md                # Unit test documentation
├── CLAUDE.md                    # Claude Code instructions (this file)
├── README.md                    # User documentation
└── pyproject.toml               # Python project configuration
```

## Dependencies

**Production:**
- `homeassistant~=2024.5` - Core framework
- `pandas~=2.2` - Solar data calculations
- `astral` - Sun position/timing

**Development:**
- `ruff~=0.4` - Linting and formatting
- `pre-commit~=3.7` - Git hooks
- `pytest` - Testing framework
- `pvlib~=0.11` - Photovoltaic simulations
- `matplotlib~=3.9` - Plotting for simulations

## Cover Types and Operation Modes

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

## Additional Notes

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

### Ruff Configuration
Configured in `pyproject.toml`:
- `select = ["ALL"]` - Enable all rules by default
- Specific ignores for formatter conflicts
- Home Assistant import conventions (cv, dr, er, ir, vol)
- Force sorting within sections for imports
