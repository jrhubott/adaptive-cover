# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For comprehensive developer documentation, see [DEVELOPMENT.md](DEVELOPMENT.md)** - This file contains instructions for Claude Code specifically, while DEVELOPMENT.md is the human-readable developer guide.

## Project Overview

**Adaptive Cover Pro** is a Home Assistant custom integration that automatically controls vertical blinds, horizontal awnings, and tilted/venetian blinds based on the sun's position. It calculates optimal positions to filter direct sunlight while maximizing natural light and supporting climate-aware operation.

**Language:** Python 3.11+
**Framework:** Home Assistant Core (async architecture)
**Version:** 2.5.0-beta.7 (requires Home Assistant 2024.5.0+)

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

## ⚠️ CRITICAL: Git Workflow Requirements

**BEFORE MAKING ANY CODE CHANGES, YOU MUST:**

### Step 1: Check Current Branch
```bash
git branch --show-current
```

### Step 2: Create a Feature Branch (REQUIRED)

**If you're on `main`:**
```bash
# STOP! Do NOT work on main directly
# Create a feature branch first:
git checkout -b feature/descriptive-name

# Examples:
git checkout -b feature/config-flow-ui-improvements
git checkout -b feature/add-shade-control
git checkout -b fix/climate-mode-bug
```

**NEVER:**
- ❌ Make commits directly to `main` branch
- ❌ Start coding before creating a feature branch
- ❌ Skip feature branches "because it's a small change"

**ALWAYS:**
- ✅ Create a feature branch FIRST (before any edits)
- ✅ Use descriptive branch names (feature/*, fix/*, docs/*)
- ✅ Keep commits atomic and focused
- ✅ Test changes on the feature branch

### Step 3: Work on Feature Branch
```bash
# Make your changes
# Commit regularly
git add <files>
git commit -m "descriptive message"
```

### Step 4: Release Strategy by Branch

**Feature Branch (feature/*, fix/*):**
- Create BETA releases: `./scripts/release beta --notes /tmp/release_notes.md --yes`
- Mark as prerelease for testing
- Beta version format: `v2.7.0-beta.1`

**Main Branch:**
- Create STABLE releases: `./scripts/release patch` (or minor/major)
- Only merge to main after beta testing is successful
- Stable version format: `v2.7.0`

### Why This Matters

**Working on main directly causes:**
- ❌ Accidental stable releases of untested code
- ❌ Difficult to roll back changes
- ❌ Can't test changes in isolation
- ❌ Breaks the beta testing workflow
- ❌ Confusion about release status

**Using feature branches enables:**
- ✅ Safe beta testing before merging to main
- ✅ Easy rollback if issues found
- ✅ Clear separation of stable vs. testing code
- ✅ Proper release workflow (beta → main → stable)
- ✅ Multiple features can be developed in parallel

### Example Workflow

```bash
# 1. Start with main branch
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Make changes and commit
git add <files>
git commit -m "feat: Add new feature"

# 4. Push feature branch
git push -u origin feature/my-new-feature

# 5. Create beta release from feature branch
./scripts/release beta --notes /tmp/release_notes.md --yes

# 6. Test beta release thoroughly

# 7. After successful testing, merge to main
git checkout main
git merge feature/my-new-feature
git push origin main

# 8. Create stable release from main
./scripts/release patch --notes /tmp/release_notes.md --yes

# 9. Clean up feature branch
git branch -d feature/my-new-feature
git push origin --delete feature/my-new-feature
```

### Release
```bash
./scripts/release              # Create a release (interactive)
./scripts/release beta         # Create beta release (auto-increment)
./scripts/release patch        # Create patch release (X.Y.Z+1)
./scripts/release --help       # See all options
```

The release script automates the entire release process:
- Updates version in manifest.json
- Creates git commit and annotated tag
- Pushes to GitHub and triggers automated workflow
- Edits GitHub release with proper notes
- Verifies ZIP asset creation
- Supports both beta and production releases

## Testing

**For comprehensive testing documentation, see [UNIT_TESTS.md](UNIT_TESTS.md)**

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_calculation.py -v

# Run with coverage
pytest tests/ --cov=custom_components/adaptive_cover_pro --cov-report=term

# Run in virtual environment
source venv/bin/activate && pytest tests/ -v
```

### Test Coverage

Current test coverage status:

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| calculation.py | 91% | 129 | ✅ Comprehensive |
| helpers.py | 100% | 29 | ✅ Complete |
| inverse_state behavior | 100% | 14 | ✅ Complete |
| **Total** | **30%** | **172** | 🔄 In progress |

**Test Organization:**
- `tests/test_calculation.py` - Position calculation logic (129 tests)
  - Phase 1: AdaptiveGeneralCover properties (40 tests)
  - Phase 2: Cover type classes - Vertical, Horizontal, Tilt (50 tests)
  - Phase 3: NormalCoverState logic (20 tests)
  - Phase 4: ClimateCoverData properties (40 tests)
  - Phase 5: ClimateCoverState logic (50 tests)
- `tests/test_helpers.py` - Helper utility functions (29 tests)
- `tests/test_inverse_state.py` - Inverse state behavior (14 tests)
- `tests/conftest.py` - Shared fixtures and configuration

**Key Testing Features:**
- Comprehensive fixtures for cover instances
- Datetime mocking for time-dependent tests
- Entity state mocking for Home Assistant integration
- Edge case handling (NaN, ValueError, boundary conditions)
- 100% coverage of critical business logic

See [UNIT_TESTS.md](UNIT_TESTS.md) for:
- Detailed test descriptions
- Fixture documentation
- Testing patterns and best practices
- Coverage goals and future expansion plans

### When to Add Tests

**CRITICAL: Always add or update tests when making code changes.**

**Add new tests when:**
- Adding new features or functionality
- Adding new classes, methods, or functions
- Adding new cover types or operation modes
- Implementing new calculation logic
- Adding climate mode features
- Modifying entity handling

**Update existing tests when:**
- Changing calculation algorithms or formulas
- Modifying state determination logic
- Changing default behaviors
- Updating method signatures
- Fixing bugs (add regression test)

**Testing checklist:**
1. ✅ Write tests for new code before committing
2. ✅ Ensure all tests pass locally: `pytest tests/ -v`
3. ✅ Check coverage: `pytest tests/ --cov --cov-report=term`
4. ✅ Aim for 90%+ coverage for calculation logic
5. ✅ Update UNIT_TESTS.md if adding new test categories
6. ✅ Follow existing patterns in test_calculation.py

**Example workflow:**
```bash
# 1. Make code changes
# 2. Add/update tests
# 3. Run tests
pytest tests/ -v

# 4. Check coverage
pytest tests/test_calculation.py --cov=custom_components/adaptive_cover_pro/calculation.py --cov-report=term

# 5. Commit code and tests together
git add custom_components/adaptive_cover_pro/calculation.py tests/test_calculation.py
git commit -m "feat: Add new feature with tests"
```

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

#### Diagnostic Sensor Guidelines

**IMPORTANT:** When creating diagnostic sensors, prevent logbook/activity feed clutter by excluding them from Home Assistant's activity tracking.

**Pattern for Diagnostic Sensors:**
```python
class MyDiagnosticSensor(AdaptiveCoverDiagnosticSensor):
    """Diagnostic sensor description."""

    # Set empty unit_of_measurement to exclude from logbook
    _attr_native_unit_of_measurement = ""  # Prevents activity log entries

    # For P0 sensors (basic diagnostics), override parent to enable by default
    _attr_entity_registry_enabled_default = True  # Optional: only for P0 sensors
```

**Why This Matters:**
- Diagnostic sensors update frequently (every calculation cycle, cover action, etc.)
- Without `unit_of_measurement`, Home Assistant includes them in logbook by default
- This creates excessive clutter in the activity/logbook feed
- Setting empty string `""` triggers Home Assistant's logbook exclusion
- History is still recorded for debugging purposes

**When to Apply:**
- ✅ All diagnostic sensors that show operational data (last action, status, etc.)
- ✅ Sensors that update frequently (multiple times per hour)
- ✅ Sensors showing technical/debugging information
- ❌ User-facing sensors that represent meaningful state changes (control method, position)

**Examples:**
- `AdaptiveCoverLastActionSensor` - Shows last cover action (updates every action)
- Future diagnostic sensors - Active temperature, climate conditions, time windows

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

## Inverse State Behavior

### CRITICAL: Do Not Change This Behavior

The `inverse_state` feature is designed to handle covers that don't follow Home Assistant guidelines (where 0=closed, 100=open). When enabled, it inverts the calculated position for both position-capable AND open/close-only covers.

### How Inverse State Works

**For Position-Capable Covers:**
- Calculated position is inverted: `state = 100 - state`
- Inverted position is sent to the cover entity
- Example: Calculate 30% → invert to 70% → send position 70 to cover

**For Open/Close-Only Covers:**
- Calculated position is inverted: `state = 100 - state`
- Inverted position is compared to threshold
- Example: Calculate 30% → invert to 70% → 70% ≥ 50% → send OPEN command

### Code Flow (coordinator.py)

1. **Line 822-824**: Inverse state is applied if enabled and interpolation is NOT used
   ```python
   if self._inverse_state and not self._use_interpolation:
       state = inverse_state(state)
   ```

2. **Line 497-502**: For open/close-only covers, threshold is applied to the (potentially inverted) state
   ```python
   if state >= self._open_close_threshold:
       service = "open_cover"
   else:
       service = "close_cover"
   ```

### Why This Order Is Correct

The inversion happens BEFORE the threshold check for open/close-only covers. This is intentional because:
- It allows `inverse_state` to work consistently for both cover types
- Covers with inverted semantics need inverted behavior at the command level, not just position level
- The threshold operates on the "inverted world" where the cover's semantics are backwards

### Development Rules

**NEVER:**
- Change the order of inverse_state application and threshold checking
- Skip inverse_state for open/close-only covers when it's enabled
- Apply inverse_state after the threshold check

**ALWAYS:**
- Preserve the current flow: calculate → invert (if enabled) → threshold (for open/close-only)
- Test both position-capable and open/close-only covers when modifying state calculation
- Refer to this section when working on coordinator state calculation logic

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

## Development Workflow Summary

**CRITICAL REQUIREMENTS** (See detailed workflow above):
- ⚠️ **ALWAYS create a git feature branch BEFORE making any changes** (see [Git Workflow Requirements](#️-critical-git-workflow-requirements))
- ⚠️ **NEVER work directly on main branch** - Create feature branches for ALL changes
- Keep commits atomic and focused
- Never refactor code unless explicitly asked
- **ALWAYS add or update tests when adding features or changing logic**
  - New features require new tests covering the functionality
  - Logic changes require updating existing tests to match new behavior
  - Aim for 90%+ coverage for core calculation logic
  - See [UNIT_TESTS.md](UNIT_TESTS.md) for testing patterns and best practices

**Release Workflow:**
- Feature branch → Beta release (`v2.7.0-beta.1`)
- After testing → Merge to main
- Main branch → Stable release (`v2.7.0`)

## Feature Planning

### Features Planned Section

The README.md file contains a "Features Planned" section that tracks upcoming features and enhancements:

**Location:** [README.md - Features Planned](../README.md#features-planned)

**Guidelines:**
1. **Check for New Features**: When asked to add new functionality, consult the Features Planned section first to see if it's already listed
2. **Suggest from the List**: Proactively suggest implementing features from this list when appropriate
3. **Cross Off Completed Features**: When implementing a planned feature, use strikethrough markdown (`~~feature name~~`) to mark it as completed
4. **Add New Features**: If a user requests a feature that should be planned, add it to this section in the README

**Format:**
```markdown
- Feature category
  - ~~Completed feature~~
  - Pending feature
  - Another pending feature
```

**Example Workflow:**
1. User asks to add unit system support
2. Check Features Planned section - it's already listed
3. Implement the feature
4. Update README.md: Change `- Support Home Assistant unit system` to `- ~~Support Home Assistant unit system~~`
5. Mention in commit message and release notes that this was a planned feature

## Release Process

### Creating Releases

When creating releases, follow these guidelines:

1. **Version Numbering**
   - Use semantic versioning: `MAJOR.MINOR.PATCH`
   - Beta releases: `MAJOR.MINOR.PATCH-beta.N`
   - Update version in `custom_components/adaptive_cover_pro/manifest.json`

2. **Git Tags**
   - Create annotated tags: `git tag -a vX.Y.Z -m "Release notes"`
   - Tag format must match `v*.*.*` to trigger the release workflow
   - Beta tags like `v2.3.0-beta.1` are supported

3. **Release Notes**
   - **NEVER** include `Co-Authored-By:` lines in release notes
   - **NEVER** include Claude/AI attributions (e.g., "Generated with Claude Code")
   - **ALWAYS** generate notes in `/tmp/release_notes.md` and use `--notes` parameter
   - **NEVER** use `--editor` parameter (avoids interactive editor)
   - Use clear, user-friendly language with emoji section headers
   - Include: Features, Documentation, Technical Details, Installation, Testing sections
   - For beta releases, mark as prerelease and include testing guidance

4. **Automated Release Workflow**
   - Pushing a tag matching `v*.*.*` triggers `.github/workflows/publish-release.yml`
   - The workflow automatically:
     - Creates a GitHub release
     - ZIPs the `custom_components/adaptive_cover_pro` directory
     - Uploads `adaptive_cover_pro.zip` as a release asset
   - **IMPORTANT**: Always verify that `adaptive_cover_pro.zip` is attached to the release
   - If the ZIP is missing, the workflow may have failed - check GitHub Actions logs

5. **Release Creation Steps**

   **Automated (Recommended):**
   ```bash
   # 1. Generate release notes in tmp directory
   cat > /tmp/release_notes.md << 'EOF'
   ## 🎯 Release Title

   Release description here...

   ### ✨ Features
   - Feature 1
   - Feature 2

   ### 📚 Documentation
   - Doc update 1

   ### 🧪 Testing
   - Tested with Python 3.11 and 3.12
   - Home Assistant 2024.5.0+
   EOF

   # 2. Pass notes file to release script (works for ALL release types)
   ./scripts/release patch --notes /tmp/release_notes.md --yes    # Patch release
   ./scripts/release minor --notes /tmp/release_notes.md --yes    # Minor release
   ./scripts/release major --notes /tmp/release_notes.md --yes    # Major release
   ./scripts/release beta --notes /tmp/release_notes.md --yes     # Beta release

   # For help with all options
   ./scripts/release --help
   ```

   **IMPORTANT:** Always generate notes in `/tmp/release_notes.md` and use `--notes` parameter
   for **ALL release types** (patch, minor, major, beta). Do NOT use `--editor` parameter.

   **Manual (Fallback):**
   ```bash
   # 1. Update version in manifest.json
   # 2. Commit the version bump
   git add custom_components/adaptive_cover_pro/manifest.json
   git commit -m "chore: Bump version to vX.Y.Z"

   # 3. Create and push tag (triggers workflow)
   git tag -a vX.Y.Z -m "Release notes here (NO Co-Authored-By)"
   git push origin vX.Y.Z

   # 4. Wait for workflow to complete (~15 seconds)
   # 5. Edit release to update notes and mark as prerelease if needed
   gh release edit vX.Y.Z --title "Title" --notes "Notes" --prerelease

   # 6. Verify ZIP asset exists
   gh release view vX.Y.Z --json assets
   ```

6. **Determining Release Type by Branch** ⚠️ CRITICAL

   **EXPECTED WORKFLOW (Do this):**
   - **Feature branch** (feature/*, fix/*) → Create a BETA release
     - Example: `git checkout -b feature/my-feature` then `./scripts/release beta`
     - Use beta version numbers: `MAJOR.MINOR.PATCH-beta.N`
     - Mark as prerelease in GitHub
     - Include testing instructions and warnings
     - Test thoroughly before merging to main

   - **Main branch** → Create a STABLE release (after beta testing)
     - Only merge to main AFTER successful beta testing
     - Example: `git checkout main && git merge feature/my-feature` then `./scripts/release patch`
     - Use standard semantic versioning: `MAJOR.MINOR.PATCH`
     - Not marked as prerelease (production-ready)
     - Should follow successful beta testing

   **⚠️ WARNING:** If you find yourself about to create a beta release from main, STOP! You should have created a feature branch first. This is a workflow violation and indicates you worked on main directly (which should never happen).

7. **Beta Release Guidelines**
   - Mark as prerelease: `gh release edit vX.Y.Z-beta.N --prerelease`
   - Include clear testing instructions
   - Warn users this is for testing purposes
   - Request feedback on specific features being tested

## Documentation Guidelines

### README.md Updates

**CRITICAL:** Always update README.md when adding new features or making user-visible changes.

**Required Updates:**
1. **Features Section** (~line 52-91)
   - Add bullet points describing the new feature
   - Include key capabilities and options
   - Mention any configuration requirements

2. **Entities Section** (~line 447-495)
   - Add new entities to the appropriate table
   - Include entity name pattern, default state, and description
   - Mark optional/conditional entities clearly
   - Note any special behavior (disabled by default, climate mode only, etc.)

3. **Variables Section** (if adding config options)
   - Document new configuration variables
   - Include default values and valid ranges
   - Explain what the option controls

4. **Known Limitations** (if applicable)
   - Document any limitations or edge cases
   - Provide workarounds if available

**Example Workflow:**
```bash
# 1. Make code changes
# 2. Update README.md
# 3. Commit both together
git add custom_components/adaptive_cover_pro/ README.md
git commit -m "feat: Add feature X

- Implementation details
- README updated with feature documentation"
```

**Quality Check:**
- Use clear, user-friendly language
- Include examples where helpful
- Keep table formatting consistent
- Verify markdown renders correctly

### DEVELOPMENT.md Updates

**CRITICAL:** Always update DEVELOPMENT.md when making changes that affect the development process or workflow.

**When to Update DEVELOPMENT.md:**

1. **New Development Scripts** (scripts/ directory)
   - Add documentation to "Development Scripts" section
   - Include purpose, usage, options, and examples
   - Document what the script does step-by-step
   - Add troubleshooting tips if applicable

2. **Changes to Release Process**
   - Update "Release Process" section (~line 150-700)
   - Document new release script features or options
   - Update examples if behavior changes
   - Add new troubleshooting scenarios
   - Update workflow diagrams if flow changes

3. **Architecture Changes**
   - Update "Architecture Notes" section
   - Document new patterns or design decisions
   - Update data flow diagrams
   - Add explanations for critical behaviors

4. **New Testing Strategies**
   - Update "Testing" section
   - Document new test environments or tools
   - Add testing examples and best practices

5. **Code Standards Changes**
   - Update "Code Standards" section
   - Document new linting rules or conventions
   - Update import order or style guidelines
   - Add new best practices

6. **Project Structure Changes**
   - Update "Project Structure" section (~line 35-80)
   - Add new directories or major files
   - Update line counts for major files if significantly changed
   - Document purpose of new components

7. **Debugging Tools/Techniques**
   - Update "Debugging" section
   - Add new common issues and solutions
   - Document new debugging tools or approaches

**Required Updates:**
- Keep examples current and working
- Ensure all script documentation matches actual behavior
- Maintain accuracy of line number references (approximate is fine)
- Update workflow diagrams if process changes
- Add troubleshooting for new error scenarios

**Example Workflow:**
```bash
# 1. Make changes to development process (e.g., add new script)
# 2. Update DEVELOPMENT.md with documentation
# 3. Test that instructions work
# 4. Commit both together
git add scripts/new-script DEVELOPMENT.md
git commit -m "feat: Add new development script

- Script implementation
- DEVELOPMENT.md updated with usage documentation"
```

**Quality Check:**
- Test all command examples to ensure they work
- Use consistent formatting with existing documentation
- Include practical examples for complex features
- Add visual diagrams (ASCII art) where helpful
- Cross-reference related sections

**Special Considerations:**
- **Release Script Documentation:** This is the most detailed section in DEVELOPMENT.md (~400 lines). When updating release process, ensure:
  - Examples remain current and accurate
  - Troubleshooting covers new error scenarios
  - Workflow diagram reflects actual execution flow
  - All command-line options are documented
  - CI/CD integration examples work correctly

## Manual Testing & Simulation

**For unit test documentation, see [UNIT_TESTS.md](UNIT_TESTS.md)**

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
│   ├── config_context_adapter.py # Logging adapter
│   ├── diagnostics.py           # Diagnostics export
│   ├── manifest.json            # Integration metadata
│   ├── translations/            # i18n files (13 languages)
│   ├── blueprints/              # Automation blueprints
│   └── simulation/              # Testing and simulation tools
├── scripts/
│   ├── setup                    # Development environment setup
│   ├── develop                  # Start Home Assistant dev server
│   ├── lint                     # Run linting
│   └── release                  # Create releases (automated)
├── tests/                       # Unit tests
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── test_calculation.py      # Calculation logic tests (129 tests, 91% coverage)
│   ├── test_helpers.py          # Helper function tests (29 tests, 100% coverage)
│   └── test_inverse_state.py    # Inverse state tests (14 tests, 100% coverage)
├── config/                      # Test Home Assistant config
├── notebooks/                   # Jupyter notebooks for testing
├── .github/workflows/           # GitHub Actions
│   └── publish-release.yml      # Automated release workflow
├── DEVELOPMENT.md               # Developer documentation (comprehensive)
├── UNIT_TESTS.md                # Unit test documentation (test structure, patterns, coverage)
├── CLAUDE.md                    # Instructions for Claude Code (this file)
├── README.md                    # User documentation
└── pyproject.toml               # Python project configuration
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
