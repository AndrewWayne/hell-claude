# Hell Claude MVP Acceptance Audit

Date: 2026-07-19

Result: **28/28 mandatory criteria passed.** The three advisory live-environment checks remain unverified and do not block the MVP. The version 0.1.1 dual-trigger change is additionally covered by [the D01–D10 audit](dual-trigger-audit.md).

## Verification commands

```text
python3 -m unittest discover -s tests -v
# Ran 44 tests ... OK

python3 .../plugin-creator/scripts/validate_plugin.py plugins/hell-claude
# Plugin validation passed

python3 .../skill-creator/scripts/quick_validate.py plugins/hell-claude/skills/hell-report
# Skill is valid!

claude plugin validate .
claude plugin validate plugins/hell-claude
# Validation passed for the marketplace and plugin

bash -n plugins/hell-claude/hooks/detect-complaint.sh
git diff --check
# exit 0
```

All tracked JSON files except the deliberately malformed fail-open fixture were decoded with Python's JSON parser. All tracked YAML files were decoded with PyYAML. The malformed fixture was exercised by the Hook contract tests. A scan of public docs, plugin files, configuration, records, and workflows found no placeholder credentials, credential-bearing remotes, or maintainer home paths.

## Mandatory criteria

| ID | Result | Current evidence |
| --- | --- | --- |
| E01 | PASS | Both nested manifests and both repository marketplaces pass `test_plugin_metadata`; official plugin and marketplace validators pass. |
| E02 | PASS | Shared Hook fixtures run through the POSIX adapter locally and both adapters in the Ubuntu/Windows CI matrix. |
| E03 | PASS | `test_required_prompts_trigger_and_other_input_fails_open` and configuration coverage pass. |
| E04 | PASS | `test_automatic_trigger_cools_down_but_explicit_trigger_does_not` passes. |
| E05 | PASS | `test_hook_has_no_network_or_transcript_access` passes; scripts read stdin, packaged rules, and plugin data only. |
| E06 | PASS | Official Skill validator and schema/Agent contract tests pass. |
| E07 | PASS | Skill and tests explicitly distinguish 20 `role=user` messages from 20 turns. |
| E08 | PASS | Skill limits selection to the minimum evidence chain and forbids full-session dumping. |
| E09 | PASS | Skill contract covers credentials, identity/path data, private remotes, `.env`, full files, and unselected diffs. |
| E10 | PASS | Confirmation-order contract proves the explicit gate precedes every submission path and that cancel/ambiguous replies authorize no network action. |
| E11 | PASS | Skill uses authenticated `gh`, browser fallback, and expressly forbids token handling. |
| E12 | PASS | `test_issue_form_matches_parser_contract` verifies exact headings and all nine Agents. |
| E13 | PASS | Parser tests reject missing, duplicate, oversized, unknown-category, and unsupported-schema input. |
| E14 | PASS | Named sensitive-data detector test covers all required fictional patterns and verifies values are not returned. |
| E15 | PASS | Normalization tests and versioned configuration cover Agent, model, task, failure, alias, and unknown-Agent behavior. |
| E16 | PASS | Record tests verify deterministic `records/YYYY/issue-N.yaml` content and required provenance/privacy fields. |
| E17 | PASS | Record tests verify byte-idempotent retry and stable-path edit behavior. |
| E18 | PASS | Exact normalized duplicate test returns a non-blocking Issue hint. |
| E19 | PASS | Workflow contract verifies events, concurrency, minimal permissions, controlled paths, and no Issue-body shell interpolation. |
| E20 | PASS | Process tests prove invalid and sensitive reports write no record and expose only field/detector names. |
| E21 | PASS | Statistics tests cover total, timestamp, three rankings, recent reports, and nine Agent indexes. |
| E22 | PASS | Marker replacement and fixed-input second-run tests are byte-identical. |
| E23 | PASS | README documentation contract passes. |
| E24 | PASS | Codex and Claude Code guides cover macOS, Linux, Windows, Hook trust, `/hell`, update, and uninstall. |
| E25 | PASS | Privacy and contribution contracts cover consent, deletion, Git history, fictional fixtures, and MIT contribution terms. |
| E26 | PASS | Full suite: 44 tests, 0 failures, 0 errors. |
| E27 | PASS | Diff, JSON/YAML, plugin, Skill, marketplace, shell syntax, placeholder, and credential scans pass. |
| E28 | PASS | End-to-end test creates a fictional record, README update, Agent index, and archived result; sensitive input creates no record. |

## Advisory criteria

| ID | Result | Note |
| --- | --- | --- |
| A01 | UNVERIFIED LOCALLY | PowerShell is not installed on this machine. The checked-in CI matrix runs the same contract on `windows-latest`. |
| A02 | UNVERIFIED | No install was made into the user's live Codex or Claude Code configuration during this audit. |
| A03 | UNVERIFIED | No disposable public Issue was created; the local end-to-end dry run passed. |
