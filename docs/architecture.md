# fabrik_bar Architecture

## Overview

fabrik_bar is a Claude Code plugin that provides:
1. Persistent statusline with session information
2. Contextual hook notifications (session start, context alerts, git events)

## Architecture

```
fabrik_bar/
├── hooks/              # Hook entry points (infrastructure layer)
│   ├── session_start.py
│   ├── user_prompt_submit.py
│   └── git_watcher.py
├── lib/                # Business logic (mixed domain + infrastructure)
│   ├── config.py       # Configuration loading with I/O
│   ├── validator.py    # Pure validation logic
│   ├── notifier.py     # Pure formatting functions
│   ├── logger.py       # Logging infrastructure
│   ├── hook_utils.py   # Shared hook utilities
│   ├── models.py       # TypedDict domain models
│   └── schema.py       # Input schema validation
├── scripts/            # Utility scripts
│   └── verify_installation.py
└── tests/              # Test suite
    ├── hooks/
    ├── lib/
    └── scripts/
```

## Design Principles

### Current State

The codebase follows **partial** Clean Architecture and FP principles:

**✅ Good:**
- Pure functions in `notifier.py` and `validator.py`
- Hooks are thin entry points
- Business logic separated from I/O in some areas

**❌ Needs Improvement:**
- No clear domain layer separation
- Infrastructure concerns mixed with business logic in `config.py`
- No Protocol interfaces for dependency inversion
- Generic `Dict[str, Any]` types instead of proper models (being addressed in Task 9)

## Hook Flow

All hooks follow this pattern:

1. Read JSON from stdin
2. Parse with error handling (exit 0 on failure)
3. Load configuration
4. Execute business logic
5. Output JSON to stdout

## Error Handling Strategy

Hooks use `exit(0)` on errors to prevent Claude Code from disabling them.
Errors are logged to stderr for debugging.

## Dependencies

- Python 3.11+
- pytest (testing)
- mypy (type checking)
- Claude Code hook framework
