# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For comprehensive developer documentation, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - This file contains instructions for Claude Code specifically, while docs/DEVELOPMENT.md is the human-readable developer guide.

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
- `AdaptiveVerticalCover` - Up/down blind calculations with enhanced geometric accuracy
  - `calculate_position()` - Main calculation with safety margins and window depth support
  - `_calculate_safety_margin()` - Angle-dependent safety margins (0-35% at extremes)
  - `_handle_edge_cases()` - Robust fallbacks for extreme sun angles
  - Supports optional `window_depth` parameter for advanced precision
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
- ✅ ALWAYS create a pull request after pushing the branch
- ✅ Keep commits atomic and focused
- ✅ Test changes on the feature branch
- ❌ NEVER commit directly to `main` branch
- ❌ NEVER skip feature branches "because it's a small change"
- ❌ NEVER merge to main without a pull request

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

**Step 4: Push and Create Pull Request**
```bash
# Push feature branch
git push -u origin fix/issue-123-sensor-unavailable

# Create pull request immediately after pushing
# For issue-related branches, link PR to the issue
gh pr create --title "fix: Short description of fix (#123)" \
             --body "Fixes #123" \
             --base main

# Or for non-issue branches
gh pr create --title "fix: Short description of fix" \
             --base main

# The PR description should include:
# - Summary of changes
# - Testing performed
# - Related issues (Fixes #123, Related to #456)
```

**Pull Request Guidelines:**
- ✅ ALWAYS create a PR after pushing a branch
- ✅ Link PRs to issues using "Fixes #123" in the PR body
- ✅ Use descriptive PR titles matching the commit convention (fix:, feat:, docs:)
- ✅ Include testing details in PR description
- ❌ NEVER merge branches directly without a PR
- ❌ NEVER skip PR creation "because it's a small change"

**Merging:**
- Only merge PRs to main after review and all checks pass
- Use GitHub UI or: `gh pr merge <PR-number> --squash` (or --merge/--rebase)
- Issues will auto-close when PR is merged if "Fixes #123" is in PR body

### Pull Request Workflow

**CRITICAL: All branches MUST have a pull request before merging to main.**

**When to Create a PR:**
- ✅ Immediately after pushing any feature/fix/docs branch
- ✅ For ALL branches, regardless of size or complexity
- ✅ Even for single-commit changes

**PR Creation Process:**

1. **After pushing branch:**
   ```bash
   # If addressing an issue
   gh pr create --title "fix: Description of fix (#123)" \
                --body "## Summary

   Brief description of changes

   ## Testing
   - Tested scenario 1
   - Tested scenario 2

   ## Related Issues
   Fixes #123" \
                --base main

   # If NOT addressing a specific issue
   gh pr create --title "feat: Description of feature" \
                --body "## Summary

   Brief description of changes

   ## Testing
   - Tested scenario 1
   - Tested scenario 2" \
                --base main
   ```

2. **PR Title Format:**
   - Use conventional commit format: `fix:`, `feat:`, `docs:`, `chore:`, `test:`
   - Include issue number if applicable: `fix: Description (#123)`
   - Keep under 70 characters

3. **PR Body Requirements:**
   - **Summary:** What changed and why
   - **Testing:** What was tested and results
   - **Related Issues:** Use `Fixes #123` to auto-close issues when PR merges

4. **Linking PRs to Issues:**
   - Use keywords in PR body: `Fixes #123`, `Closes #123`, `Resolves #123`
   - Multiple issues: `Fixes #123, Fixes #456`
   - Non-closing reference: `Related to #123`, `Part of #123`
   - Issue will automatically close when PR is merged to main

**Example PR Body Template:**
```markdown
## Summary

Added 30-second startup grace period to prevent false manual override
detection when Home Assistant restarts and covers respond slowly.

## Testing

- ✅ All 248 tests passing
- ✅ 8 new tests for startup grace period
- ✅ Linting clean
- ✅ Tested HA restart scenario with slow-responding covers

## Related Issues

Fixes #11
```

**Common PR Operations:**
```bash
# View PR details
gh pr view

# Check PR status (from any branch)
gh pr status

# View PR in browser
gh pr view --web

# List all open PRs
gh pr list

# Add reviewers
gh pr edit --add-reviewer username

# Update PR title
gh pr edit --title "New title"

# Merge PR (after approval)
gh pr merge --squash    # Squash commits (recommended)
gh pr merge --merge     # Standard merge
gh pr merge --rebase    # Rebase and merge
```

### Merging and Release Workflow

**CRITICAL: Context-Aware Merge Behavior**

**When Exiting Plan Mode:**
- ✅ ALWAYS ask the user if they want to:
  1. Create a pull request (if not already created)
  2. Merge the PR and create a production release
  3. Create a beta release (without merging to main)
- Use the AskUserQuestion tool to present these options
- Wait for user confirmation before proceeding with PR creation, merge, or release

**When NOT in Plan Mode (ad-hoc changes):**
- ✅ Create a pull request after pushing changes (always required)
- ✅ Stay on the feature/fix branch after pushing changes
- ❌ DO NOT ask about merging to main
- ❌ DO NOT merge automatically
- The user will decide when to merge the PR separately

**Example Question (Plan Mode Only):**
```
After completing the implementation, ask:
"The changes have been committed and pushed to the feature branch. What would you like to do next?"

Options:
1. Create a pull request (linking to issue #123 if applicable)
2. Create a pull request and merge to main
3. Create a beta release (stay on feature branch)
4. Stay on feature branch for more testing
```

**gh CLI Quick Reference:**

| Task | Command |
|------|---------|
| View issue | `gh issue view 123` |
| List open issues | `gh issue list` |
| List by label | `gh issue list --label bug` |
| Add comment | `gh issue comment 123 --body "Message"` |
| Close manually | `gh issue close 123 --comment "Fixed in v2.6.8"` |
| Create PR | `gh pr create --title "Fix: Description (#123)" --body "Fixes #123"` |
| Link PR to issue | Include "Fixes #123" in PR body |
| View PR | `gh pr view 456` |
| List PRs | `gh pr list` |
| Merge PR | `gh pr merge 456 --squash` (or --merge/--rebase) |
| Check PR status | `gh pr status` |

### Commit Message Guidelines

**CRITICAL:** Git commits must NOT include Claude attribution:
- ❌ NEVER add `Co-Authored-By: Claude` lines
- ❌ NEVER add `Generated with Claude Code`
- ✅ Commit messages should only describe the changes made

This applies to ALL commits (regular commits, merge commits, etc.) and release notes.

### Release Strategy

**Release Notes Directory:**
- All release notes stored in `release_notes/` directory
- Filename format: `vX.Y.Z.md` or `vX.Y.Z-beta.N.md`
- Provides historical tracking of all releases
- Committed to git for version control

**Feature Branch:**
- Create BETA releases: `./scripts/release beta --notes release_notes/v2.7.0-beta.1.md --yes`
- Beta version format: `v2.7.0-beta.1`
- Mark as prerelease for testing

**Main Branch:**
- Create STABLE releases: `./scripts/release patch --notes release_notes/v2.7.0.md --yes`
- Only merge to main AFTER successful beta testing
- Stable version format: `v2.7.0`

**⚠️ CRITICAL:** Only create releases when explicitly requested by the user.
- ❌ NEVER create a release proactively
- ✅ ONLY create releases when user explicitly asks

## Testing

**For comprehensive testing documentation, see [docs/UNIT_TESTS.md](docs/UNIT_TESTS.md)**

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
- ❌ NEVER create releases proactively
- ✅ ONLY create when user explicitly asks

### Release Script: `./scripts/release`

The release script automates version management, git tagging, and GitHub release creation.

**Usage:**
```bash
./scripts/release [VERSION_SPEC] [OPTIONS]
```

### Version Specification

| Spec | Description | Example Result |
|------|-------------|----------------|
| `patch` | Increment patch version (X.Y.Z+1) | 2.6.8 → 2.6.9 |
| `minor` | Increment minor version (X.Y+1.0) | 2.6.8 → 2.7.0 |
| `major` | Increment major version (X+1.0.0) | 2.6.8 → 3.0.0 |
| `beta` | Auto-increment beta version | 2.6.8 → 2.6.9-beta.1<br>2.6.8-beta.1 → 2.6.8-beta.2 |
| `X.Y.Z` | Explicit version number | 2.7.0 (explicit) |
| `X.Y.Z-beta.N` | Explicit beta version | 2.7.0-beta.5 (explicit) |
| *(omitted)* | Interactive mode (prompts for choice) | User selects from menu |

**How `beta` works:**
- If current version is stable (e.g., `2.6.8`) → creates `2.6.9-beta.1` (next patch's first beta)
- If current version is beta (e.g., `2.6.9-beta.1`) → creates `2.6.9-beta.2` (increment beta number)

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | | Preview operations without executing any changes |
| `--yes` | `-y` | Skip all confirmation prompts (CI/automation mode) |
| `--notes FILE` | | Read release notes from specified file |
| `--auto-notes` | | Use auto-generated template notes only |
| `--force-branch` | | Skip branch validation (use with caution) |
| `--help` | `-h` | Show help text and exit |

**Note:** `--editor` option exists in script but should **NOT** be used per CLAUDE.md guidelines. Always use `--notes` parameter instead.

### Common Usage Patterns

**Standard workflow (recommended):**
```bash
# 1. Create release_notes directory if it doesn't exist
mkdir -p release_notes

# 2. Generate release notes (use version number in filename)
cat > release_notes/v2.6.11.md << 'EOF'
## 🎯 Release Title

### ✨ Features
- Feature 1

### 🐛 Bug Fixes
- Fix 1

### 🧪 Testing
- Tested with Python 3.11 and 3.12
- Home Assistant 2024.5.0+
EOF

# 3. Commit the release notes to git FIRST (release script requires clean working directory)
git add release_notes/v2.6.11.md
git commit -m "docs: Add release notes for v2.6.11"

# 4. Create release (handles version bump, tag, and push automatically)
./scripts/release patch --notes release_notes/v2.6.11.md --yes
```

**CRITICAL:** The release script requires a clean working directory. You MUST commit the release notes file before running the release script, not after. The release script will automatically:
- Update manifest.json version
- Create version bump commit
- Create annotated git tag
- Push both commits and tag to GitHub
- Create GitHub release with ZIP asset

**Quick beta release:**
```bash
# Auto-increment beta, skip confirmations, use auto-generated notes
./scripts/release beta --yes --auto-notes
```

**Preview before executing:**
```bash
# See what would happen without making changes
./scripts/release patch --dry-run
```

**Explicit version:**
```bash
# Use specific version number (create release notes first)
./scripts/release 2.7.0 --notes release_notes/v2.7.0.md --yes
```

**Interactive mode:**
```bash
# Select version type from menu
./scripts/release
```

### What the Script Does

The script automates the complete release workflow:

1. **Validates environment** - Checks for git, gh, jq; verifies authentication
2. **Checks working directory** - Ensures no uncommitted changes
3. **Calculates version** - Based on VERSION_SPEC and current version
4. **Validates branch** - Ensures beta from feature branch, stable from main
5. **Checks tag** - Verifies tag doesn't already exist
6. **Updates manifest.json** - Sets new version number
7. **Creates git commit** - Commits version change
8. **Creates annotated tag** - Tags with release notes
9. **Pushes to GitHub** - Pushes commit and tag to remote
10. **Waits for workflow** - Monitors GitHub Actions workflow completion
11. **Edits release** - Updates GitHub release with notes and prerelease flag
12. **Verifies ZIP asset** - Confirms `adaptive_cover_pro.zip` was created

### Release Notes Guidelines

**CRITICAL Rules:**
- **NEVER** include `Co-Authored-By:` lines
- **NEVER** include Claude/AI attributions
- **ALWAYS** use `--notes` parameter with versioned filename: `release_notes/vX.Y.Z.md`
- **NEVER** use `--editor` parameter
- **ALWAYS** commit release notes to git after creating release

**File Naming Convention:**
- Production releases: `release_notes/v2.6.11.md`
- Beta releases: `release_notes/v2.7.0-beta.1.md`
- Directory: `release_notes/` (tracked in git)

**Content Guidelines:**
- Use clear, user-friendly language
- Include emoji section headers (🎯, ✨, 🐛, 📚, 🧪)
- Document: Features, Bug Fixes, Documentation, Technical Details, Installation, Testing
- For beta releases: Include testing instructions and warnings

### Branch-Based Release Strategy

| Branch Type | Release Type | Command | Version Format |
|-------------|--------------|---------|----------------|
| `feature/*`, `fix/*` | Beta (prerelease) | `./scripts/release beta --notes release_notes/v2.7.0-beta.1.md --yes` | `v2.7.0-beta.1` |
| `main` | Stable (production) | `./scripts/release patch --notes release_notes/v2.7.0.md --yes` | `v2.7.0` |

**⚠️ WARNING:** If you find yourself creating a beta release from main, STOP! You should have created a feature branch first.

**Workflow:**
1. **Feature branch** → Create beta release → Test
2. **Merge to main** → Create stable release

### Error Handling and Rollback

The script includes automatic rollback on failure:
- Deletes created tags (local and remote)
- Resets commits if version bump was created
- Prevents partial releases

If a release fails:
1. Script automatically rolls back changes
2. Check error message for cause
3. Fix issue and retry
4. Use `--dry-run` to preview before retry

### Troubleshooting

**Common issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| "Working directory not clean" | Uncommitted changes | Commit or stash changes first |
| "Tag already exists" | Tag created previously | Delete tag or use different version |
| "GitHub CLI not authenticated" | Not logged into gh | Run `gh auth login` |
| "Production releases must be from main" | Wrong branch | Switch to main or use `--force-branch` (not recommended) |
| "ZIP asset not found" | Workflow failed | Check GitHub Actions logs |

**Check workflow status:**
```bash
gh run list --workflow=publish-release.yml
```

**View release:**
```bash
gh release view v2.6.8
```

## Documentation Guidelines

### README.md Updates

**CRITICAL:** Always update README.md when adding new features or making user-visible changes.

**Required Updates:**
1. **Features Section** - Add bullet points describing the new feature
2. **Entities Section** - Add new entities to appropriate table
3. **Variables Section** - Document new configuration variables (if applicable)
4. **Known Limitations** - Document limitations or edge cases (if applicable)

### DEVELOPMENT.md Updates

**CRITICAL:** Always update docs/DEVELOPMENT.md when making changes that affect the development process.

**When to Update:**
- New development scripts
- Changes to release process
- Architecture changes
- New testing strategies
- Code standards changes
- Project structure changes
- Debugging tools/techniques

### VSCODE_TESTING_GUIDE.md Updates

**CRITICAL:** Always update docs/VSCODE_TESTING_GUIDE.md when making changes that affect the VS Code testing workflow.

**When to Update:**
- New VS Code debug configurations
- Changes to launch.json or tasks.json
- New testing keyboard shortcuts
- Test runner configuration changes
- VS Code extension recommendations
- Testing UI workflow changes
- Debugging tips and techniques for VS Code

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

### Enhanced Geometric Accuracy

**Added in v2.7.0** to fix Issue #1 (shadow calculation accuracy at extreme angles).

The integration includes sophisticated geometric enhancements to ensure accurate sun blocking across all sun positions. These improvements are implemented in `AdaptiveVerticalCover.calculate_position()` in `calculation.py`.

#### Implementation Details

**Phase 1: Core Formula Enhancements (Automatic)**

1. **Edge Case Handling** (`_handle_edge_cases()`)
   - Elevation < 2°: Returns full window coverage (h_win)
   - |Gamma| > 85°: Returns full window coverage (h_win)
   - Elevation > 88°: Uses simplified calculation (distance × tan(elevation))
   - Returns tuple: `(is_edge_case: bool, position: float)`

2. **Safety Margins** (`_calculate_safety_margin()`)
   - Returns multiplier ≥1.0 to increase blind extension
   - Gamma margin: Smoothstep interpolation from 1.0 (at 45°) to 1.2 (at 90°)
   - Low elevation margin: Linear from 1.0 (at 10°) to 1.15 (at 0°)
   - High elevation margin: Linear from 1.0 (at 75°) to 1.1 (at 90°)
   - Margins combine multiplicatively (margin = gamma_margin × elev_margin)

3. **Calculation Flow**
   ```python
   def calculate_position(self) -> float:
       # 1. Check edge cases first
       is_edge_case, edge_position = self._handle_edge_cases()
       if is_edge_case:
           return edge_position

       # 2. Account for window depth (if configured)
       effective_distance = self.distance
       if self.window_depth > 0 and abs(self.gamma) > 10:
           depth_contribution = self.window_depth * sin(rad(abs(self.gamma)))
           effective_distance += depth_contribution

       # 3. Base calculation
       path_length = effective_distance / cos(rad(self.gamma))
       base_height = path_length * tan(rad(self.sol_elev))

       # 4. Apply safety margin
       safety_margin = self._calculate_safety_margin(self.gamma, self.sol_elev)
       adjusted_height = base_height * safety_margin

       # 5. Clip to window height
       return np.clip(adjusted_height, 0, self.h_win)
   ```

**Phase 2: Window Depth Parameter (Optional)**

- Added `window_depth` field to `AdaptiveVerticalCover` dataclass (default 0.0)
- Configured via `CONF_WINDOW_DEPTH` in config flow (0.0-0.5m range)
- Only affects calculation when `window_depth > 0` and `|gamma| > 10°`
- Adds horizontal offset: `depth_contribution = window_depth × sin(|gamma|)`
- Accounts for window reveals/frames creating additional shadow

#### Testing Requirements

When modifying geometric accuracy calculations:

1. **Run existing tests** to ensure no regression:
   ```bash
   source venv/bin/activate
   python -m pytest tests/test_geometric_accuracy.py -v
   ```

2. **Test coverage requirements:**
   - Safety margin behavior at all angle ranges
   - Edge case handling at thresholds
   - Smooth transitions across ranges
   - Regression tests (<5% deviation at normal angles)
   - Backward compatibility (window_depth=0 matches Phase 1)

3. **Key test files:**
   - `tests/test_geometric_accuracy.py` - 34 dedicated tests
   - `tests/test_calculation.py` - Integration with existing calculation tests

#### Modification Guidelines

**DO:**
- Test all changes with full test suite (214 tests must pass)
- Maintain backward compatibility (existing installations unaffected)
- Keep safety margins conservative (always ≥ baseline position)
- Use smoothstep interpolation for smooth transitions
- Document changes in commit messages and release notes

**DON'T:**
- Remove or reduce safety margins without thorough testing
- Change edge case thresholds without testing transitions
- Break backward compatibility (window_depth must default to 0.0)
- Introduce numerical instability (NaN, infinity)
- Skip regression testing at normal angles

**CRITICAL:**
- Safety margins are intentionally conservative to ensure sun blocking
- Edge case thresholds chosen to prevent numerical instability
- Smoothstep interpolation prevents jarring position changes
- Window depth is optional (Phase 1 works standalone)

#### Diagnostic Information

Users can monitor geometric accuracy via diagnostic sensors:
- "Calculated Position" - Raw position before adjustments
- "Sun Gamma" - Horizontal angle from window normal
- "Sun Elevation" - Vertical angle above horizon
- Compare calculated vs actual position to see safety margin effects

## Configuration Structure

**`config_entry.data`** (setup phase):
- `name` - Instance name
- `sensor_type` - cover_blind/cover_awning/cover_tilt

**`config_entry.options`** (configurable):
- Window azimuth, field of view, elevation limits
- Cover-specific dimensions (height, length, slat properties)
- Enhanced geometric accuracy:
  - `window_depth` - Optional window reveal/frame depth (0.0-0.5m, default 0.0)
  - Safety margins and edge case handling apply automatically (not configurable)
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
├── release_notes/               # Historical release notes
│   ├── README.md                # Release notes documentation
│   └── vX.Y.Z.md                # Individual release notes (versioned)
├── docs/                        # Documentation directory
│   ├── ARCHITECTURE.md          # Architecture documentation
│   ├── CONTRIBUTING.md          # Contributing guidelines
│   ├── DEVELOPMENT.md           # Developer documentation
│   ├── UNIT_TESTS.md            # Unit test documentation
│   └── VSCODE_TESTING_GUIDE.md  # VS Code testing guide
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
