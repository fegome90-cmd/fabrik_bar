# fabrik_bar - Claude Code Plugin

Hybrid statusline + hook notification system for Claude Code.

## Quick Start

```bash
# Install dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Type check
mypy lib/

# Enable debug logging
export FABRIK_DEBUG=1
```

## Project Structure

```
lib/           # Business logic (config, git, notifier, logger)
hooks/         # Claude Code hook entry points
tests/         # pytest test suite (lib/, hooks/, scripts/)
scripts/       # Verification and utility scripts
docs/plans/    # Implementation plans and design docs
```

## Architecture

**Layered architecture:**
- `hooks/` → Infrastructure layer (stdin/stdout JSON)
- `lib/` → Domain layer (pure functions, no I/O)
- `tests/` → Black-box testing at boundaries

**Shared utilities:**
- `lib/hook_utils.py` → stdin reading, JSON output (used by all hooks)
- `lib/logger.py` → 4-tier fallback logging (stderr → file → __stderr__ → stdout)
- `lib/models.py` → TypedDict types for hook data

## Critical Anti-Patterns (AVOID)

Based on thorough code review findings:

### Error Handling

❌ **Catch-all exception hiding bugs**
```python
except Exception:
    return DEFAULTS  # Hides programming bugs!
```
✅ **Separate expected from unexpected errors**
```python
except (OSError, ValueError, KeyError) as e:
    log_error(f"Expected error: {e}")
    return DEFAULTS
except Exception as e:
    log_error(f"BUG: {type(e).__name__}: {e}\n{traceback.format_exc()}")
    raise  # Re-raise to make failure visible
```

### Hook Exit Codes

❌ **sys.exit(1) disables hooks on any error**
```python
except Exception:
    sys.exit(1)  # Claude Code disables the hook!
```
✅ **Exit 0 on recoverable errors, 1 only on fatal I/O**
```python
except JSONDecodeError:
    sys.stderr.write("[ERROR] Invalid JSON\n")
    sys.exit(0)  # Don't disable hook
except OSError as e:
    sys.stderr.write(f"[FATAL] Cannot write: {e}\n")
    sys.exit(1)  # Only exit 1 on I/O failure
```

### Error Return Values

❌ **Returning None for all errors indistinguishably**
```python
def get_current_branch() -> Optional[str]:
    # ... all errors return None
```
✅ **Use Union types or enums for distinguishable errors**
```python
class GitError(Enum):
    NOT_INSTALLED = "git_not_found"
    TIMEOUT = "git_timeout"
    NOT_REPO = "not_a_repository"

def get_current_branch() -> Union[str, GitError]:
    # ... return specific error types
```

### Test Coverage

❌ **Untested error paths**
- `lib/logger.py` had 38% coverage (only happy path)
- `lib/git.py` had no dedicated tests

✅ **Test every error branch**
- Mock all failure modes (OSError, TimeoutExpired, JSONDecodeError)
- Use `pytest.raises` for exception paths
- Target: 80% branch coverage minimum

### JSON Serialization

❌ **No fallback when dumps() fails**
```python
print(json.dumps(output))  # Crashes on unserializable data
```
✅ **Graceful degradation with error fallback**
```python
try:
    print(json.dumps(output))
except (TypeError, ValueError) as e:
    fallback = {"error": str(e)}
    print(json.dumps(fallback))
```

## Type Safety

**Current status:** Lenient mypy mode (`disallow_untyped_defs = false`)

**Baseline:** `docs/mypy-baseline.md` documents 28 existing type errors

**Goal:** Progressive migration to strict mode
1. Fix new code with proper types
2. Address baseline errors incrementally
3. Enable `disallow_untyped_defs = true` when baseline clear

## Testing Strategy

**Unit tests:** `tests/lib/` → Test pure functions in isolation
**Integration tests:** `tests/hooks/` → Test hook stdin/stdout behavior
**Fixtures:** `tests/conftest.py` → Shared test utilities

**Running tests:**
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=lib --cov=hooks

# Specific test file
pytest tests/lib/test_git.py -v
```

## Configuration

**Location:** `fabrik_bar.local.md` (YAML frontmatter)

**Loading:** `lib/config.py` parses with custom `_parse_simple_yaml()`

**Validation:** `lib/validator.py` validates thresholds and git events

## Documentation

- **README.md** → User-facing features and troubleshooting
- **docs/plans/** → Implementation plans and design docs
- **docs/mypy-baseline.md** → Type error baseline
- **docs/coverage-baseline.md** → Test coverage targets
- **docs/architecture.md** → Architecture patterns

## Development Workflow

1. **Write test** → TDD: RED-GREEN-REFACTOR
2. **Implement feature** → Keep functions small and pure
3. **Type check** → `mypy lib/` (ignore baseline errors)
4. **Run tests** → `pytest tests/ -v`
5. **Commit** → Conventional commits: `fix:`, `feat:`, `test:`

## Common Tasks

**Add new hook:**
1. Create `hooks/new_hook.py` (executable: `chmod +x`)
2. Register in `hooks/hooks.json`
3. Add tests in `tests/hooks/test_new_hook.py`

**Add new lib module:**
1. Create `lib/new_module.py` with type hints
2. Add tests in `tests/lib/test_new_module.py`
3. Export from `lib/__init__.py` if public API

**Debug hook issues:**
```bash
export FABRIK_DEBUG=1
# Check logs in ~/.claude/logs/fabrik_bar.log
```

## Known Issues

See `docs/plans/2026-01-15-thorough-review-fixes.md` for full list of addressed issues:
- ✅ Error handling improved (expected vs unexpected)
- ✅ Hook exit codes fixed (0 on recoverable, 1 on fatal)
- ✅ Git errors now distinguishable (GitError enum)
- ✅ Test coverage expanded (logger, git, hook_utils)
- ✅ Type annotations added (progressive migration)
