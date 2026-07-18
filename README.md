# Hell Claude

Hell Claude is a public archive for coding-agent failures that users decide are worth preserving. Its client plugin notices explicit frustration or `/hell`, prepares a small redacted report, and asks for confirmation before opening a GitHub Issue. A GitHub Action validates accepted Issues, archives them as structured YAML, and rebuilds the tables below.

These are user-submitted incidents, not controlled experiments. The statistics are not a benchmark and must not be read as model failure rates.

## Installation

The first release provides direct installation for Codex and Claude Code. The report schema can still describe all nine supported Agent families.

- [Install for Codex](docs/install/codex.md)
- [Install for Claude Code](docs/install/claude-code.md)

Both packages contain a `UserPromptSubmit` Hook and the same `hell-report` Skill. Review and trust the Hook before enabling it: installed plugins can execute local commands with your user permissions.

## Verification

After installation, start a new client session and enter `/hell`. The Agent should offer to build a Hell report draft. It must show the complete title and body and wait for the exact confirmation “Submit this Hell report” before any network action.

## Usage

Automatic detection uses a small English and Chinese phrase list and a five-minute cooldown. `/hell` always bypasses the cooldown. The Skill looks backward through at most 20 user messages—never 20 full turns—and selects only evidence needed to explain the failure.

The preferred submission path is an already authenticated GitHub CLI session. Run `gh auth login` yourself if needed. When `gh` is unavailable or logged out, the Skill opens a prefilled browser form and leaves the final GitHub Submit click to you.

## Privacy

Nothing is submitted merely because the Hook matched. The draft is redacted locally and requires explicit confirmation. The server then performs a second, fail-closed scan before writing a record. Read [PRIVACY.md](PRIVACY.md) before sending private or work-related material.

## Supported Agents

The schema accepts `claude-code`, `codex`, `opencode`, `forgecode`, `kimi-code`, `trae`, `openclaw`, `hermes`, and `pi`. Direct plugin installation currently targets Codex and Claude Code; the other names are classification targets, not installable adapters in this release.

## Archive statistics

<!-- HELL-STATS:START -->
> These counts describe archived user submissions, not controlled model failure rates.

**Archived reports:** 0

**Last generated:** 2026-07-18T00:00:00Z

### Agents

| Name | Reports |
| --- | ---: |
| No archived reports | 0 |

### Models

| Name | Reports |
| --- | ---: |
| No archived reports | 0 |

### Failure categories

| Name | Reports |
| --- | ---: |
| No archived reports | 0 |

### Recent reports

| Issue | Agent | Model | Failures | Submitted |
| --- | --- | --- | --- | --- |
| No archived reports | | | | |
<!-- HELL-STATS:END -->

## Contributing

Reports arrive through the [Hell report Issue Form](https://github.com/AndrewWayne/hell-claude/issues/new?template=hell-report.yml). Code and taxonomy changes are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Never place real credentials, private source, or personal data in a fixture.

## Roadmap

- Improve GitHub presentation with richer, automatically refreshed views.
- Add carefully tested adapters for more Agent clients.
- Expand aliases and categories without changing historical records.
- Evaluate duplicate clustering beyond the MVP's exact-match hint.

## License

Code and documentation are available under the [MIT License](LICENSE). Submitted reports remain public GitHub content supplied by their authors.
