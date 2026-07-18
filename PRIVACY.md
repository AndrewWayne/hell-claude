# Privacy

Hell Claude is designed around review and consent, but every submitted GitHub Issue is public. Do not submit material that you are not allowed to publish.

## What the client sees

The Hook reads the current submitted prompt, its packaged phrase list, local cooldown/configuration state, and a runtime model identifier supplied by the client. Codex supplies the current model with each prompt. Claude Code only supplies it at session start, so the Hook keeps a per-session copy in the plugin data directory; it may be stale after a mid-session model switch. The Hook accepts only a restricted-format identifier of at most 128 characters using letters, numbers, `.`, `_`, `:`, `/`, `+`, and `-`; it otherwise records `unknown`. This format check prevents arbitrary text from entering the report but does not verify that the model exists. The Hook does not read repository files or contact a network service. An automatic match is a soft signal: it does not run the Skill. It asks the Agent to judge whether a major mistake occurred and, only when warranted, ask whether the user wants a draft while continuing the active task.

An unambiguous yes authorizes a local draft only. It does not authorize submission. `/hell` skips the soft assessment and authorizes local drafting immediately, but it also does not authorize submission.

The Skill may inspect a candidate window ending at the trigger and extending backward through at most 20 user messages. “20 user messages” is not 20 turns: intervening Agent replies and tool events may be considered, but only the smallest relevant excerpts should enter the draft.

## What leaves your machine

Nothing leaves through this plugin until the complete Issue title and body, including the captured runtime model identifier or `unknown`, are shown, the Agent asks whether to submit it now, and you give an explicit confirmation through a direct affirmative response to that question. No fixed phrase is required. Silence, ambiguity, cancellation, editing the draft, or changing the subject does not authorize submission. If the payload changes, the Agent must show it and ask again. If you confirm, the approved title and body go to GitHub through your existing authenticated `gh` session, or through a browser form that you submit yourself. The plugin does not ask for, read, or store a GitHub token.

Before preview, the Skill removes credentials, private keys, email addresses, home paths, private remotes, `.env` content, full files, unselected diffs, and hidden platform instructions. A server-side scan blocks archival when named sensitive-data detectors match. Automated scanning reduces risk; it cannot guarantee that every private fact will be found.

## Public archive and deletion

Accepted Issues are copied into `records/` and summarized in README and Agent indexes. To request deletion, edit or close the Issue and contact the repository maintainers in a new Issue that links only to the report number. Maintainers can remove the current Issue content and archive file.

Git history and GitHub caches may retain earlier versions after normal deletion. A complete purge can require a coordinated Git history rewrite and may still not remove third-party forks, clones, notifications, or search caches. For exposed credentials, revoke or rotate them immediately; deletion is not a substitute.
