---
name: hell-report
description: Use when a user expresses dissatisfaction with a coding agent, invokes /hell, or asks to report poor agent behavior.
---

# Hell Report

Build a local, minimal failure report. Do not send data until the user reviews the complete payload and gives explicit confirmation.

## Supported Agents

Use one canonical ID: `claude-code`, `codex`, `opencode`, `forgecode`, `kimi-code`, `trae`, `openclaw`, `hermes`, or `pi`. Use `other` for an unknown Agent and preserve its name under Raw Agent Name.

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

Show the complete Issue title and body. Offer three choices: edit, cancel, or submit.

Only an explicit confirmation such as “Submit this Hell report” authorizes submission. A vague or ambiguous reply, silence, topic change, approval of the wording, or approval of an earlier plan does not count as explicit confirmation. On cancel, discard the draft and perform no network action.

## Submit

Use the repository from `HELL_CLAUDE_REPOSITORY`; default to `AndrewWayne/hell-claude`.

After explicit confirmation:

1. Run `gh auth status`.
2. If authenticated, write the approved body to a temporary local file and run:

   ```bash
   gh issue create --repo OWNER/REPO --title "TITLE" --body-file "TEMP_FILE"
   ```

3. Delete the temporary file after success or failure.
4. Never read, request, store, print, or transmit a GitHub token.

If `gh` is missing, unauthenticated, or denied, URL-encode the approved title and body locally and open the repository's browser new-Issue form. Tell the user that opening the browser does not submit anything; GitHub receives the Issue only when the user clicks Submit.

If GitHub or the server later labels the report `needs-redaction`, tell the user to edit the flagged field without repeating the sensitive value.
