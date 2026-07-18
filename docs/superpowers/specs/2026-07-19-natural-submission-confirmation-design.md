# Natural Submission Confirmation Design

**Date:** 2026-07-19
**Status:** Approved design

## Goal

Remove the fixed “Submit this Hell report” passphrase without removing the final submission decision. After the user authorizes draft generation, the Agent shows the complete GitHub Issue payload and asks whether to submit it now. A direct, unambiguous affirmative answer to that question authorizes submission.

## Authorization flow

Drafting and submission remain separate decisions:

1. The user authorizes generation of a local draft.
2. The Agent collects the smallest relevant context, redacts sensitive material, and builds the Issue title and body.
3. The Agent shows the complete title and body.
4. The Agent asks a direct question such as “Submit this report now?”
5. A direct affirmative response in context, including “yes,” “可以,” or “提交吧,” authorizes submission. No fixed phrase is required.

Authorization is bound to the immediately preceding submission question and the displayed payload. Silence, a topic change, an ambiguous response, a request to edit the draft, or approval unrelated to that question does not authorize submission. Cancellation performs no network action.

If the payload changes after confirmation, the Agent must show the changed payload and ask again before submitting it.

## Submission paths

After confirmation, the existing submission behavior remains unchanged:

- Prefer `gh issue create` when GitHub CLI authentication is available.
- Otherwise open the prefilled browser fallback, where the user performs GitHub’s final submission action.
- Never request, inspect, or store a GitHub token.

## Components

The behavior must be consistent across:

- `hell-report/SKILL.md`;
- POSIX and PowerShell Hook instructions;
- README, privacy documentation, and client installation guides;
- Skill, Hook, documentation, and acceptance contract tests.

Historical specifications and audit reports remain historical records and are not rewritten.

## Verification

Contract tests must prove that:

- the complete payload appears before the submission question;
- direct affirmative answers to that question authorize submission without a passphrase;
- ambiguous replies, cancellation, editing requests, silence, and topic changes do not authorize submission;
- a changed payload requires a new preview and confirmation;
- every `gh` or browser path remains after the confirmation gate;
- documentation no longer instructs users to type “Submit this Hell report.”

The Codex `/hell` slash-command compatibility issue is outside this change.
