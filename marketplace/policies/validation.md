# Validation Policy

This marketplace accepts Codex plugins that can be installed from a repo-backed
marketplace source. Every listed plugin must pass automated validation before it
can be distributed.

## Required checks

- The Codex marketplace file exists at `.agents/plugins/marketplace.json`.
- Each marketplace entry has a unique kebab-case name.
- Each entry uses `source.source: local` and a `./`-prefixed `source.path`
  inside the repository root.
- Each plugin has `.codex-plugin/plugin.json`.
- Plugin manifest `name` matches the marketplace entry.
- Plugin manifest `version` is semantic version compatible.
- Plugin manifest declares a `skills` directory.
- At least one bundled `SKILL.md` exists.
- Every bundled `SKILL.md` has frontmatter `name` and `description`.
- Optional `mcpServers` paths point to real files.
- A public listing exists at `marketplace/listings/<plugin>.json`.
- Listing metadata declares verification, pricing, transactions, governance,
  legal, distribution, and developer contact fields.
- A lightweight secret scan finds no obvious credentials.
- Transaction ledger hash chaining is valid if a local ledger is present.

## Manual review

Manual review is required when a plugin:

- Requests external-service credentials.
- Uses MCP servers with network access.
- Can spend money or submit real-world orders.
- Writes to user data or third-party systems.
- Bundles code from an upstream project with unclear redistribution rights.
- Claims a paid entitlement or premium runtime.

## Risk tiers

- `low`: local file transformation or read-only helper workflow.
- `medium`: external service auth, networked MCP, or workspace data access.
- `high`: real-world spending, irreversible user actions, regulated data, or
  broad write permissions.
- `critical`: direct credential handling, financial transfer, privileged system
  access, or actions with legal or safety impact.

High and critical risk listings must require explicit user confirmation in their
skill instructions and listing governance metadata.

## Validation commands

```bash
python3 scripts/validate_marketplace.py
python3 scripts/build_public_index.py --marketplace-source ZhangXingyu123/codex-skill-store
```

Use `--strict` in CI when warnings should fail the build.
