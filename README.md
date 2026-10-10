# fabrik_bar

Hybrid information display system for Claude Code.

## Overview

fabrik_bar combines two complementary information systems:

1. **Enhanced statusline.sh** - Persistent status bar with real-time updates (300ms)
2. **Hook-based notifications** - Contextual alerts for important events

## Features

### Statusline (Persistent)

Located at `~/.claude/statusline.sh`, displays:

| Element | Description |
|---------|-------------|
| 🎭 Opus | Model name with icon |
| 󰉋 Developer | Current directory |
| main* | Git branch with dirty indicator |
| +42 -13 | Lines added/removed |
| ctx ███░░░░░ 25% R:1200 W:300 | Context bar with cache details |
| 📦 9 | Bundle count from Elle's context |
| MCP: 5 | Connected MCP servers |
| ⏱ 01:23:45 | Session duration timer |
| 🔶 #42 | GitHub PR number (via gh cli) |

### Hook Notifications (Event-Driven)

| Hook | Event | Description |
|------|-------|-------------|
| SessionStart | Session start | Shows context, bundles, MCP servers, model |
| UserPromptSubmit | Context usage | Alerts at 80% (⚡) and 90% (⚠️) |
| PreToolUse | Git commands | Detects branch switch, commit, merge, push |

## Configuration

Edit `~/.claude/plugins/fabrik_bar/fabrik_bar.local.md`:

```yaml
hooks:
  context_alerts:
    warning_threshold: 80   # % for ⚡ warning
    critical_threshold: 90  # % for ⚠️ critical
  git_events:
    events: ["branch_switch", "commit", "merge", "push"]
```

## Requirements

- Claude Code with statusLine support
- Python 3
- jq (for JSON parsing in bash)
- gh cli (optional, for GitHub PR info)

## Theme

Uses Gentleman theme colors:

| Color | Hex | Name |
|-------|-----|------|
| #7FB4CA | azul claro | Primary |
| #E0C15A | dorado | Accent |
| #A3B5D6 | azul gris | Secondary |
| #B7CC85 | verde | Success |
| #CB7C94 | rosa/rojo | Error |

## Architecture

```
fabrik_bar/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── hooks/
│   ├── hooks.json           # Hook registration
│   ├── session_start.py     # Session summary
│   ├── user_prompt_submit.py # Context alerts
│   └── git_watcher.py       # Git events
├── lib/
│   ├── __init__.py
│   ├── config.py            # Configuration loader
│   └── notifier.py          # Notification formatter
└── fabrik_bar.local.md      # Local configuration
```

## Troubleshooting

### Statusline not appearing
- Check `~/.claude/settings.json` has statusLine config
- Verify `statusline.sh` is executable: `chmod +x ~/.claude/statusline.sh`
- Check Claude Code logs: `~/.claude/logs/`

### Hooks not firing
- Verify Python scripts are executable: `chmod +x hooks/*.py`
- Enable debug logging: `export FABRIK_DEBUG=1`
- Check hook JSON syntax: `cat hooks/hooks.json | jq .`

### Missing bundle info
- Verify `~/.claude/.context/core/` directory exists
- Check context files are present

### Session timer not incrementing
- Check `~/.claude/tmp/session_start` file permissions
- Verify date command works

### GitHub PR info not showing
- Verify gh CLI is installed: `gh --version`
- Check you're in a git repository with an open PR
- Check auth: `gh auth status`

## Performance Considerations

- **Statusline refresh rate**: Controlled by Claude Code (~300ms)
- **GitHub PR caching**: PR info cached for 60 seconds to avoid network calls
- **Git commands**: Use `git -C` to run in workspace directory
- **MCP checking**: Reads mcp.json on each refresh (no caching)

## Development

See design doc: `~/.claude/docs/plans/2026-01-13-fabrik_bar-design.md`

## License

MIT
# Test PR Demo
This is a demo PR for testing the test-pr skill.
