# Distribution Policy

This marketplace is distributed as a Git-backed Codex plugin marketplace.

## Repository layout

```text
.agents/plugins/marketplace.json
plugins/<plugin-name>/.codex-plugin/plugin.json
plugins/<plugin-name>/skills/<skill-name>/SKILL.md
marketplace/listings/<plugin-name>.json
public/marketplace.json
public/index.html
```

Codex reads `.agents/plugins/marketplace.json`. The public website and JSON
catalog are generated from the same source plus listing metadata.

## User install flow

```bash
codex plugin marketplace add ZhangXingyu123/codex-skill-store
```

Then the user opens the Codex plugin directory, selects this marketplace source,
and installs the plugin.

## Versioning

- Plugin versions use semantic versioning.
- Marketplace listing changes that do not alter installed behavior can update
  listing metadata without bumping the plugin version.
- Any behavior, permission, MCP, script, or skill instruction change must bump
  the plugin version.
- Breaking permission changes require manual review and release notes.

## Release tracks

- `stable`: default public install track.
- `preview`: listed, but still collecting feedback.
- `blocked`: retained for audit history but unavailable for install.

## Delisting

A plugin can be delisted when:

- Validation fails.
- The maintainer is unreachable for a security issue.
- The plugin violates policy.
- Upstream redistribution rights are unclear.
- The listing misrepresents pricing, data access, or capabilities.

Delisted plugins should stay in the audit log with the reason and timestamp.
