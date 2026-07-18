# Dual-Trigger Hook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand complaint phrases and make automatic matches request Agent judgment and draft permission without stalling the user's active task, while keeping `/hell` immediate.

**Architecture:** The existing platform adapters continue to own deterministic phrase matching and cooldown. They emit one shared hard-trigger message for `/hell` and one shared soft-trigger message for automatic/custom matches; `SKILL.md` owns the two authorization gates and non-blocking task/report coordination.

**Tech Stack:** JSON, Bash with `jq`, Windows PowerShell 5.1+, Markdown Skill instructions, Python `unittest`.

## Global Constraints

- `/hell` immediately invokes `hell-report`, bypasses cooldown, and authorizes local drafting only.
- Automatic and custom phrase matches never invoke the Skill directly.
- The 12 requested phrases use the existing case-insensitive substring semantics.
- A soft match is not proof of a major mistake.
- Hell Claude alone must not stall the user's active task.
- Draft permission and submission permission are separate explicit gates.
- Hook failures remain silent and fail-open; Hook code performs no network access.
- Bash and PowerShell outputs remain semantically identical.

---

### Task 1: Phrase and Trigger Contract

**Files:**
- Modify: `tests/test_plugin_metadata.py`
- Modify: `tests/test_hook_contract.py`
- Modify: `tests/fixtures/hook/explicit.json`

**Interfaces:**
- Consumes: `run_hook(adapter, fixture, data_dir)`.
- Produces: constants `HARD_TRIGGER_TEXT` and `SOFT_TRIGGER_TEXT` used by all Hook assertions.

- [ ] **Step 1: Write failing phrase and output tests**

Add the exact requested list to the metadata assertion. Add a helper that writes a temporary JSON fixture with one prompt, then assert each requested phrase emits `SOFT_TRIGGER_TEXT` and does not emit `HARD_TRIGGER_TEXT`. Update `/hell`, cooldown, and custom-phrase assertions to require the appropriate output.

- [ ] **Step 2: Verify the red state**

Run: `python3 -m unittest tests.test_plugin_metadata tests.test_hook_contract -v`

Expected: FAIL because the new phrases are absent and automatic matches still emit the old immediate-Skill instruction.

- [ ] **Step 3: Commit the red tests only after implementation is green**

The tests and implementation are committed together in Task 3 so the repository does not intentionally retain a failing commit.

### Task 2: Skill Authorization Contract

**Files:**
- Modify: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `plugins/hell-claude/skills/hell-report/SKILL.md`.
- Produces: static behavioral checks for draft permission, separate submission permission, and non-stalling execution.

- [ ] **Step 1: Write failing Skill tests**

Assert the Skill contains these unambiguous concepts: `draft authorization`, `does not authorize submission`, `continue the user's active task`, `must not stall`, and a complete-payload submission gate after drafting. Assert the draft-authorization section appears before collection and submission.

- [ ] **Step 2: Verify the red state**

Run: `python3 -m unittest tests.test_skill_contract -v`

Expected: FAIL because the current Skill has one submission gate but no soft-trigger draft gate or non-stalling rule.

### Task 3: Minimal Hook and Skill Implementation

**Files:**
- Modify: `plugins/hell-claude/hooks/phrases.json`
- Modify: `plugins/hell-claude/hooks/detect-complaint.sh`
- Modify: `plugins/hell-claude/hooks/detect-complaint.ps1`
- Modify: `plugins/hell-claude/skills/hell-report/SKILL.md`
- Test: `tests/test_plugin_metadata.py`
- Test: `tests/test_hook_contract.py`
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Hard output: immediate local draft through `hell-report`, complete preview, separate explicit submission confirmation.
- Soft output: continue active task, assess concrete major mistake, ask for draft permission only when warranted, invoke Skill only after yes, and keep submission separately gated.

- [ ] **Step 1: Add the 12 phrases**

Append `WTF`, `silly`, `stupid`, `are you crazy`, `what're you doing`, `ruin it`, `go die`, `他妈`, `傻逼`, `煞笔`, `脑残`, and `去死` to `phrases.json`, preserving uniqueness after case-folding.

- [ ] **Step 2: Split adapter output by trigger type**

Define the same two message strings in Bash and PowerShell. Emit the hard string when `explicit` is true and the soft string otherwise. Do not alter matching, configuration, cooldown, or fail-open branches.

- [ ] **Step 3: Add Skill entry and coordination rules**

Add a `Draft authorization` section before collection. State that `/hell` and an explicit report request authorize drafting, while a soft-trigger path reaches the Skill only after an unambiguous yes. State that draft permission does not authorize submission. Add a `Work alongside the active task` section requiring safe correction/continuation and forbidding a Hell-only stall.

- [ ] **Step 4: Run focused tests**

Run: `python3 -m unittest tests.test_plugin_metadata tests.test_hook_contract tests.test_skill_contract -v`

Expected: all focused tests PASS.

- [ ] **Step 5: Commit**

```text
git add plugins/hell-claude tests/test_plugin_metadata.py tests/test_hook_contract.py tests/test_skill_contract.py
git commit -m "feat: add soft complaint trigger flow"
```

### Task 4: Public Behavior Documentation

**Files:**
- Modify: `README.md`
- Modify: `PRIVACY.md`
- Modify: `docs/install/codex.md`
- Modify: `docs/install/claude-code.md`
- Test: `tests/test_docs_contract.py`

**Interfaces:**
- Produces: public explanation of soft/hard triggers, two authorization gates, and non-stalling behavior.

- [ ] **Step 1: Write the failing documentation contract**

Require README and privacy text to distinguish soft assessment, local draft authorization, and separate submission confirmation. Require both client guides to state that `/hell` starts a local draft immediately.

- [ ] **Step 2: Verify red, update docs, and verify green**

Run: `python3 -m unittest tests.test_docs_contract -v`

Expected before documentation edits: FAIL. Expected after edits: PASS.

- [ ] **Step 3: Commit**

```text
git add README.md PRIVACY.md docs/install tests/test_docs_contract.py docs/superpowers/plans/2026-07-19-dual-trigger-hook.md
git commit -m "docs: explain dual-trigger authorization"
```

### Task 5: Acceptance Audit

**Files:**
- Create: `docs/evals/dual-trigger-audit.md`
- Modify: `docs/evals/mvp-audit.md`

**Interfaces:**
- Consumes: D01–D10 from `docs/evals/dual-trigger-acceptance.md`.
- Produces: a current pass/fail evidence table and advisory status.

- [ ] **Step 1: Run full verification**

Run the full unit suite, Codex plugin validator, Claude marketplace/plugin validators, Skill validator, Bash syntax, tracked JSON/YAML parsing, `git diff --check`, and a public-file credential/placeholder scan.

- [ ] **Step 2: Record D01–D10 evidence**

Write one row per criterion with direct test names, file paths, or command results. Do not mark native PowerShell or live-client checks as executed unless current evidence proves them.

- [ ] **Step 3: Commit the audit**

```text
git add docs/evals/dual-trigger-audit.md docs/evals/mvp-audit.md
git commit -m "test: audit dual-trigger acceptance"
```

- [ ] **Step 4: Verify the committed tree**

Run: `python3 -m unittest discover -s tests -v && git diff --check && git status --porcelain`

Expected: all tests PASS, both Git checks exit 0, and status prints nothing.
