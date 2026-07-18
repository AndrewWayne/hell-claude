# Contributing

Contributions should keep collection small, consent explicit, and archival deterministic.

## Ground rules

- Use fictional conversations, identities, paths, repositories, and credentials in tests and examples.
- Never commit real tokens, private source, customer data, or copied private transcripts.
- Run `python3 -m unittest discover -s tests -v` and `git diff --check` before opening a pull request.
- Keep the Issue headings and parser contract synchronized.

## Common changes

- Agent aliases belong in `config/agents.yml`; preserve the nine canonical IDs.
- Trigger phrases belong in `plugins/hell-claude/hooks/phrases.json`; avoid broad words that fire during ordinary coding discussion.
- Task and failure categories belong in their versioned files under `config/`.
- Platform adapters must keep the Bash and PowerShell trigger decisions identical. Add shared fixtures for every behavior change.
- Statistics are generated from archived records only. Do not parse free-form Issues directly into README content.

Changes to privacy boundaries, confirmation, schema fields, or archive paths need contract tests first. New records should be submitted as Issues rather than hand-authored YAML.

## License

By contributing code or documentation, you agree that your contribution is provided under the repository's MIT License. A public report is user-submitted content and should contain only material its author has permission to publish.
