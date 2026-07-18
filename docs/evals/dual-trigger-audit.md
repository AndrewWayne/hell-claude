# Dual-Trigger Hook Acceptance Audit

Date: 2026-07-19

Version: 0.1.1

Result: **10/10 mandatory criteria passed.** Native PowerShell and live-client checks remain advisory and unverified on this machine.

## Verification summary

```text
python3 -m unittest discover -s tests -v
# Ran 45 tests ... OK

python3 .../plugin-creator/scripts/validate_plugin.py plugins/hell-claude
# Plugin validation passed

python3 .../skill-creator/scripts/quick_validate.py plugins/hell-claude/skills/hell-report
# Skill is valid!

claude plugin validate .
claude plugin validate plugins/hell-claude
# Validation passed for marketplace and plugin

bash -n plugins/hell-claude/hooks/detect-complaint.sh
git diff --check
# exit 0
```

All 11 tracked JSON files except the deliberately malformed fail-open fixture and all 10 tracked YAML files parsed successfully. Public-file placeholder and credential scans returned no findings.

## Mandatory criteria

| ID | Result | Evidence |
| --- | --- | --- |
| D01 | PASS | `test_phrase_rules_are_unique` verifies all 13 requested case-folded phrases and uniqueness. |
| D02 | PASS | `test_requested_phrases_use_the_soft_trigger` feeds every phrase through the real adapter contract. POSIX ran locally; the same test targets PowerShell in Windows CI. |
| D03 | PASS | `test_automatic_trigger_cools_down_but_explicit_trigger_does_not` verifies repeated `/hell` hard triggers. |
| D04 | PASS | Required, automatic, and custom-configuration tests distinguish hard and soft output and reject immediate Skill output for phrase matches. |
| D05 | PASS | `test_soft_trigger_encodes_judgment_and_two_authorization_gates` verifies that a match is not proof and major-mistake judgment is required. |
| D06 | PASS | Hook semantic test and `test_draft_permission_is_separate_and_does_not_stall_active_work` verify continuation and non-stalling rules. |
| D07 | PASS | Hook and Skill tests require an unambiguous yes for local draft generation only. |
| D08 | PASS | Skill gate-order tests require complete preview and a separate explicit submission confirmation before `gh` or browser paths. |
| D09 | PASS | Existing Hook, Skill, privacy, cooldown, configuration, minimization, redaction, and 50,000-character tests remain green. |
| D10 | PASS | Full suite, official validators, syntax parsing, Bash syntax, scans, and Git checks pass. |

## Advisory criteria

| Check | Result | Note |
| --- | --- | --- |
| Native PowerShell | UNVERIFIED LOCALLY | PowerShell is not installed; `windows-latest` remains in the client CI matrix. |
| Live Codex | UNVERIFIED | Version 0.1.1 was not installed into the user's live Codex configuration during this audit. |
| Live Claude Code | UNVERIFIED | Version 0.1.1 was not installed into the user's live Claude Code configuration during this audit. |
