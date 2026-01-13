---
# fabrik_bar Configuration

# Statusline settings
statusline:
  show_bundles: true
  show_session_timer: true
  show_gh_info: true
  show_cache_detail: true
  mcp_check_timeout: 500  # ms

# Hook notifications
hooks:
  session_start:
    enabled: true
    show_summary: true

  context_alerts:
    enabled: true
    warning_threshold: 80  # %
    critical_threshold: 90  # %

  git_events:
    enabled: true
    events: ["branch_switch", "commit", "merge", "push"]

  context_changes:
    enabled: true
    notify_on_bundle_change: true

# Theme (Gentleman defaults)
theme:
  colors:
    primary: "#7FB4CA"
    accent: "#E0C15A"
    secondary: "#A3B5D6"
    success: "#B7CC85"
    error: "#CB7C94"
---
