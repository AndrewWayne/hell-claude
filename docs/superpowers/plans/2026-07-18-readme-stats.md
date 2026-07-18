# README and Statistics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a useful project README with installation guidance and regenerate repository statistics after every archived Issue.

**Architecture:** `scripts/update_readme.py` reads only validated YAML records, computes deterministic aggregates, replaces one marked README region, and generates Agent index pages. The archive workflow calls it in the same serialized commit so records and displayed counts stay synchronized.

**Tech Stack:** Python 3.11+, PyYAML, Markdown, `unittest` snapshot tests, GitHub Actions.

## Global Constraints

- README contains project introduction, installation, usage, privacy, supported Agents, contribution guidance, roadmap, and statistics.
- Action-generated text is confined to `HELL-STATS:START` and `HELL-STATS:END`.
- Counts describe submitted archived cases, not controlled failure rates.
- Generated output is deterministic and idempotent.
- MVP shows totals, last update, Agent/model/failure rankings, recent records, and per-Agent indexes.
- GitHub Pages remains a second-phase read-only consumer of the same records.

---

## File Map

- `README.md`: manual content plus generated region.
- `scripts/update_readme.py`: record loading, aggregation, Markdown rendering, marker replacement, index generation.
- `tests/test_update_readme.py`: aggregation and snapshot tests.
- `tests/fixtures/stats/records/*.yaml`: fictional records.
- `tests/fixtures/stats/expected.md`: expected generated region.
- `docs/agents/*.md`: generated Agent indexes.
- `CONTRIBUTING.md`: contribution rules.
- `PRIVACY.md`: collection, redaction, and deletion policy.
- `.github/workflows/archive-issue.yml`: invoke stats generation and commit outputs.

### Task 1: Record Loader and Aggregates

**Files:**
- Create: `scripts/update_readme.py`
- Create: `tests/test_update_readme.py`
- Create: `tests/fixtures/stats/records/issue-1.yaml`
- Create: `tests/fixtures/stats/records/issue-2.yaml`
- Create: `tests/fixtures/stats/records/issue-3.yaml`

**Interfaces:**
- Produces: `load_records(root: Path) -> list[dict]`.
- Produces: `aggregate(records: list[dict]) -> dict[str, Counter]` with keys `agents`, `models`, `failures`.
- Invalid record files raise `ValueError` with the path and do not produce partial output.

- [ ] **Step 1: Add fictional record fixtures**

Create three schema-version-1 records: two Codex cases and one Claude Code case. Use models `gpt-example` and `claude-example`, and overlap one failure category so ordering and counts can be asserted. Do not copy real conversations.

- [ ] **Step 2: Write failing aggregate tests**

```python
import unittest
from pathlib import Path
from scripts.update_readme import aggregate, load_records

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/stats/records"

class StatsTests(unittest.TestCase):
    def test_aggregate_counts_each_failure_category(self):
        stats = aggregate(load_records(FIXTURES))
        self.assertEqual(stats["agents"]["codex"], 2)
        self.assertEqual(stats["agents"]["claude-code"], 1)
        self.assertEqual(stats["models"]["gpt-example"], 2)
        self.assertEqual(stats["failures"]["incorrect-code"], 2)
```

- [ ] **Step 3: Verify red state**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: FAIL because `scripts.update_readme` does not exist.

- [ ] **Step 4: Implement loader and aggregates**

```python
from collections import Counter
from pathlib import Path
import yaml

def load_records(root: Path) -> list[dict]:
    records = []
    for path in sorted(root.rglob("issue-*.yaml")):
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
            if record["schema_version"] != 1 or record["status"] != "archived":
                raise ValueError("unsupported record")
        except Exception as exc:
            raise ValueError(f"invalid record {path}: {exc}") from exc
        records.append(record)
    return records

def aggregate(records: list[dict]) -> dict[str, Counter]:
    result = {"agents": Counter(), "models": Counter(), "failures": Counter()}
    for record in records:
        result["agents"][record["agent"]["framework"]] += 1
        result["models"][record["agent"].get("model") or "unknown"] += 1
        result["failures"].update(record["failure"]["categories"])
    return result
```

- [ ] **Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: aggregate tests PASS.

```bash
git add scripts/update_readme.py tests/test_update_readme.py tests/fixtures/stats
git commit -m "feat: aggregate archived report statistics"
```

### Task 2: Deterministic Markdown Renderer

**Files:**
- Modify: `scripts/update_readme.py`
- Modify: `tests/test_update_readme.py`
- Create: `tests/fixtures/stats/expected.md`

**Interfaces:**
- Produces: `render_stats(records: list[dict], generated_at: str) -> str`.
- Sorting: count descending, canonical key ascending for ties.
- Recent records: five newest by `submitted_at`, then Issue number descending.

- [ ] **Step 1: Write failing snapshot and tie-order tests**

Call `render_stats(records, "2026-07-18T12:00:00Z")` and compare the complete string to `expected.md`. Assert that tied names appear alphabetically.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: FAIL with missing `render_stats`.

- [ ] **Step 3: Implement rendering helpers**

```python
def ranked_rows(counter):
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))

def table(title, counter):
    lines = [f"### {title}", "", "| Name | Reports |", "| --- | ---: |"]
    lines.extend(f"| {name} | {count} |" for name, count in ranked_rows(counter))
    if not counter:
        lines.append("| No archived reports | 0 |")
    return "\n".join(lines)
```

`render_stats` must include:

```markdown
> These counts describe archived user submissions, not controlled model failure rates.

**Archived reports:** 3

**Last generated:** 2026-07-18T12:00:00Z

### Agents
...
### Models
...
### Failure categories
...
### Recent reports
...
```

Link recent records to their GitHub Issue URLs from `source_issue` and repository slug passed through configuration, not from untrusted Issue text.

- [ ] **Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: snapshot and ordering tests PASS.

```bash
git add scripts/update_readme.py tests/test_update_readme.py tests/fixtures/stats/expected.md
git commit -m "feat: render report statistics"
```

### Task 3: Safe README Marker Replacement

**Files:**
- Modify: `scripts/update_readme.py`
- Modify: `tests/test_update_readme.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `replace_generated_region(document: str, generated: str) -> str`.
- Requires exactly one start marker and one end marker in the correct order.

- [ ] **Step 1: Write marker safety tests**

Assert that:

- text before and after the markers remains byte-for-byte unchanged;
- a second identical run produces the same bytes;
- missing, duplicated, or reversed markers raise `ValueError`;
- an empty record set produces a valid zero-count region.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: FAIL with missing `replace_generated_region`.

- [ ] **Step 3: Implement strict replacement**

```python
START = "<!-- HELL-STATS:START -->"
END = "<!-- HELL-STATS:END -->"

def replace_generated_region(document: str, generated: str) -> str:
    if document.count(START) != 1 or document.count(END) != 1:
        raise ValueError("README must contain exactly one marker pair")
    before, rest = document.split(START, 1)
    current, after = rest.split(END, 1)
    if document.index(START) > document.index(END):
        raise ValueError("README markers are reversed")
    return f"{before}{START}\n{generated.rstrip()}\n{END}{after}"
```

- [ ] **Step 4: Add the initial README generated region**

Keep the current project title, add a short scope statement, and add one empty marker pair. Do not add the full manual documentation until Task 5.

- [ ] **Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: all marker tests PASS.

```bash
git add scripts/update_readme.py tests/test_update_readme.py README.md
git commit -m "feat: update README statistics safely"
```

### Task 4: Per-Agent Indexes and Command Interface

**Files:**
- Modify: `scripts/update_readme.py`
- Modify: `tests/test_update_readme.py`
- Create: `docs/agents/.gitkeep`

**Interfaces:**
- Produces: `render_agent_index(agent_id: str, records: list[dict]) -> str`.
- CLI: `python scripts/update_readme.py --records records --readme README.md --agents-dir docs/agents --repository OWNER/REPO --generated-at ISO8601`.

- [ ] **Step 1: Write failing index tests**

Assert that all nine canonical Agent pages exist after a run, even when an Agent has zero records. A page with records lists Issue, model, failure categories, and submission date. A second run changes no bytes.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_update_readme -v`

Expected: FAIL with missing index function or CLI.

- [ ] **Step 3: Implement indexes and CLI**

Use `argparse`. Write files only when content differs. Remove no unknown files from `docs/agents`. Generate only these names:

```text
claude-code.md
codex.md
opencode.md
forgecode.md
kimi-code.md
trae.md
openclaw.md
hermes.md
pi.md
```

- [ ] **Step 4: Run command twice and commit**

Run:

```bash
python scripts/update_readme.py --records tests/fixtures/stats/records --readme README.md --agents-dir /tmp/hell-agent-index --repository owner/repo --generated-at 2026-07-18T12:00:00Z
python scripts/update_readme.py --records tests/fixtures/stats/records --readme README.md --agents-dir /tmp/hell-agent-index --repository owner/repo --generated-at 2026-07-18T12:00:00Z
python3 -m unittest tests.test_update_readme -v
```

Expected: both commands exit 0 and all tests PASS.

```bash
git add scripts/update_readme.py tests/test_update_readme.py docs/agents/.gitkeep
git commit -m "feat: generate Agent report indexes"
```

### Task 5: Complete README, Privacy, and Contribution Docs

**Files:**
- Modify: `README.md`
- Create: `PRIVACY.md`
- Create: `CONTRIBUTING.md`
- Modify: `docs/install/codex.md`
- Modify: `docs/install/claude-code.md`

**Interfaces:**
- Consumes: installation docs and marker region.
- Produces: the public project landing page and policy documents.

- [ ] **Step 1: Write README manual sections**

Use this order:

1. Project purpose and warning that counts are not benchmark failure rates.
2. Flow: detect, select, redact, preview, confirm, Issue, archive.
3. Codex and Claude Code quick install links plus `gh auth login` recommendation.
4. Automatic trigger and `/hell` usage.
5. Privacy summary, 20-user-message definition, and link to `PRIVACY.md`.
6. Supported nine-Agent table and note that direct installation covers two clients.
7. Manual Issue submission.
8. Generated statistics marker region.
9. Contribution link and roadmap, including read-only GitHub Pages in phase two.

- [ ] **Step 2: Write privacy policy**

State what the plugin selects, what it excludes, that confirmation is required, what server scanning does, how `needs-redaction` works, how to request deletion, and that removing Git history requires maintainer action. State that the plugin never collects GitHub tokens.

- [ ] **Step 3: Write contribution rules**

Explain how to add aliases, phrases, failure categories, platform adapters, and fictional tests. Require contributors to avoid real private sessions in fixtures. State that code, documentation, and submitted records are contributed under the repository's existing MIT License unless a file states another license; contributors must have permission to submit every excerpt they include.

- [ ] **Step 4: Verify manual content and marker integrity**

Run:

```bash
rg -n "Codex|Claude Code|/hell|gh auth login|20|PRIVACY|CONTRIBUTING|GitHub Pages" README.md
python3 -m unittest tests.test_update_readme -v
```

Expected: every required topic appears and all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md PRIVACY.md CONTRIBUTING.md docs/install
git commit -m "docs: complete project landing page"
```

### Task 6: Integrate Statistics into Archival Workflow

**Files:**
- Modify: `.github/workflows/archive-issue.yml`
- Modify: `tests/test_archive_issue.py`
- Modify: `tests/test_update_readme.py`

**Interfaces:**
- Consumes: the archived record written by `archive_issue.py`.
- Produces: one commit containing the record, README update, and Agent indexes.

- [ ] **Step 1: Write a workflow integration test**

Assert that an archived-and-changed workflow run invokes `scripts/update_readme.py` before `git add` and stages only:

```text
records/
README.md
docs/agents/
```

Assert that invalid and redaction states do not invoke the generator or commit.

- [ ] **Step 2: Verify red state**

Run: `python3 -m unittest tests.test_archive_issue tests.test_update_readme -v`

Expected: FAIL because the workflow does not invoke `update_readme.py`.

- [ ] **Step 3: Update the workflow**

After a changed record is written, pass `$GITHUB_REPOSITORY` and the current UTC timestamp to `update_readme.py`. Stage the three allowed paths, commit once, rebase, and push inside the existing serialized workflow.

- [ ] **Step 4: Run all repository tests**

Run:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Expected: all tests PASS and `git diff --check` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/archive-issue.yml tests/test_archive_issue.py tests/test_update_readme.py
git commit -m "feat: refresh statistics after archival"
```
