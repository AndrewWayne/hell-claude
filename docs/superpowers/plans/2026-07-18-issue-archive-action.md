# Issue Archive Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert every format-valid, safety-clean Hell report Issue into one stable YAML record without manual review.

**Architecture:** A Python command reads the GitHub event JSON, parses fixed Markdown headings, validates and normalizes the report, scans sensitive content, and writes `records/YYYY/issue-N.yaml`. A workflow commits the record and updates Issue labels; invalid or sensitive reports fail closed.

**Tech Stack:** GitHub Issue Forms, Python 3.11+, PyYAML, `unittest`, GitHub Actions.

## Global Constraints

- Reports passing format and safety checks archive automatically.
- `invalid-report` and `needs-redaction` never write records.
- Replies never repeat detected sensitive values.
- Re-running an unchanged Issue is idempotent.
- Editing an Issue updates the same record path.
- Duplicate detection adds `possible-duplicate` but does not block archival.
- Issue text is data only; no Issue field is interpolated into a shell command.
- Workflow permissions are limited to `contents: write` and `issues: write`.

---

## File Map

- `.github/ISSUE_TEMPLATE/hell-report.yml`: manual structured submission form.
- `config/agents.yml`: canonical Agent IDs, display names, and aliases.
- `config/model-aliases.yml`: optional raw-model to canonical-model mappings.
- `config/task-categories.yml`: accepted task categories.
- `config/failure-categories.yml`: accepted failure categories.
- `requirements-actions.txt`: PyYAML runtime dependency.
- `scripts/archive_issue.py`: parser, validation, scanning, normalization, record writer.
- `tests/fixtures/issues/*.json`: GitHub event fixtures.
- `tests/test_archive_issue.py`: unit and command tests.
- `.github/workflows/archive-issue.yml`: event orchestration, commit, labels, comments.

### Task 1: Issue Form, Aliases, and Body Parser

**Files:**
- Create: `.github/ISSUE_TEMPLATE/hell-report.yml`
- Create: `config/agents.yml`
- Create: `config/model-aliases.yml`
- Create: `config/task-categories.yml`
- Create: `config/failure-categories.yml`
- Create: `requirements-actions.txt`
- Create: `scripts/archive_issue.py`
- Create: `tests/test_archive_issue.py`

**Interfaces:**
- Produces: `parse_sections(body: str) -> dict[str, str]`.
- Required section keys: `Schema Version`, `Agent`, `Raw Agent Name`, `Model`, `Task Category`, `User Goal`, `Expected Behavior`, `Actual Behavior`, `Failure Categories`, `Impact`, `Evidence`, `Client Redaction`.

- [ ] **Step 1: Write parser tests**

```python
import unittest
from scripts.archive_issue import parse_sections

BODY = """## Schema Version
1
## Agent
Codex
## Raw Agent Name
Codex CLI
## Model
unknown
## Task Category
debugging
## User Goal
Fix a failing test.
## Expected Behavior
Change the faulty condition.
## Actual Behavior
Deleted the test.
## Failure Categories
destructive-action
## Impact
file-changes
## Evidence
The test file was removed.
## Client Redaction
completed
"""

class ParseSectionsTests(unittest.TestCase):
    def test_parses_schema_and_fixed_headings(self):
        parsed = parse_sections(BODY)
        self.assertEqual(parsed["Schema Version"], "1")
        self.assertEqual(parsed["Agent"], "Codex")
        self.assertEqual(parsed["Evidence"], "The test file was removed.")

    def test_rejects_duplicate_headings(self):
        with self.assertRaisesRegex(ValueError, "duplicate heading"):
            parse_sections(BODY + "\n## Agent\nClaude Code\n")
```

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue.ParseSectionsTests -v`

Expected: FAIL because `scripts.archive_issue` does not exist.

- [ ] **Step 3: Implement the parser**

```python
import re

HEADING = re.compile(r"^## ([A-Za-z ]+)\s*$")

def parse_sections(body: str) -> dict[str, str]:
    lines = body.replace("\r\n", "\n").splitlines()
    result = {}
    current = None
    values: list[str] = []
    for line in lines[1:]:
        match = HEADING.match(line)
        if match:
            if current is not None:
                result[current] = "\n".join(values).strip()
            current = match.group(1)
            if current in result:
                raise ValueError(f"duplicate heading: {current}")
            values = []
        elif current is not None:
            values.append(line)
    if current is not None:
        result[current] = "\n".join(values).strip()
    return result
```

- [ ] **Step 4: Add configuration files**

`config/agents.yml` must contain all nine canonical IDs and their aliases. `config/model-aliases.yml` starts as an empty mapping and preserves unknown raw model values. `config/task-categories.yml` contains `coding`, `debugging`, `refactoring`, `explanation`, `tool-operation`, and `other`. `config/failure-categories.yml` contains the ten categories from the design. Set `requirements-actions.txt` to `PyYAML>=6,<7`.

- [ ] **Step 5: Add the Issue Form**

Use Issue Form inputs whose rendered Markdown headings match `SKILL.md` exactly. Add a required `Schema Version` input prefilled with `1`; GitHub submits input values but does not submit static Markdown elements. Make Agent a dropdown with nine values, make model optional, make goal/expected/actual/evidence required textareas, make failure categories checkboxes, and add a required privacy acknowledgment. Follow the [GitHub Issue Form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema).

- [ ] **Step 6: Verify and commit**

Run:

```bash
python3 -m pip install -r requirements-actions.txt
python3 -m unittest tests.test_archive_issue.ParseSectionsTests -v
python3 -c "import yaml; yaml.safe_load(open('config/agents.yml'))"
```

Expected: parser tests PASS and both YAML config files load.

```bash
git add .github/ISSUE_TEMPLATE config requirements-actions.txt scripts/archive_issue.py tests/test_archive_issue.py
git commit -m "feat: add structured Hell report parser"
```

### Task 2: Validation, Normalization, and Safety Scan

**Files:**
- Modify: `scripts/archive_issue.py`
- Modify: `tests/test_archive_issue.py`
- Create: `tests/fixtures/issues/valid.json`
- Create: `tests/fixtures/issues/invalid.json`
- Create: `tests/fixtures/issues/sensitive.json`

**Interfaces:**
- Produces: `normalize_agent(value: str, aliases: dict) -> tuple[str, str | None]`.
- Produces: `normalize_model(value: str, aliases: dict) -> tuple[str, str]` and preserves the raw value.
- Produces: `validate_report(sections: dict[str, str], allowed_failures: set[str], allowed_tasks: set[str]) -> list[str]`.
- Produces: `scan_sensitive(text: str) -> list[str]`; results contain detector names only, never matched values.

- [ ] **Step 1: Write failing validation tests**

```python
from scripts.archive_issue import normalize_agent, normalize_model, scan_sensitive

class ValidationTests(unittest.TestCase):
    def test_normalize_agent_alias(self):
        aliases = {"codex": ["codex cli", "openai codex"]}
        self.assertEqual(normalize_agent("Codex CLI", aliases), ("codex", "Codex CLI"))

    def test_unknown_agent_becomes_other(self):
        self.assertEqual(normalize_agent("New Agent", {}), ("other", "New Agent"))

    def test_unknown_model_preserves_raw_value(self):
        self.assertEqual(normalize_model("vendor/model-x", {}), ("vendor/model-x", "vendor/model-x"))

    def test_scan_reports_detector_names_only(self):
        text = "token ghp_" + "A" * 36 + " and me@example.com"
        findings = scan_sensitive(text)
        self.assertIn("github-token", findings)
        self.assertIn("email-address", findings)
        self.assertNotIn("ghp_", repr(findings))
```

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: FAIL with missing imported functions.

- [ ] **Step 3: Implement normalization and validation**

```python
REQUIRED = {
    "Schema Version", "Agent", "Model", "Task Category", "User Goal", "Expected Behavior",
    "Actual Behavior", "Failure Categories", "Impact", "Evidence",
    "Client Redaction",
}

def normalize_agent(value: str, aliases: dict[str, list[str]]) -> tuple[str, str | None]:
    raw = value.strip()
    folded = raw.casefold()
    for canonical, values in aliases.items():
        if folded == canonical.casefold() or folded in {v.casefold() for v in values}:
            return canonical, None if folded == canonical.casefold() else raw
    return "other", raw

def normalize_model(value: str, aliases: dict[str, str]) -> tuple[str, str]:
    raw = value.strip() or "unknown"
    return aliases.get(raw.casefold(), raw), raw

def validate_report(
    sections: dict[str, str],
    allowed_failures: set[str],
    allowed_tasks: set[str],
) -> list[str]:
    errors = []
    if sections.get("Schema Version") != "1":
        errors.append("unsupported schema_version")
    for key in sorted(REQUIRED):
        if not sections.get(key, "").strip():
            errors.append(f"missing field: {key}")
    supplied = {v.strip() for v in sections.get("Failure Categories", "").splitlines() if v.strip()}
    unknown = sorted(supplied - allowed_failures)
    if unknown:
        errors.append("unknown failure categories: " + ", ".join(unknown))
    if sections.get("Task Category") not in allowed_tasks:
        errors.append("unknown task category")
    if sections.get("Client Redaction") != "completed":
        errors.append("client redaction is not completed")
    if len("\n".join(sections.values())) > 50_000:
        errors.append("report exceeds 50000 characters")
    return errors
```

- [ ] **Step 4: Implement named safety detectors**

Compile detectors for GitHub tokens, common API-key prefixes, PEM private keys, email addresses, absolute Unix home paths, Windows user-profile paths, `.env` assignments, and credential-bearing HTTPS remotes. `scan_sensitive` returns sorted unique detector names. It must not return snippets, offsets, or original values.

- [ ] **Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: parser, normalization, validation, and detector tests PASS.

```bash
git add scripts/archive_issue.py tests/test_archive_issue.py tests/fixtures/issues
git commit -m "feat: validate and scan Hell reports"
```

### Task 3: Stable Record Writer and Idempotency

**Files:**
- Modify: `scripts/archive_issue.py`
- Modify: `tests/test_archive_issue.py`
- Create: `tests/fixtures/records/issue-42.yaml`

**Interfaces:**
- Produces: `build_record(issue: dict, sections: dict, config: dict) -> dict`.
- Produces: `record_path(root: Path, issue: dict) -> Path`.
- Produces: `write_record(path: Path, record: dict) -> bool` where the boolean says whether content changed.

- [ ] **Step 1: Write the failing record test**

Create an Issue numbered 42 with `created_at = "2026-07-18T12:00:00Z"`. Assert:

```python
self.assertEqual(record_path(root, issue), root / "records/2026/issue-42.yaml")
self.assertEqual(record["id"], "github-issue-42")
self.assertEqual(record["source_issue"], 42)
self.assertEqual(record["agent"]["framework"], "codex")
self.assertEqual(record["privacy"]["server_scan"], "passed")
```

Call `write_record` twice and assert the first result is `True`, the second is `False`, and the bytes do not change.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: FAIL with missing record functions.

- [ ] **Step 3: Implement deterministic YAML writing**

`build_record` maps fixed headings into the schema from the design. Parse failure categories and impact as non-empty line lists. Use `yaml.safe_dump(record, sort_keys=False, allow_unicode=True)` and append one newline. Compare the serialized bytes before writing so unchanged Issues produce no diff.

- [ ] **Step 4: Add command behavior**

`main()` accepts:

```text
--event PATH
--repo-root PATH
--result PATH
```

It writes a result JSON with one of:

```json
{"status":"archived","record":"records/2026/issue-42.yaml","changed":true}
{"status":"invalid-report","errors":["missing field: Evidence"]}
{"status":"needs-redaction","findings":["github-token"]}
```

Return exit 0 for all three business states so the workflow can label the Issue. Return nonzero only for infrastructure faults such as unreadable event JSON or unwritable repository paths.

- [ ] **Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: every test PASS, including the idempotent second write.

```bash
git add scripts/archive_issue.py tests/test_archive_issue.py tests/fixtures/records
git commit -m "feat: archive reports as stable records"
```

### Task 4: Workflow, Labels, and Concurrent Commits

**Files:**
- Create: `.github/workflows/archive-issue.yml`
- Create: `.github/labels.yml`
- Modify: `tests/test_archive_issue.py`

**Interfaces:**
- Consumes: `archive_issue.py --result result.json`.
- Produces: a pushed record plus exactly one terminal label: `archived`, `invalid-report`, or `needs-redaction`; `possible-duplicate` may coexist.

- [ ] **Step 1: Add a workflow contract test**

Parse the workflow as YAML and assert:

```python
self.assertEqual(workflow["permissions"]["contents"], "write")
self.assertEqual(workflow["permissions"]["issues"], "write")
self.assertIn("issues", workflow["on"])
self.assertTrue(workflow["concurrency"]["group"])
```

Also assert that the workflow never includes `pull_request_target` or `issue_comment` triggers.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: FAIL because the workflow is absent.

- [ ] **Step 3: Implement the workflow**

Trigger on Issue `opened`, `edited`, and `reopened`. Set a repository-wide archive concurrency group with `cancel-in-progress: false`. Steps:

1. Check out the default branch.
2. Set up Python 3.11 and install `requirements-actions.txt`.
3. Run `archive_issue.py` against `$GITHUB_EVENT_PATH`.
4. Read `result.json` with a short Python command and expose status/record/changed through `$GITHUB_OUTPUT`.
5. If archived and changed, configure the bot identity, add only the reported record path, commit, pull with rebase, and push with a bounded retry.
6. Use `gh issue edit` to remove stale terminal labels and add the current label.
7. Add a generic comment for invalid or redaction states. The redaction comment lists detector names only.

Pass the Issue number as a numeric argument to `gh`; do not build commands from title or body text.

- [ ] **Step 4: Define labels**

Add `archived`, `invalid-report`, `needs-redaction`, and `possible-duplicate` with distinct colors and short descriptions.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python3 -m unittest tests.test_archive_issue -v
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/archive-issue.yml'))"
```

Expected: all tests PASS and workflow YAML loads.

```bash
git add .github/workflows/archive-issue.yml .github/labels.yml tests/test_archive_issue.py
git commit -m "feat: automate Issue archival"
```

### Task 5: Duplicate Hint and Edit Synchronization

**Files:**
- Modify: `scripts/archive_issue.py`
- Modify: `.github/workflows/archive-issue.yml`
- Modify: `tests/test_archive_issue.py`

**Interfaces:**
- Produces: `find_possible_duplicate(record: dict, records_root: Path) -> int | None`.
- Adds `duplicate_issue` to result JSON without changing archival eligibility.

- [ ] **Step 1: Write duplicate and edit tests**

Create two records with the same normalized Agent, task category, failure categories, and normalized goal text. Assert that issue 43 reports issue 42 as a possible duplicate. Change issue 42's body, rerun, and assert that only `issue-42.yaml` changes.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: FAIL with missing duplicate function.

- [ ] **Step 3: Implement conservative matching**

Normalize whitespace and case in `task.goal`. Return a duplicate only when Agent, task category, the failure-category set, and normalized goal all match. Exclude the current issue number. Do not add fuzzy matching in MVP.

- [ ] **Step 4: Update workflow labels**

When `duplicate_issue` exists, add `possible-duplicate` and comment with only the existing Issue number. Remove the label when a later edit no longer matches.

- [ ] **Step 5: Run the complete archive suite and commit**

Run: `python3 -m unittest tests.test_archive_issue -v`

Expected: all parser, safety, record, workflow, duplicate, and edit tests PASS.

```bash
git add scripts/archive_issue.py .github/workflows/archive-issue.yml tests/test_archive_issue.py
git commit -m "feat: flag possible duplicate reports"
```
