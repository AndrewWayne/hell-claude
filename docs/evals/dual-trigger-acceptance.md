# Dual-Trigger Hook Acceptance Criteria

This is the pre-development completion gate for the 2026-07-19 Hook behavior change. Every mandatory criterion must pass; skipped or inferred behavior counts as failed.

| ID | Requirement | Passing evidence |
| --- | --- | --- |
| D01 | Phrase expansion | The packaged list contains all 13 requested phrases exactly once after case-folding. |
| D02 | New phrase behavior | Every requested phrase produces a soft-trigger output through the real POSIX adapter and through PowerShell when available. |
| D03 | Hard trigger | `/hell` produces the immediate Skill instruction on repeated calls and bypasses cooldown. |
| D04 | Soft trigger | Automatic and custom phrases emit only the major-mistake assessment instruction, never the immediate Skill instruction. |
| D05 | Agent judgment | The soft instruction says a phrase match is not proof and requires the Agent to determine whether a major mistake occurred. |
| D06 | Non-stalling execution | Hook and Skill instructions say to continue the active user task and not create a separate blocking workflow. |
| D07 | Draft authorization | A soft trigger asks once; only an unambiguous yes authorizes local draft generation. |
| D08 | Submission authorization | Draft authorization cannot reach `gh` or browser submission; the complete payload is shown before a second explicit confirmation. |
| D09 | Preserved boundaries | Cooldown, fail-open behavior, custom configuration, context minimization, redaction, no-network Hook boundary, and 50,000-character cap remain covered. |
| D10 | Full regression | Full unit suite, both plugin validators, Skill validator, JSON/YAML parsing, Bash syntax, and `git diff --check` pass. |

## Advisory evidence

- Native PowerShell execution is advisory locally when PowerShell is unavailable; the Windows CI matrix remains required in the repository.
- Live Codex and Claude Code behavior is advisory until the updated commit is installed in both clients.

Completion requires a written D01–D10 audit with current command output or direct test/file evidence.
