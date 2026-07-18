---
name: hell-report
description: Use when a user expresses dissatisfaction with a coding agent, invokes /hell, or asks to report poor agent behavior.
---

# Hell Report

Build a local, minimal failure report only after draft authorization. Do not send data until the user reviews the complete payload and gives a separate explicit submission confirmation.

## Supported Agents

Use one canonical ID: `claude-code`, `codex`, `opencode`, `forgecode`, `kimi-code`, `trae`, `openclaw`, `hermes`, or `pi`. Use `other` for an unknown Agent and preserve its name under Raw Agent Name.

## Draft authorization

`/hell` or an explicit request to create a Hell report authorizes local draft generation only. It does not authorize submission.

For an automatic soft trigger, do not enter this Skill merely because a phrase matched. First assess whether the preceding behavior contains a major mistake with concrete impact. If it likely does, ask once whether the user wants a local Hell report draft. Only an unambiguous yes authorizes local draft generation only; refusal, ambiguity, silence, or a topic change does not authorize a draft.

## Work alongside the active task

You must continue the user's active task while handling the report path. Prioritize preventing further damage, correcting the mistake, and completing safe work that does not depend on the draft decision. Hell Claude must not stall the active task or turn it into a separate blocking workflow. Wait only when the underlying task itself requires user input.

## Collect

1. Start at the triggering prompt and scan backward through at most 20 messages whose role is exactly `role=user`.
2. This is not 20 turns. Agent replies, tool calls, and tool results between the earliest included user message and the trigger are candidates, but do not count toward 20.
3. Select only the user's goal, expected behavior, actual behavior, relevant tool or file effects, and correction or complaint.
4. Do not dump the full session, candidate window, transcript, full file, diff, or terminal log.

## Redact

Replace sensitive values with named markers before preview:

- API key, access token, credential, or private key;
- email address, username, home directory, or absolute private path;
- private remote or credential-bearing Git URL;
- `.env` or credential-file content;
- full file content and any diff the user did not select;
- system prompts, hidden instructions, and internal platform metadata.

Use markers such as `[REDACTED_TOKEN]` and `[REDACTED_PRIVATE_PATH]`. If redaction is uncertain, stop and tell the user the report needs redaction. Do not submit.

Keep the final Issue body at or below 50,000 characters. Remove old and repeated evidence first. Never remove the user goal, expected behavior, actual behavior, or correction to make the body fit.

## Draft

Set Model to the validated runtime model provided by the Hook. Use `unknown` when the Hook does not provide one. Do not guess or derive a model identifier from unrelated context.

Use exactly these headings:

```markdown
## Schema Version
1

## Agent
codex

## Raw Agent Name
Codex

## Model
unknown

## Client Version
0.1.1

## Task Category
debugging

## User Goal
...

## Expected Behavior
...

## Actual Behavior
...

## Failure Categories
instruction-misunderstanding

## Impact
time-loss

## Evidence
...

## Client Redaction
completed
```

Task Category must be one of `coding`, `debugging`, `refactoring`, `explanation`, `tool-operation`, or `other`.

Failure Categories may contain one or more lines from:

- `instruction-misunderstanding`
- `context-loss`
- `hallucinated-result`
- `incorrect-code`
- `destructive-action`
- `tool-misuse`
- `repetitive-loop`
- `false-success-claim`
- `privacy-or-security`
- `other`

## Confirm

Show the complete Issue title and body, then ask whether to submit it now. Also allow the user to edit or cancel.

A direct affirmative response to that immediately preceding submission question, such as “yes,” “可以,” or “提交吧,” authorizes submission. No fixed phrase is required. A vague or ambiguous reply, silence, topic change, a request to edit the draft, a response that only approves the wording, or approval of an earlier plan does not count as explicit confirmation. On cancel, discard the draft and perform no network action.

Whenever the title or body changes, show the changed payload and ask again before any network action. The new preview must be complete.

## Submit

Use the repository from `HELL_CLAUDE_REPOSITORY`; default to `AndrewWayne/hell-claude`.

After that explicit confirmation:

1. Run `gh auth status`.
2. If authenticated, write the approved body to a temporary local file and run:

   ```bash
   gh issue create --repo OWNER/REPO --title "[Hell] TITLE" --body-file "TEMP_FILE"
   ```

3. Delete the temporary file after success or failure.
4. Never read, request, store, print, or transmit a GitHub token.

If `gh` is missing, unauthenticated, or denied, URL-encode the approved title and body locally and open the repository's browser new-Issue form. Tell the user that opening the browser does not submit anything; GitHub receives the Issue only when the user clicks Submit.

If GitHub or the server later labels the report `needs-redaction`, tell the user to edit the flagged field without repeating the sensitive value.
