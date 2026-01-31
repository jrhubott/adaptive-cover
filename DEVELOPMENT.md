# Development Guide

This guide covers everything you need to know to develop and contribute to the Adaptive Cover Pro integration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Scripts](#development-scripts)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Release Process](#release-process)
- [Code Standards](#code-standards)
- [Debugging](#debugging)
- [Architecture Notes](#architecture-notes)

## Prerequisites

Before you begin development, ensure you have the following installed:

### Required Tools

- **Python 3.11+** - The integration requires Python 3.11 or higher
- **Git** - Version control
- **Home Assistant Core** - For testing the integration
- **pip** - Python package manager

### Recommended Tools

- **GitHub CLI (`gh`)** - Required for automated releases
- **jq** - Required for release script (JSON parsing)
- **Visual Studio Code** or **PyCharm** - Recommended IDEs with Home Assistant support

### Installation (macOS)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 git gh jq

# Verify installations
python3 --version
git --version
gh --version
jq --version
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/jrhubott/adaptive-cover.git
cd adaptive-cover
```

### 2. Run Initial Setup

The setup script installs development dependencies and configures pre-commit hooks:

```bash
./scripts/setup
```

This script will:
- Install Python development dependencies (ruff, pre-commit, etc.)
- Set up pre-commit hooks for automatic linting
- Configure your development environment

### 3. Verify Setup

```bash
# Check linting works
./scripts/lint

# Verify pre-commit hooks are installed
pre-commit run --all-files
```

## Project Structure

```
adaptive-cover/
├── custom_components/adaptive_cover_pro/
│   ├── __init__.py              # Integration entry point
│   ├── coordinator.py           # Data coordinator (939 lines)
│   ├── calculation.py           # Position calculations (596 lines)
│   ├── config_flow.py           # Configuration UI (896 lines)
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
├── config/                      # Test Home Assistant config
│   └── configuration.yaml       # Mock entities for testing
├── notebooks/                   # Jupyter notebooks for testing
│   └── test_env.ipynb          # Algorithm testing/visualization
├── .github/workflows/           # GitHub Actions
│   └── publish-release.yml      # Automated release workflow
├── DEVELOPMENT.md              # This file
├── CLAUDE.md                   # Instructions for Claude Code
├── README.md                   # User documentation
└── pyproject.toml              # Python project configuration

```

## Development Scripts

All development scripts are located in the `scripts/` directory and follow a consistent pattern.

### Setup Script

**Purpose:** Initial development environment setup

```bash
./scripts/setup
```

**What it does:**
- Installs Python development dependencies
- Sets up pre-commit hooks
- Validates environment

**When to use:**
- First time setting up the project
- After pulling major changes that update dependencies
- When pre-commit hooks need to be reinstalled

### Development Server

**Purpose:** Run Home Assistant with the integration loaded for testing

```bash
./scripts/develop
```

**What it does:**
- Creates `config/` directory if not present
- Sets `PYTHONPATH` to include `custom_components/`
- Starts Home Assistant with debug logging
- Uses `config/configuration.yaml` for test setup with mock entities

**Features:**
- Hot reload: Changes to Python files are reflected after restart
- Debug logging: Verbose output for troubleshooting
- Mock entities: Pre-configured test entities in `config/configuration.yaml`

**Access:**
- Web UI: http://localhost:8123
- Default credentials: Created on first run

**Tips:**
- Keep the terminal open to see logs in real-time
- Press `Ctrl+C` to stop the server
- Changes require a Home Assistant restart to take effect

### Linting Script

**Purpose:** Run code quality checks and auto-fix issues

```bash
./scripts/lint
```

**What it does:**
- Runs `ruff check . --fix` - Linting with auto-fix
- Runs `ruff format .` - Code formatting

**When to use:**
- Before committing changes
- After writing new code
- When fixing linting errors

**Note:** Pre-commit hooks run this automatically on `git commit`

### Release Script

**Purpose:** Automate the entire release process

See [Release Process](#release-process) section for detailed documentation.

## Development Workflow

### Branch Strategy

We use a feature-branch workflow:

```
main (production releases)
  ├── feature/new-feature
  ├── feature/bug-fix
  └── feature/enhancement
```

**Rules:**
- `main` branch contains stable, production-ready code
- Create feature branches for all changes
- Beta releases are created from feature branches
- Production releases are created from `main` branch only

### Creating a Feature Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-new-feature

# Make changes, commit, push
git add .
git commit -m "feat: Add new feature"
git push origin feature/my-new-feature
```

### Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only changes
- `style:` - Code style changes (formatting, missing semicolons, etc.)
- `refactor:` - Code refactoring without changing functionality
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks (dependencies, tooling, etc.)

**Examples:**

```bash
# Feature
git commit -m "feat: Add lux threshold configuration option"

# Bug fix
git commit -m "fix: Correct manual override detection for open/close-only covers"

# Documentation
git commit -m "docs: Update README with new diagnostic sensors"

# Chore
git commit -m "chore: Bump version to v2.5.0-beta.7"
```

### Pre-commit Hooks

Pre-commit hooks run automatically when you commit:

- **Ruff linting** - Code quality checks
- **Ruff formatting** - Code formatting
- **Prettier** - YAML/JSON formatting
- **Trailing whitespace** - Remove trailing whitespace
- **End-of-file fixer** - Ensure files end with newline

If a hook fails:
1. Review the changes made by auto-fix
2. Stage the fixed files: `git add .`
3. Commit again: `git commit -m "your message"`

To skip hooks (not recommended):
```bash
git commit --no-verify -m "your message"
```

## Testing

### Manual Testing with Development Server

The recommended way to test changes is using the development server:

```bash
# Start the development server
./scripts/develop

# In another terminal, make changes to the code
# Then restart Home Assistant from the UI or by restarting the script
```

**Test Configuration:**

The `config/configuration.yaml` file contains mock entities for testing:
- Mock covers (position-capable and open/close-only)
- Mock temperature sensors
- Mock weather entity
- Mock presence sensors

Edit this file to create the test scenarios you need.

### Automated Tests

This integration uses pytest for automated testing.

**For comprehensive test documentation, see [UNIT_TESTS.md](UNIT_TESTS.md)** which includes:
- Detailed test descriptions for all 172 tests
- Fixture documentation with usage examples
- Testing patterns and best practices
- Coverage goals and future expansion plans

#### Running Tests Locally

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov --cov-report=term-missing

# Run specific test file
pytest tests/test_calculation.py

# Run specific test
pytest tests/test_calculation.py::test_gamma_angle_calculation_sun_directly_in_front

# Run only unit tests (fast)
pytest -m unit

# Run with verbose output
pytest -v

# Use the test script
./scripts/test              # Run all tests
./scripts/test unit         # Run only unit tests
./scripts/test coverage     # Run with detailed coverage
```

#### Test Structure

- `tests/conftest.py` - Shared fixtures (hass mock, logger, configs, cover instances)
- `tests/test_calculation.py` - Position calculation tests (129 tests, unit)
  - Phase 1: AdaptiveGeneralCover properties (40 tests)
  - Phase 2: Cover type classes (50 tests)
  - Phase 3: NormalCoverState logic (20 tests)
  - Phase 4: ClimateCoverData properties (40 tests)
  - Phase 5: ClimateCoverState logic (50 tests)
- `tests/test_helpers.py` - Helper function tests (29 tests, unit)
- `tests/test_inverse_state.py` - Critical inverse state tests (14 tests, unit)

**Total: 172 tests** (all passing)

#### Test Coverage

Current test coverage status:

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| **calculation.py** | 91% | 129 | ✅ Comprehensive |
| **helpers.py** | 100% | 29 | ✅ Complete |
| **const.py** | 100% | - | ✅ Complete |
| **inverse_state** | 100% | 14 | ✅ Complete |
| **coordinator.py** | 22% | - | 🔄 Future work |
| **Overall** | 30% | 172 | 🔄 In progress |

See [UNIT_TESTS.md](UNIT_TESTS.md) for detailed coverage information and future expansion plans.

#### Writing Tests

Tests use pytest fixtures from `conftest.py`. Example:

```python
import pytest
from custom_components.adaptive_cover_pro.helpers import get_safe_state

@pytest.mark.unit
def test_get_safe_state_returns_state(hass):
    """Test get_safe_state returns state when available."""
    state_obj = MagicMock()
    state_obj.state = "25.5"
    hass.states.get.return_value = state_obj

    result = get_safe_state(hass, "sensor.temperature")

    assert result == "25.5"
```

**Best Practices:**
- Use descriptive test names that explain what is being tested
- Add docstrings explaining the test purpose
- Mark tests with `@pytest.mark.unit` for fast tests
- Use fixtures from `conftest.py` for common setup
- Keep tests simple and focused on one behavior

#### Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Pushes to feature branches
- Manual workflow dispatch

See `.github/workflows/tests.yml` for CI configuration.

**CI Matrix:**
- Python 3.11
- Python 3.12

**CI Steps:**
1. Checkout code
2. Set up Python environment
3. Install dependencies
4. Run tests with coverage
5. Upload coverage to Codecov (Python 3.12 only)

#### Test Philosophy

**Priority Order:**
1. **Pure functions** - Test utilities and helpers first (easiest)
2. **Critical behaviors** - Test inverse_state and documented behaviors
3. **Core algorithms** - Test calculation logic
4. **Integration** - Test coordinator and flows (future)

**What We Test:**
- Pure utility functions (no I/O)
- Position calculation algorithms
- Sun angle and azimuth calculations
- Blind spot detection logic
- Position clamping and validation
- Critical documented behaviors (inverse state order of operations)

**What We Don't Test (Yet):**
- Async coordinator logic (complex, lower priority initially)
- Config flow UI (requires Home Assistant test framework)
- Entity registration (lower ROI, can be added later)

### Testing the Release Script

The release script supports dry-run mode for safe testing:

```bash
# Test beta release (no changes made)
./scripts/release beta --dry-run

# Test with explicit version
./scripts/release 2.5.1-beta.1 --dry-run

# Test production release (requires main branch)
git checkout main
./scripts/release patch --dry-run
```

### Jupyter Notebooks

For algorithm testing and visualization:

```bash
# Install Jupyter dependencies
pip install jupyter matplotlib pvlib

# Start Jupyter
jupyter notebook

# Open notebooks/test_env.ipynb
```

**Use cases:**
- Test position calculation algorithms
- Visualize cover positions over time
- Simulate different sun positions and configurations
- Generate plots for documentation

### Simulation Tools

The `custom_components/adaptive_cover_pro/simulation/` directory contains tools for simulating cover behavior over time.

## Release Process

The release process is fully automated with the `./scripts/release` tool.

### Quick Start

```bash
# Create beta release (interactive, opens editor for notes)
./scripts/release beta --editor

# Create production release from main
git checkout main
./scripts/release patch --editor
```

### Release Script Overview

The release script automates:
1. ✅ Version management in `manifest.json`
2. ✅ Git commit and annotated tag creation
3. ✅ Pushing to GitHub (triggers automated workflow)
4. ✅ Editing GitHub release with notes and prerelease flag
5. ✅ Verifying ZIP asset creation

### Command Syntax

```bash
./scripts/release [VERSION_SPEC] [OPTIONS]
```

**VERSION_SPEC:**
- `patch` - Increment patch version (X.Y.Z+1)
- `minor` - Increment minor version (X.Y+1.0)
- `major` - Increment major version (X+1.0.0)
- `beta` - Auto-increment beta version
- `X.Y.Z` - Explicit version number
- `X.Y.Z-beta.N` - Explicit beta version
- *(omit for interactive mode)*

**OPTIONS:**
- `--dry-run` - Preview operations without executing
- `--yes, -y` - Skip confirmation prompts
- `--editor, -e` - Open editor for release notes
- `--notes FILE` - Read release notes from file
- `--auto-notes` - Use auto-generated notes only
- `--force-branch` - Skip branch validation
- `--help, -h` - Show help text

### Release Types

#### Beta Releases

**When to use:** Testing new features on feature branches

**Characteristics:**
- Created from feature branches
- Version format: `X.Y.Z-beta.N`
- Marked as "prerelease" on GitHub
- Includes testing instructions
- Not recommended for production use

**Example workflow:**

```bash
# On feature branch
git checkout feature/new-feature

# Create beta release (auto-increment)
./scripts/release beta --editor

# Or with explicit version
./scripts/release 2.5.1-beta.1 --editor
```

**Release notes template:**
```markdown
# Beta Release vX.Y.Z-beta.N

**⚠️ BETA RELEASE** - This is a beta version for testing purposes.

## Changes
- Feature: [description]
- Bug fix: [description]

## Testing Instructions
1. Install vX.Y.Z-beta.N
2. Test: [specific test cases]
3. Report issues at: https://github.com/jrhubott/adaptive-cover/issues

## Installation
Download `adaptive_cover_pro.zip` from assets below.
```

#### Production Releases

**When to use:** Stable releases from main branch

**Characteristics:**
- Created from `main` branch only
- Version format: `X.Y.Z`
- Not marked as prerelease
- Production-ready
- Full release notes

**Example workflow:**

```bash
# Merge feature branch to main
git checkout main
git merge feature/new-feature
git push origin main

# Create production release
./scripts/release patch --editor
# or
./scripts/release 2.5.0 --editor
```

**Release notes template:**
```markdown
# Adaptive Cover Pro vX.Y.Z

## What's New
- [Feature highlights]

## Bug Fixes
- [Bug fixes]

## Breaking Changes
None

## Installation
### HACS: Update through HACS
### Manual: Download adaptive_cover_pro.zip
```

### Release Script Workflow

Here's what happens when you run the release script:

```
1. Validate Environment
   ├─ Check required tools (git, gh, jq)
   ├─ Verify gh authentication
   ├─ Ensure working directory is clean
   └─ Validate manifest.json exists

2. Calculate Version
   ├─ Read current version from manifest.json
   ├─ Calculate new version based on VERSION_SPEC
   └─ Validate version format

3. Validate Branch
   ├─ Check current branch
   ├─ Ensure branch matches release type
   │  ├─ Beta: Any branch (usually feature/*)
   │  └─ Production: main branch only
   └─ Skip with --force-branch if needed

4. Get Release Notes
   ├─ Option 1: Open editor (--editor)
   ├─ Option 2: Read from file (--notes FILE)
   └─ Option 3: Auto-generate (--auto-notes)

5. Update Version
   └─ Update manifest.json with jq (preserves formatting)

6. Create Git Commit
   ├─ Stage manifest.json
   └─ Commit: "chore: Bump version to vX.Y.Z"

7. Create Annotated Tag
   ├─ Tag name: vX.Y.Z
   └─ Tag message: Release notes (Co-Authored-By filtered)

8. Push to GitHub
   ├─ Push commit to current branch
   └─ Push tag (triggers GitHub Actions workflow)

9. Wait for Workflow
   ├─ Poll GitHub every 5s
   ├─ Timeout: 60s
   └─ Workflow creates initial release + ZIP asset

10. Edit Release
    ├─ Set title: "Adaptive Cover Pro ⛅ vX.Y.Z"
    ├─ Set detailed notes
    └─ Add --prerelease flag for beta releases

11. Verify ZIP Asset
    ├─ Check adaptive_cover_pro.zip exists
    ├─ Verify size is reasonable (100KB-500KB)
    └─ Display success message with release URL
```

### Examples

#### Example 1: Beta Release (Interactive)

```bash
# On feature branch with new feature
git checkout feature/diagnostic-sensors

# Run release script in interactive mode
./scripts/release

# Select "1) Beta"
# Opens editor with template
# Edit release notes, save, and close
# Confirms and creates release
```

#### Example 2: Beta Release (Quick)

```bash
# Auto-increment beta, use auto-generated notes
./scripts/release beta --yes --auto-notes
```

#### Example 3: Production Release

```bash
# Ensure on main branch
git checkout main

# Create patch release with editor
./scripts/release patch --editor

# Edit release notes with full changelog
# Confirms and creates production release
```

#### Example 4: Explicit Version

```bash
# Create specific version
./scripts/release 2.6.0-beta.1 --editor
```

#### Example 5: Release Notes from File

```bash
# Prepare release notes
cat > /tmp/release-notes.md << 'EOF'
# Adaptive Cover Pro v2.5.0

## What's New
- New diagnostic sensors for troubleshooting
- Improved manual override detection
- Support for open/close-only covers

## Bug Fixes
- Fixed inverse state behavior for open/close-only covers
- Corrected unit display for Last Cover Action sensor
EOF

# Create release with notes from file
./scripts/release 2.5.0 --notes /tmp/release-notes.md --yes
```

#### Example 6: Dry Run (Safe Testing)

```bash
# Preview what would happen without making changes
./scripts/release beta --dry-run

# Output shows all operations that would be performed
# No actual changes to git or GitHub
```

### Release Checklist

Before creating a release:

- [ ] All changes committed and pushed to feature branch
- [ ] Pre-commit hooks passing
- [ ] Code linted: `./scripts/lint`
- [ ] Manual testing completed with `./scripts/develop`
- [ ] README.md updated with new features/entities
- [ ] CLAUDE.md updated if development process changed
- [ ] Working directory clean: `git status`

For beta releases:
- [ ] On feature branch
- [ ] Version will be X.Y.Z-beta.N

For production releases:
- [ ] On main branch
- [ ] Beta testing completed successfully
- [ ] Version will be X.Y.Z (no beta suffix)

### Troubleshooting Releases

#### Problem: Working directory not clean

```
✗ Working directory is not clean
ℹ Commit or stash changes before creating a release
```

**Solution:** Commit or stash your changes:
```bash
git add .
git commit -m "your message"
# or
git stash
```

#### Problem: Production release from feature branch

```
✗ Production releases must be created from main branch
ℹ Current branch: feature/my-feature
ℹ Switch to main: git checkout main
```

**Solution:** Either:
1. Switch to main: `git checkout main`
2. Use beta version: `./scripts/release beta`
3. Override (not recommended): `./scripts/release --force-branch`

#### Problem: Tag already exists

```
✗ Tag already exists locally: v2.5.0
```

**Solution:** Use a different version:
```bash
# Delete local tag if it's a mistake
git tag -d v2.5.0

# Or use a different version
./scripts/release 2.5.1
```

#### Problem: GitHub CLI not authenticated

```
✗ GitHub CLI not authenticated
ℹ Run: gh auth login
```

**Solution:** Authenticate with GitHub:
```bash
gh auth login
# Follow the prompts to authenticate
```

#### Problem: ZIP asset not found

```
✗ ZIP asset not found: adaptive_cover_pro.zip
```

**Solution:** Check GitHub Actions workflow:
```bash
# View recent workflow runs
gh run list --workflow=publish-release.yml

# View specific run details
gh run view <run-id>
```

The workflow might have failed. Check the logs and re-run if necessary.

#### Problem: Workflow timeout

```
✗ Workflow did not complete within 60s
```

**Solution:** The workflow is probably still running:
```bash
# Check workflow status
gh run list --workflow=publish-release.yml

# Wait for it to complete, then manually edit the release
gh release edit v2.5.0 --title "Title" --notes "Notes"
```

### Rollback on Failure

The release script automatically rolls back changes if an error occurs:

1. **Deletes the local tag** (if created)
2. **Deletes the remote tag** (if pushed)
3. **Resets the commit** (if manifest.json was committed)

If you need to manually rollback:

```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push --delete origin vX.Y.Z

# Reset last commit (if needed)
git reset --hard HEAD^

# Force push to remote (if commit was already pushed)
git push --force origin feature/branch-name
```

### CI/CD Mode

For automated releases in CI/CD pipelines:

```bash
# Non-interactive, no prompts, auto-generated notes
./scripts/release beta --yes --auto-notes
```

**Environment variables needed:**
- `GITHUB_TOKEN` - For `gh` authentication
- GitHub Actions automatically provides this

## Code Standards

### Python Style Guide

We use **Ruff** for linting and formatting, configured in `pyproject.toml`.

**Configuration:**
- Select: `["ALL"]` - Enable all rules by default
- Specific ignores for formatter conflicts and false positives
- Home Assistant import conventions: `cv`, `dr`, `er`, `ir`, `vol`
- Force sorting within sections for imports

**Run linting:**
```bash
./scripts/lint
```

### Import Order

Imports are organized into sections:

```python
"""Module docstring."""
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import logging
from typing import Any

# 3. Third-party libraries
import voluptuous as vol
from astral import LocationInfo

# 4. Home Assistant core
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

# 5. Local imports
from .const import DOMAIN, CONF_SENSOR_TYPE
from .coordinator import AdaptiveDataUpdateCoordinator
```

### Async Best Practices

This integration uses Home Assistant's async architecture:

**DO:**
```python
async def async_my_function():
    """Async function."""
    result = await some_async_call()
    return result

@callback
def _sync_callback():
    """Callback function (no I/O)."""
    return value
```

**DON'T:**
```python
def blocking_function():
    """This blocks the event loop!"""
    time.sleep(1)  # ❌ Never block!
    return requests.get(url)  # ❌ Use aiohttp!
```

**Rules:**
- Never block the event loop
- Use `async`/`await` for I/O operations
- Use `@callback` decorator for sync callbacks
- Use `hass.async_add_executor_job()` for blocking calls

### Logging

Use the logging adapter with context:

```python
from .config_context_adapter import get_adapter

_LOGGER = logging.getLogger(__name__)

# In your class
self._adapter = get_adapter(_LOGGER, self._name)

# Log with context
self._adapter.debug("Message here")
```

**Log levels:**
- `debug()` - Detailed diagnostic information
- `info()` - General informational messages
- `warning()` - Warning messages (recoverable issues)
- `error()` - Error messages (serious problems)

### Entity Naming

Follow Home Assistant conventions:

```python
# Entity ID format
entity_id = f"{domain}.{type}_{description}_{name}"

# Examples
"sensor.adaptive_cover_position_living_room"
"switch.adaptive_cover_control_bedroom"
"binary_sensor.adaptive_cover_sun_in_window_office"
```

### Configuration Validation

Use Home Assistant's voluptuous integration:

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_FOV, default=90): vol.All(
        vol.Coerce(int),
        vol.Range(min=1, max=180)
    ),
})
```

## Debugging

### Debug Logging

Enable debug logging in `config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.adaptive_cover_pro: debug
```

### Common Issues

#### Issue: Entity not updating

**Cause:** Coordinator not triggering updates

**Solution:**
- Check if entity is listening to coordinator
- Verify `_handle_coordinator_update()` is called
- Check coordinator's `async_update_listeners()` is called

#### Issue: Position calculation incorrect

**Cause:** Sun position or geometry calculation

**Solution:**
- Enable diagnostic sensors to see calculated values
- Use Jupyter notebook to visualize calculations
- Check sun position: azimuth, elevation
- Verify window azimuth and field of view

#### Issue: Manual override not detected

**Cause:** Threshold or state comparison

**Solution:**
- Check `manual_override_threshold` setting
- Verify cover entity reports position correctly
- Enable Last Cover Action diagnostic sensor
- Check logs for "Manual override detected" messages

### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Home Assistant",
      "type": "python",
      "request": "launch",
      "module": "homeassistant",
      "args": [
        "-c",
        "config",
        "--debug"
      ],
      "justMyCode": false
    }
  ]
}
```

Set breakpoints in the code and launch with F5.

## Architecture Notes

### Data Coordinator Pattern

The integration uses Home Assistant's **Data Coordinator Pattern**:

```
┌─────────────────────────────────────┐
│  AdaptiveDataUpdateCoordinator      │
│  (coordinator.py)                   │
│                                     │
│  - Manages entity listeners         │
│  - Coordinates updates              │
│  - Calls calculation engine         │
│  - Controls cover entities          │
└─────────┬───────────────────────────┘
          │
          ├──> Listens to: sun, temp, weather, presence
          │
          ├──> Calls: AdaptiveVerticalCover/Horizontal/Tilt
          │            (calculation.py)
          │
          └──> Updates: sensor, switch, binary_sensor, button
                        (platform files)
```

### Cover Calculation Classes

Position calculations are in `calculation.py`:

- **`AdaptiveVerticalCover`** - Up/down blind calculations
- **`AdaptiveHorizontalCover`** - In/out awning calculations
- **`AdaptiveTiltCover`** - Slat rotation calculations
- **`NormalCoverState`** - Basic sun position mode
- **`ClimateCoverState`** - Climate-aware mode

Each has a `calculate_position()` method that returns 0-100.

### State Flow

```
1. State Change (sun/temp/weather/presence)
   ↓
2. Coordinator: async_check_entity_state_change()
   ↓
3. Coordinator: _async_update_data()
   ↓
4. Calculation: calculate_position()
   ↓
5. Coordinator: Apply inverse/interpolation
   ↓
6. Coordinator: Check if should control
   ↓
7. Coordinator: Call cover service
   ↓
8. Coordinator: Update entity listeners
   ↓
9. Entities: _handle_coordinator_update()
```

### Inverse State Behavior

**CRITICAL:** Do not change this behavior without careful consideration.

The `inverse_state` feature handles covers that don't follow Home Assistant guidelines:

1. Calculate position (0-100)
2. Apply inverse if enabled: `state = 100 - state`
3. For open/close-only covers: Compare inverted state to threshold
4. Send command to cover

See CLAUDE.md "Inverse State Behavior" section for full details.

### Configuration Flow UI

The integration provides a comprehensive multi-step configuration UI (`config_flow.py`):

**Enhanced User Experience:**
- **Rich Field Descriptions:** Every configuration field includes detailed descriptions with practical examples, recommended values, and context
- **Visual Units:** All numeric selectors display appropriate units (°, %, m, cm, minutes, lux, W/m²)
- **Consistent Interface:** NumberSelector with sliders for most numeric inputs, providing clear min/max bounds
- **Technical Term Explanations:** Complex concepts like azimuth, FOV (field of view), and elevation are explained in user-friendly language

**Translation Support:**
- English descriptions are in `strings.json` (base file) and `translations/en.json`
- Additional languages supported: German (de), Spanish (es), French (fr), Dutch (nl), Slovak (sk)
- Translations can be added by copying `strings.json` structure and translating the `data_description` values

**Configuration Steps:**
1. Initial setup: Choose cover type (vertical/horizontal/tilt)
2. Cover-specific settings: Dimensions, orientation, tracking parameters
3. Automation settings: Delta position/time, manual override, start/end times
4. Climate mode (optional): Temperature, presence, weather, lux/irradiance sensors
5. Weather conditions (if climate mode enabled)
6. Blind spot (optional): Define obstacles that block sun
7. Interpolation (optional): Custom position mapping for non-standard covers

**Best Practices for Config Flow Changes:**
- Always add `data_description` for new fields in `strings.json`
- Use `NumberSelector` with `unit_of_measurement` for all numeric inputs
- Provide practical examples and typical values in descriptions
- Test configuration flow on mobile and desktop interfaces
- Keep descriptions concise but informative (2-4 sentences ideal)

## Additional Resources

- **User Documentation:** [README.md](README.md)
- **AI Assistant Instructions:** [CLAUDE.md](CLAUDE.md)
- **Home Assistant Docs:** https://developers.home-assistant.io/
- **Python Async Guide:** https://docs.python.org/3/library/asyncio.html
- **Ruff Documentation:** https://docs.astral.sh/ruff/

## Getting Help

- **Issues:** https://github.com/jrhubott/adaptive-cover/issues
- **Discussions:** https://github.com/jrhubott/adaptive-cover/discussions
- **Home Assistant Community:** https://community.home-assistant.io/

---

**Happy developing! 🚀**
