# Hell Claude MVP Eval

This file defines the completion gate for the MVP. A green unit test suite alone does not prove completion. The final audit must satisfy every mandatory criterion below with current repository or runtime evidence.

## Scoring

- Mandatory criteria use pass/fail scoring.
- MVP completion requires 100% of mandatory criteria.
- A skipped, unrun, flaky, or indirectly inferred criterion counts as failed.
- Advisory criteria do not block completion, but the final report must list any advisory failure.
- Tests must use fictional conversations and credentials.

## Mandatory criteria

| ID | Requirement | Passing evidence | Failure condition |
| --- | --- | --- | --- |
| E01 | Codex and Claude Code package metadata | Both manifests validate, share name/version, and point to the same plugin root | Missing manifest, invalid manifest, mismatched identity |
| E02 | Cross-platform Hook contract | POSIX and PowerShell adapters consume the same stdin fixtures and return the same trigger decision | Adapter missing, blocking exit, divergent output |
| E03 | Trigger behavior | `/hell`, default English/Chinese phrases, and custom phrases trigger; ordinary and malformed input fail open | False negative for required trigger or output for ordinary input |
| E04 | Cooldown behavior | Repeated automatic trigger is suppressed within the configured interval; `/hell` bypasses cooldown | Explicit trigger suppressed or cooldown ignored |
| E05 | Hook privacy boundary | Hook reads only submitted Hook JSON, phrase configuration, and cooldown state; it performs no network call | Hook reads worktree content, transcript, token, or remote endpoint |
| E06 | Skill discovery and schema | `SKILL.md` has valid frontmatter and names all nine canonical Agents and the fixed report headings | Invalid frontmatter or missing Agent/schema field |
| E07 | Twenty-user-message semantics | Skill says count only `role=user` messages, says this is not 20 turns, and includes intervening Agent/tool events only as candidates | “20 messages” or “20 turns” ambiguity remains |
| E08 | Context minimization | Skill selects goal, expected behavior, actual behavior, effects, and correction; it rejects full-session dumping | Skill instructs the Agent to upload the entire candidate window |
| E09 | Client redaction | Skill covers tokens, keys, email, home paths, private remotes, `.env`, full files, and unselected diffs | Any required detector or exclusion is absent |
| E10 | Confirmation gate | Tests prove cancel and ambiguous answers cannot reach submission; only explicit confirmation can invoke `gh` or browser fallback | Any submission path runs before confirmation |
| E11 | Submission authentication | Skill prefers authenticated `gh`, falls back to a prefilled browser form, and never requests or stores a token | Plugin handles a GitHub token or lacks fallback |
| E12 | Issue Form contract | Form labels render the exact headings consumed by the parser and expose all nine Agents | Parser/form heading mismatch or missing Agent |
| E13 | Format validation | Parser rejects missing, duplicate, oversized, and unsupported-schema reports | Invalid report reaches `records/` |
| E14 | Server safety scan | Named detectors catch fictional GitHub/API tokens, private keys, email, home paths, private remotes, and `.env` assignments without echoing matches | Sensitive value appears in result/comment |
| E15 | Normalization | Agent, model, task, and failure fields normalize through versioned configuration; unknown Agent becomes `other` with `raw_name` | Alias splits a canonical bucket or unknown data is lost |
| E16 | Stable archival | Valid Issue N creates one deterministic `records/YYYY/issue-N.yaml` with source, timestamps, evidence, and privacy status | Non-deterministic record or unstable path |
| E17 | Edit and retry idempotency | Reprocessing unchanged content creates no diff; editing Issue N updates only its stable record | Duplicate file or unrelated record changes |
| E18 | Duplicate hint | Exact normalized duplicate adds `possible-duplicate` without blocking archival | Duplicate is rejected or fuzzy matching creates unsupported claims |
| E19 | Workflow security | Workflow handles opened/edited/reopened Issues, serializes writes, requests only contents/issues write, and never executes Issue text | Overbroad permissions, unsafe interpolation, or race-prone writes |
| E20 | Failure states | `invalid-report` and `needs-redaction` write no record and replies list only field/detector names | Fail-open archival or sensitive echo |
| E21 | Dynamic statistics | Generator produces totals, update time, Agent/model/failure rankings, recent records, and nine Agent indexes from records | Missing metric/index or direct parsing of free-form Issues |
| E22 | README ownership | Generator changes only the marked stats region; a second run with identical inputs is byte-identical | Manual README content changes or output drifts |
| E23 | README content | README includes purpose, limitations, install, verification, use, privacy, nine Agents, contribution, and roadmap | Required public guidance missing |
| E24 | Install coverage | Codex and Claude Code docs cover macOS/Linux/Windows install, trust, `/hell` verification, update, and uninstall | A supported platform/client lacks a tested path |
| E25 | Privacy and contribution policy | Policies explain consent, deletion, Git-history caveat, fixture rules, and contribution license | User cannot learn what leaves the machine or how to remove it |
| E26 | Full regression suite | `python3 -m unittest discover -s tests -v` exits 0 with no failures or errors | Any test fails or errors |
| E27 | Repository hygiene | `git diff --check`, JSON/YAML parsing, plugin validation, and secret-fixture scan pass | Syntax, whitespace, placeholder, or real-secret finding |
| E28 | End-to-end dry run | A fictional Issue event produces a record, README update, Agent index, and archived result; a sensitive event produces no record | Pipeline components pass only in isolation |

## Advisory criteria

| ID | Requirement | Evidence |
| --- | --- | --- |
| A01 | Native PowerShell execution | Windows CI or local `pwsh` runs the PowerShell fixture suite |
| A02 | Live client smoke tests | Current Codex and Claude Code load the plugin and show its Hook/Skill |
| A03 | Live GitHub smoke test | A disposable Issue completes the workflow in the target repository |

## Final audit procedure

1. Run the full regression suite.
2. Run the acceptance contract tests.
3. Validate both plugin manifests and `SKILL.md` with their official validators.
4. Parse every JSON and YAML file.
5. Run the end-to-end dry run in a temporary directory.
6. Inspect workflow permissions and generated diff paths.
7. Search for placeholders, private paths, credentials, and untracked files.
8. Record E01 through E28 as pass or fail with command output or file links.

The implementation is complete only when E01 through E28 pass.
