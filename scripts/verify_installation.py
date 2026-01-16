#!/usr/bin/env python3
"""Verify fabrik_bar installation integrity."""

import json
import os
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def check_plugin_json_consistency():
    """Verify both plugin.json files are consistent."""
    root_json = PLUGIN_DIR / "plugin.json"
    claude_plugin_json = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

    if not root_json.exists():
        print("❌ root plugin.json missing")
        return False

    if not claude_plugin_json.exists():
        print("❌ .claude-plugin/plugin.json missing")
        return False

    with open(root_json) as f:
        root_data = json.load(f)

    with open(claude_plugin_json) as f:
        claude_plugin_data = json.load(f)

    # Check hooks are defined in .claude-plugin
    if "hooks" not in claude_plugin_data:
        print("❌ .claude-plugin/plugin.json missing hooks array")
        return False

    hooks = claude_plugin_data.get("hooks", [])
    if len(hooks) != 3:
        print(f"❌ Expected 3 hooks, found {len(hooks)}")
        return False

    hook_names = {h["name"] for h in hooks}
    expected = {"session_start", "user_prompt_submit", "git_watcher"}
    if hook_names != expected:
        print(f"❌ Hook names mismatch: {hook_names} vs {expected}")
        return False

    # Check root doesn't have hooks (should only be in .claude-plugin)
    if "hooks" in root_data:
        print("⚠️  root plugin.json has hooks (should be minimal)")

    print("✅ plugin.json files consistent")
    return True


def check_settings_json():
    """Verify settings.json has fabrik_bar enabled."""
    if not SETTINGS_PATH.exists():
        print("⚠️  settings.json not found")
        return True

    with open(SETTINGS_PATH) as f:
        settings = json.load(f)

    enabled = settings.get("enabledPlugins", {}).get("fabrik_bar@local")
    if enabled is not True:
        print(f"❌ fabrik_bar@local not enabled: {enabled}")
        return False

    print("✅ settings.json has fabrik_bar@local enabled")
    return True


def check_hooks_json():
    """Verify hooks.json exists and is valid."""
    hooks_json = PLUGIN_DIR / "hooks" / "hooks.json"

    if not hooks_json.exists():
        print("❌ hooks/hooks.json missing")
        return False

    with open(hooks_json) as f:
        hooks_data = json.load(f)

    hooks = hooks_data.get("hooks", {})
    expected_events = {"SessionStart", "UserPromptSubmit", "PreToolUse"}

    if set(hooks.keys()) != expected_events:
        print(f"❌ hooks.json missing events: {set(hooks.keys())} vs {expected_events}")
        return False

    print("✅ hooks.json valid")
    return True


def check_hook_scripts():
    """Verify hook scripts exist."""
    hooks_dir = PLUGIN_DIR / "hooks"
    scripts = ["session_start.py", "user_prompt_submit.py", "git_watcher.py"]

    for script in scripts:
        script_path = hooks_dir / script
        if not script_path.exists():
            print(f"❌ Hook script missing: {script}")
            return False

    print("✅ Hook scripts exist")
    return True


def check_hook_scripts_executable():
    """Verify hook scripts are executable."""
    hooks_dir = PLUGIN_DIR / "hooks"
    scripts = ["session_start.py", "user_prompt_submit.py", "git_watcher.py"]

    all_executable = True
    for script in scripts:
        script_path = hooks_dir / script
        if not script_path.exists():
            print(f"❌ Hook script missing: {script}")
            all_executable = False
            continue

        if not os.access(script_path, os.X_OK):
            print(f"⚠️  Hook script not executable: {script}")
            print(f"   Run: chmod +x {script_path}")
            all_executable = False

    if all_executable:
        print("✅ Hook scripts are executable")
    return all_executable


def main():
    """Run all verification checks."""
    print("🔍 Verifying fabrik_bar installation...\n")

    checks = [
        check_plugin_json_consistency,
        check_settings_json,
        check_hooks_json,
        check_hook_scripts,
        check_hook_scripts_executable,
    ]

    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            sys.stderr.write(f"[ERROR] Check {check.__name__} crashed: {e}\n")
            results.append(False)

    print(f"\n{'='*50}")
    if all(results):
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
