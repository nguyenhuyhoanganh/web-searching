# Evaluations

Representative scenarios for the `web-research` skill, in the format from Anthropic's
[Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

There is no built-in runner. Each `*.json` file describes one scenario:

- `skills` — the skill(s) under test
- `query` — the user request to give the agent (with the skill available)
- `files` — input files the scenario needs (none here; all scenarios are web-based)
- `expected_behavior` — observable behaviors that indicate success

Use them as a manual checklist, or wire them into your own harness: run the `query` with the skill
loaded and confirm each `expected_behavior` occurred. Per the best practices, establish a baseline
(run the query *without* the skill) first, so you can see what the skill adds.

## Scenarios

- `01-verify-claim.json` — decompose + fact-check a claim to a TRUE/FALSE/OUTDATED verdict with a source.
- `02-latest-version.json` — look up current/time-sensitive info and cite the source URL + date.
- `03-read-and-summarize-url.json` — read a URL into clean Markdown and summarize it.
- `04-map-and-crawl-docs.json` — discover and gather a bounded section of a docs site.
- `05-first-run-setup.json` — Python detection, skill-dir probe, and ask-before-install behavior.
