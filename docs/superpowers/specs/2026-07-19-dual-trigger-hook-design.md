# Dual-Trigger Hook Design

Date: 2026-07-19

Status: approved for autonomous implementation

## Objective

Broaden automatic complaint detection without making every phrase match interrupt the user's work or immediately start a report. Keep `/hell` as an explicit command, and separate permission to draft from permission to submit.

## Trigger levels

The Hook has two outputs:

1. **Hard trigger:** a prompt containing `/hell` instructs the Agent to invoke `hell-report` immediately and build a local draft. `/hell` continues to bypass cooldown.
2. **Soft trigger:** a prompt matching the packaged or user-defined phrase list asks the Agent to assess whether its behavior involved a major mistake. A phrase match is evidence of dissatisfaction, not proof that a report is warranted.

The default phrase list adds these exact case-insensitive substring rules:

`WTF`, `silly`, `stupid`, `are you crazy`, `what're you doing`, `ruin it`, `go die`, `他妈`, `傻逼`, `煞笔`, `脑残`, `去死`, and `操`.

The user supplied 13 new phrases. Existing phrases remain unchanged. Duplicate normalized entries are forbidden.

## Soft-trigger behavior

The injected instruction tells the Agent to:

1. Continue addressing the user's current instruction; complaint handling must not become a separate blocking workflow.
2. Judge whether its preceding behavior contains a major mistake with a concrete effect, rather than treating the matched word alone as proof.
3. If no major mistake occurred, continue the task without mentioning Hell Claude.
4. If a major mistake likely occurred, briefly ask whether the user wants a Hell report draft while continuing any work that does not depend on that answer.
5. Treat yes as authorization to generate a local draft only.
6. Invoke `hell-report` after draft authorization, produce the redacted draft, and show the complete title and body.
7. Require a separate, explicit submission confirmation before any GitHub or browser action.

An ambiguous response does not authorize drafting or submission. A refusal ends the report path without stopping the current task.

## Skill behavior

The Skill supports two entry paths:

- `/hell` or an explicit request to report authorizes drafting immediately.
- A soft trigger invokes the Skill only after the user authorizes drafting.

Drafting should accompany correction of the user's active task. The Agent prioritizes preventing further damage and completing safe corrective work. It may wait for user input only when the underlying task itself requires that input; Hell Claude alone must not stall the task.

The existing collection window, minimization, redaction, 50,000-character limit, fixed schema, authenticated `gh` preference, browser fallback, and submission confirmation remain unchanged.

## Platform and failure behavior

Bash and PowerShell adapters must emit semantically identical hard- and soft-trigger instructions for the same fixture. Hook failures remain fail-open and silent. The Hook continues to read only stdin, packaged phrases, user phrase configuration, and cooldown state, and performs no network operation.

## Testing

Tests must first fail against the current implementation, then prove:

- all 13 new phrases trigger the soft path;
- automatic matches never emit the hard-trigger instruction;
- `/hell` always emits the hard-trigger instruction and bypasses cooldown;
- custom phrases use the soft path;
- the soft instruction contains major-mistake judgment, non-blocking continuation, draft permission, and separate submission permission;
- the Skill preserves two distinct authorization gates and non-stalling behavior;
- existing privacy, cooldown, cross-platform, archive, and documentation tests remain green.
