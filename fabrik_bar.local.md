---
# fabrik_bar Configuration

## Statusline Settings

### show_bundles
Display bundle count from Elle's context.
- Type: boolean
- Default: true

### show_session_timer
Display session duration timer.
- Type: boolean
- Default: true

### show_gh_info
Show GitHub PR number (requires gh CLI).
- Type: boolean
- Default: true

### show_cache_detail
Show cache token details (R:read W:write).
- Type: boolean
- Default: true

### mcp_check_timeout
**NOT IMPLEMENTED** - Reserved for future use.
- Type: integer (milliseconds)
- Default: 500

## Hook Notifications

### session_start
Controls session startup summary.

#### enabled
Enable session start summary.
- Type: boolean
- Default: true

#### show_summary
Show detailed summary.
- Type: boolean
- Default: true

### context_alerts
Controls context window usage alerts.

#### enabled
Enable context alerts.
- Type: boolean
- Default: true

#### warning_threshold
Percentage for warning alert (⚡).
- Type: integer (0-100)
- Default: 80

#### critical_threshold
Percentage for critical alert (⚠️).
- Type: integer (0-100)
- Default: 90
- Must be greater than warning_threshold

### git_events
Controls git event notifications.

#### enabled
Enable git event detection.
- Type: boolean
- Default: true

#### events
List of git events to notify about.
- Type: list of strings
- Valid values: branch_switch, commit, merge, push, pull
- Default: ["branch_switch", "commit", "merge", "push"]

### context_changes
**NOT FULLY IMPLEMENTED** - Reserved for future use.

#### enabled
Enable context change notifications.
- Type: boolean
- Default: true

#### notify_on_bundle_change
Notify when bundles change.
- Type: boolean
- Default: true

## Theme Colors

Gentleman theme color palette.

### primary
Primary blue (#7FB4CA)
### accent
Accent gold (#E0C15A)
### secondary
Secondary mauve (#A3B5D6)
### success
Success green (#B7CC85)
### error
Error red (#CB7C94)
---
