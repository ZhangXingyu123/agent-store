# Contributing

Submit plugins through pull requests.

## Required files

```text
plugins/<plugin>/.codex-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
marketplace/listings/<plugin>.json
```

If the plugin uses MCP, include the MCP config inside the plugin folder and
reference it from `.codex-plugin/plugin.json`.

## Required validation

```bash
python3 scripts/validate_marketplace.py --strict
python3 scripts/build_public_index.py --marketplace-source owner/repo
```

## Review expectations

- Keep skill descriptions specific enough for Codex routing.
- Declare all files, external services, credentials, and write actions.
- Do not bundle upstream code unless redistribution rights are clear.
- Use explicit user confirmation for high-risk actions.
- Keep pricing visible in `marketplace/listings/<plugin>.json`.
- Do not commit secrets or production transaction ledgers.

## Versioning

Any behavior, permission, MCP, script, or skill instruction change must bump the
plugin version in `.codex-plugin/plugin.json`.
