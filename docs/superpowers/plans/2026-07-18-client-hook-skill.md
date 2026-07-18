# Client Hook and Skill Implementation Plan

> **Implementation status (2026-07-18): complete.** This file preserves the original TDD sequence. The shipped package lives at `plugins/hell-claude/`; the two repository marketplaces live at `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`. Current source and tests are authoritative where an early example below differs from the finished implementation.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one Hell Claude plugin whose Hook detects complaint prompts on macOS, Linux, and Windows and whose Skill prepares a user-approved GitHub Issue.

**Architecture:** A `UserPromptSubmit` command Hook reads JSON from stdin and emits context only when `/hell` or a configured phrase matches. POSIX shell and PowerShell adapters implement one contract and read one phrase file; `plugins/hell-claude/skills/hell-report/SKILL.md` owns selection, redaction, preview, and submission.

**Tech Stack:** Codex/Claude Code plugin manifests, JSON, POSIX shell with `jq`, Windows PowerShell 5.1+, Markdown Skill instructions, Python `unittest`, GitHub Actions.

## Global Constraints

- Direct installation is supported for Codex and Claude Code only.
- The schema accepts `claude-code`, `codex`, `opencode`, `forgecode`, `kimi-code`, `trae`, `openclaw`, `hermes`, and `pi`.
- The Hook never blocks a prompt and never uploads data.
- Automatic detection and `/hell` only generate a local draft.
- The scan window counts at most 20 `role=user` messages, not 20 turns.
- Agent replies and tool events inside that window are candidates; the payload character cap controls upload size.
- The user must inspect the complete payload and explicitly confirm submission.
- The outgoing Issue body is capped at 50,000 characters after redaction and selection.
- The plugin never reads, stores, or transmits GitHub credentials.

---

## File Map

- `plugins/hell-claude/.codex-plugin/plugin.json` and `plugins/hell-claude/.claude-plugin/plugin.json`: package metadata.
- `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`: direct-install catalogs.
- `plugins/hell-claude/hooks/hooks.json`: `UserPromptSubmit` configuration.
- `plugins/hell-claude/hooks/phrases.json`: shared phrases and cooldown.
- `plugins/hell-claude/hooks/detect-complaint.sh` and `plugins/hell-claude/hooks/detect-complaint.ps1`: platform adapters.
- `plugins/hell-claude/skills/hell-report/SKILL.md`: report workflow.
- `tests/test_plugin_metadata.py` and `tests/test_hook_contract.py`: contract tests.
- `.github/workflows/client-plugin-tests.yml`: Ubuntu/Windows tests.

### Task 1: Plugin Metadata and Rules

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `.claude-plugin/plugin.json`
- Create: `hooks/phrases.json`
- Create: `tests/test_plugin_metadata.py`

**Interfaces:**
- Produces: plugin name `hell-claude` and `{version: number, cooldown_seconds: number, phrases: string[]}`.

- [ ] **Step 1: Write the failing metadata tests**

```python
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PluginMetadataTests(unittest.TestCase):
    def test_manifests_share_name_and_version(self):
        paths = [
            ROOT / ".codex-plugin/plugin.json",
            ROOT / ".claude-plugin/plugin.json",
        ]
        values = [json.loads(path.read_text()) for path in paths]
        self.assertEqual([v["name"] for v in values], ["hell-claude", "hell-claude"])
        self.assertEqual(values[0]["version"], values[1]["version"])

    def test_rules_are_unique_and_include_explicit_trigger(self):
        rules = json.loads((ROOT / "hooks/phrases.json").read_text())
        phrases = [value.casefold().strip() for value in rules["phrases"]]
        self.assertEqual(rules["version"], 1)
        self.assertGreaterEqual(rules["cooldown_seconds"], 0)
        self.assertEqual(len(phrases), len(set(phrases)))
        self.assertIn("/hell", phrases)
```

- [ ] **Step 2: Verify the red state**

Run: `python3 -m unittest tests.test_plugin_metadata -v`

Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Add manifests**

Use this Codex manifest:

```json
{
  "name": "hell-claude",
  "description": "Capture a user-approved report when a coding agent performs badly.",
  "version": "0.1.0",
  "hooks": "./hooks/hooks.json"
}
```

Use the same name, description, and version in `.claude-plugin/plugin.json`; Claude Code discovers `hooks/hooks.json` from the plugin root.

- [ ] **Step 4: Add rules**

```json
{
  "version": 1,
  "cooldown_seconds": 300,
  "phrases": [
    "/hell",
    "fuck",
    "you are so silly",
    "this is not what i asked",
    "你在干什么",
    "这不是我要的",
    "太离谱了"
  ]
}
```

- [ ] **Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_plugin_metadata -v`

Expected: 2 tests PASS.

```bash
git add .codex-plugin .claude-plugin hooks/phrases.json tests/test_plugin_metadata.py
git commit -m "feat: add plugin metadata and complaint rules"
```

### Task 2: POSIX Hook

**Files:**
- Create: `hooks/detect-complaint.sh`
- Create: `tests/fixtures/hook/explicit.json`
- Create: `tests/fixtures/hook/negative.json`
- Create: `tests/fixtures/hook/ordinary.json`
- Create: `tests/fixtures/hook/invalid.json`
- Create: `tests/test_hook_contract.py`

**Interfaces:**
- Consumes: `hooks/phrases.json` and Hook JSON on stdin.
- Produces: exit 0 always; empty stdout when unmatched/invalid; structured `additionalContext` when matched.
- State: `PLUGIN_DATA/last-trigger-<session_id>` for cooldown.

- [ ] **Step 1: Add fixtures**

```json
{"session_id":"explicit","hook_event_name":"UserPromptSubmit","prompt":"/hell report this"}
```

Add equivalent fixtures for `This is not what I asked.`, `Please run tests.`, and literal invalid input `not-json`.

- [ ] **Step 2: Write the failing contract test**

```python
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/hook"

def run_posix(name, data_dir):
    env = os.environ.copy()
    env.update(CLAUDE_PLUGIN_ROOT=str(ROOT), PLUGIN_DATA=data_dir)
    return subprocess.run(
        ["bash", str(ROOT / "hooks/detect-complaint.sh")],
        input=(FIXTURES / name).read_text(),
        text=True, capture_output=True, env=env, check=False,
    )

class HookContractTests(unittest.TestCase):
    def test_match_and_fail_open(self):
        with tempfile.TemporaryDirectory() as data:
            matched = run_posix("explicit.json", data)
            self.assertEqual(matched.returncode, 0)
            self.assertIn("hell-report", json.loads(matched.stdout)
                          ["hookSpecificOutput"]["additionalContext"])
        with tempfile.TemporaryDirectory() as data:
            for name in ("ordinary.json", "invalid.json"):
                result = run_posix(name, data)
                self.assertEqual((result.returncode, result.stdout), (0, ""))
```

- [ ] **Step 3: Verify the red state**

Run: `python3 -m unittest tests.test_hook_contract -v`

Expected: ERROR because `detect-complaint.sh` is missing.

- [ ] **Step 4: Implement the adapter**

```bash
#!/usr/bin/env bash
set -u
root="${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
rules="$root/hooks/phrases.json"
input="$(cat)"
command -v jq >/dev/null 2>&1 || exit 0
prompt="$(printf '%s' "$input" | jq -er '.prompt | strings' 2>/dev/null)" || exit 0
session="$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null)"
explicit="$(printf '%s' "$prompt" | grep -Fqi -- '/hell' && printf yes)"
if [ "$explicit" = yes ]; then
  matched=yes
else
  config="${PLUGIN_DATA:-}/config.json"
  auto_detect=true
  phrases="$(jq -r '.phrases[] | select(. != "/hell")' "$rules")"
  if [ -n "${PLUGIN_DATA:-}" ] && [ -f "$config" ]; then
    auto_detect="$(jq -r '.auto_detect // true' "$config" 2>/dev/null)" || exit 0
    phrases="$phrases
$(jq -r '.additional_phrases[]?' "$config" 2>/dev/null)"
  fi
  [ "$auto_detect" = true ] || exit 0
  matched="$(printf '%s\n' "$phrases" | while IFS= read -r phrase; do
    [ -n "$phrase" ] && printf '%s' "$prompt" | grep -Fqi -- "$phrase" && { printf yes; break; }
  done)"
fi
[ "$matched" = yes ] || exit 0

cooldown="$(jq -r '.cooldown_seconds' "$rules")"
if [ "$explicit" != yes ] && [ -n "${PLUGIN_DATA:-}" ] && [ "$cooldown" -gt 0 ] 2>/dev/null; then
  mkdir -p "$PLUGIN_DATA" 2>/dev/null || true
  marker="$PLUGIN_DATA/last-trigger-$(printf '%s' "$session" | tr -cd 'A-Za-z0-9._-')"
  now="$(date +%s)"
  if [ -f "$marker" ]; then
    last="$(cat "$marker" 2>/dev/null || printf 0)"
    [ $((now - last)) -lt "$cooldown" ] 2>/dev/null && exit 0
  fi
  printf '%s' "$now" > "$marker" 2>/dev/null || true
fi

jq -nc '{hookSpecificOutput:{
  hookEventName:"UserPromptSubmit",
  additionalContext:"Invoke the hell-report skill. Build a local draft and require explicit confirmation before submission."
}}'
exit 0
```

- [ ] **Step 5: Add cooldown coverage**

Invoke the negative fixture twice with the same temporary data directory. Assert that the first invocation emits JSON and the second emits nothing. Invoke the explicit fixture twice with another shared data directory and assert that both invocations emit JSON, proving that `/hell` bypasses cooldown. Add one test with `PLUGIN_DATA/config.json` containing `{"auto_detect": false}` and verify that a negative phrase stays silent while `/hell` still triggers. Add another with `{"additional_phrases": ["what a disaster"]}` and verify that the custom phrase triggers.

- [ ] **Step 6: Verify and commit**

Run:

```bash
chmod +x hooks/detect-complaint.sh
python3 -m unittest tests.test_hook_contract -v
```

Expected: all POSIX tests PASS.

```bash
git add hooks/detect-complaint.sh tests/fixtures/hook tests/test_hook_contract.py
git commit -m "feat: add POSIX complaint hook"
```

### Task 3: PowerShell Hook and Hook Configuration

**Files:**
- Create: `hooks/detect-complaint.ps1`
- Create: `hooks/hooks.json`
- Modify: `tests/test_hook_contract.py`
- Create: `.github/workflows/client-plugin-tests.yml`

**Interfaces:**
- Consumes: Task 2 fixtures.
- Produces: the same output keys and fail-open behavior as the POSIX adapter.

- [ ] **Step 1: Add a PowerShell runner**

Use `shutil.which("pwsh") or shutil.which("powershell")`. Skip only when both are absent. Run `-NoProfile -File hooks/detect-complaint.ps1` and reuse every Task 2 assertion.

- [ ] **Step 2: Verify red or skipped state**

Run: `python3 -m unittest tests.test_hook_contract -v`

Expected: PowerShell contract FAILS because the script is absent, or SKIPS if PowerShell is unavailable.

- [ ] **Step 3: Implement the PowerShell adapter**

```powershell
$ErrorActionPreference = "SilentlyContinue"
$root = if ($env:CLAUDE_PLUGIN_ROOT) { $env:CLAUDE_PLUGIN_ROOT } else { Split-Path -Parent $PSScriptRoot }
$raw = [Console]::In.ReadToEnd()
try { $inputObject = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not ($inputObject.prompt -is [string])) { exit 0 }
try { $rules = Get-Content "$root/hooks/phrases.json" -Raw | ConvertFrom-Json } catch { exit 0 }
$explicit = $inputObject.prompt.IndexOf('/hell', [StringComparison]::OrdinalIgnoreCase) -ge 0
$matched = $explicit
if (-not $explicit) {
    $autoDetect = $true
    $phrases = @($rules.phrases | Where-Object { $_ -ne '/hell' })
    $configPath = if ($env:PLUGIN_DATA) { Join-Path $env:PLUGIN_DATA 'config.json' } else { $null }
    if ($configPath -and (Test-Path $configPath)) {
        try { $config = Get-Content $configPath -Raw | ConvertFrom-Json } catch { exit 0 }
        if ($null -ne $config.auto_detect) { $autoDetect = [bool]$config.auto_detect }
        $phrases += @($config.additional_phrases)
    }
    if (-not $autoDetect) { exit 0 }
    foreach ($phrase in $phrases) {
        if ($phrase -and $inputObject.prompt.IndexOf($phrase, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $matched = $true; break
        }
    }
}
if (-not $matched) { exit 0 }
if (-not $explicit -and $env:PLUGIN_DATA -and [int]$rules.cooldown_seconds -gt 0) {
    New-Item -ItemType Directory -Force -Path $env:PLUGIN_DATA | Out-Null
    $safe = [regex]::Replace([string]$inputObject.session_id, '[^A-Za-z0-9._-]', '')
    $marker = Join-Path $env:PLUGIN_DATA "last-trigger-$safe"
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if (Test-Path $marker) {
        $last = [long](Get-Content $marker -Raw)
        if (($now - $last) -lt [int]$rules.cooldown_seconds) { exit 0 }
    }
    Set-Content -NoNewline -Path $marker -Value $now
}
@{hookSpecificOutput=@{
  hookEventName="UserPromptSubmit"
  additionalContext="Invoke the hell-report skill. Build a local draft and require explicit confirmation before submission."
}} | ConvertTo-Json -Compress -Depth 4
exit 0
```

- [ ] **Step 4: Add `hooks/hooks.json`**

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "bash \"$CLAUDE_PLUGIN_ROOT/hooks/detect-complaint.sh\"",
        "commandWindows": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$env:CLAUDE_PLUGIN_ROOT\\hooks\\detect-complaint.ps1\"",
        "timeout": 5,
        "statusMessage": "Checking for a Hell report trigger"
      }]
    }]
  }
}
```

Validate `commandWindows` in Codex native Windows. Validate Claude Code native Windows separately; its documented Git Bash shell can execute the POSIX command if it ignores the Codex-specific override.

- [ ] **Step 5: Add Ubuntu/Windows CI and verify**

The workflow installs `jq` on Ubuntu and runs:

```bash
python -m unittest tests.test_plugin_metadata tests.test_hook_contract -v
```

Expected: all tests PASS on both jobs.

- [ ] **Step 6: Commit**

```bash
git add hooks/hooks.json hooks/detect-complaint.ps1 tests/test_hook_contract.py .github/workflows/client-plugin-tests.yml
git commit -m "feat: add cross-platform hook adapter"
```

### Task 4: Hell Report Skill

**Files:**
- Create: `skills/hell-report/SKILL.md`
- Create: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: Hook context naming `hell-report`.
- Produces: a fixed-heading Issue draft and an explicit confirmation gate.

- [ ] **Step 1: Write the failing Skill contract**

Read `SKILL.md` and assert that it contains `role=user`, `20`, `not 20 turns`, `explicit confirmation`, `gh issue create`, `needs-redaction`, all nine canonical Agent IDs, and frontmatter `name: hell-report`.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_skill_contract -v`

Expected: FAIL because `SKILL.md` is absent.

- [ ] **Step 3: Write the Skill workflow**

The Skill must define these gates:

1. Identify the Agent with a canonical ID or `other` plus `raw_name`.
2. Count backward at most 20 messages whose role is exactly `user`. Include intervening Agent/tool events as candidates and state that the window is not 20 turns.
3. Select only the goal, expected behavior, actual behavior, relevant effects, and user correction.
4. Replace credentials, email, home paths, private remotes, `.env` data, full files, and unselected diffs with named redaction markers. Reduce the completed body to at most 50,000 characters by dropping the oldest and least relevant evidence first.
5. Build a `schema_version: 1` body using the server parser's fixed headings.
6. Show the complete outgoing title and body; accept edit, cancel, or explicit submit.
7. After explicit submit, use `gh auth status` and `gh issue create --repo <configured repository> --body-file <temporary file>`. Delete the temporary file.
8. If `gh` is absent or unauthenticated, URL-encode locally and open the new-Issue page. Explain that nothing is submitted until the user clicks GitHub's Submit button.
9. Never request or inspect a token. Stop on cancellation, ambiguous confirmation, or unresolved redaction.

Use these exact body headings:

```markdown
## Schema Version
1
## Agent
## Raw Agent Name
## Model
## Task Category
## User Goal
## Expected Behavior
## Actual Behavior
## Failure Categories
## Impact
## Evidence
## Client Redaction
```

- [ ] **Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_skill_contract -v`

Expected: all tests PASS.

```bash
git add skills/hell-report/SKILL.md tests/test_skill_contract.py
git commit -m "feat: add Hell report skill"
```

### Task 5: Client Integration and Installation Docs

**Files:**
- Create: `docs/install/codex.md`
- Create: `docs/install/claude-code.md`
- Create: `docs/install/windows.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: completed plugin.
- Produces: install, trust, verification, update, and uninstall instructions.

- [ ] **Step 1: Document prerequisites**

State: macOS/Linux detection uses `bash` and `jq`; Windows uses PowerShell 5.1+; `gh` is recommended and browser submission is the fallback.

- [ ] **Step 2: Document installation and trust**

Codex instructions cover enablement, Hook trust review through `/hooks`, and `/hell` verification. Claude Code instructions cover `claude --plugin-dir .` for development, marketplace installation, `/hooks` inspection, and `/hell` verification. Windows instructions name the adapter used by each client.

- [ ] **Step 3: Document update and uninstall**

Explain how to update and remove `hell-claude` and state that uninstalling does not delete Issues already submitted.

- [ ] **Step 4: Run final client verification**

Run:

```bash
rg -n "/hell|gh auth login|uninstall|privacy|20" docs/install README.md
python3 -m unittest tests.test_plugin_metadata tests.test_hook_contract tests.test_skill_contract -v
```

Expected: documentation search finds every term and all available tests PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/install README.md
git commit -m "docs: add client installation guides"
```
