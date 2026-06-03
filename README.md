# Agent Store

Agent Store is a public marketplace skeleton for reusable agent capabilities.
It is designed for tools in the same family as coding agents, desktop agents,
MCP-enabled clients, and skill-based assistants.

The goal is **submit once, adapt across platforms**: developers publish one
portable capability package, then add platform adapters only where a host tool
requires a specific package or install format.

## Public Path

[https://github.com/ZhangXingyu123/agent-store](https://github.com/ZhangXingyu123/agent-store)

## Platform Adapters

Current supported adapter:

```bash
codex plugin marketplace add ZhangXingyu123/agent-store
```

Planned adapter targets:

- Open Agent Skills as the shared authoring format.
- Claude Code-compatible packaging.
- MCP-capable agent clients.
- Other agent clients that can load skills, tools, connectors, scripts, or MCP
  server definitions.

Compatibility metadata lives in:

```text
marketplace/platforms.json
```

## Marketplace Layout

```text
.agents/plugins/marketplace.json          # Host-readable marketplace catalog
plugins/<plugin>/.codex-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
marketplace/platforms.json                # Platform compatibility model
marketplace/listings/<plugin>.json        # Public listing, pricing, governance
marketplace/policies/                     # Validation, distribution, trade, governance
marketplace/transactions/                 # Private ledger location, ignored by git
scripts/validate_marketplace.py           # Validation gate
scripts/build_public_index.py             # Generates public storefront artifacts
scripts/record_transaction.py             # Purchase/refund/grant/revoke ledger events
public/index.html                         # Generated public storefront
public/marketplace.json                   # Generated public catalog
```

The `.codex-plugin` folder is a platform adapter format, not the product
identity. Agent Store's public listing model is platform-neutral and can carry
additional adapters as they are added.

## Current Listings

- `invoice-expense`: free local invoice table workflow.
- `zebra-image`: installable demo filter with a paid premium-runtime SKU model.
- `feishu-connector`: Feishu/Lark MCP connector wrapper.
- `meituan-paotui`: high-risk local-services adapter with confirmation gates.

## Validation

```bash
python3 scripts/validate_marketplace.py
python3 scripts/validate_marketplace.py --strict
```

The validator checks:

- Marketplace entry shape.
- Platform install command metadata.
- Plugin manifest shape.
- Skill frontmatter.
- Local source-path boundaries.
- Listing metadata.
- Pricing and SKU metadata.
- Governance and risk metadata.
- Optional MCP config paths.
- Lightweight secret patterns.
- Transaction ledger hash chain when a local ledger exists.

## Build Public Distribution Artifacts

```bash
python3 scripts/build_public_index.py --marketplace-source ZhangXingyu123/agent-store
```

This writes:

```text
public/marketplace.json
public/index.html
```

Publish `public/` with GitHub Pages or any static host. Host-specific
installation still uses the adapter format for that host; the public files are
for discovery, indexing, verification display, pricing, and governance.

## Transaction Ledger

The marketplace ledger records transaction events outside any single host
install flow. It can be connected to payment-provider webhooks.

```bash
python3 scripts/record_transaction.py purchase \
  --plugin zebra-image \
  --buyer user@example.com \
  --provider stripe \
  --provider-event-id evt_123 \
  --idempotency-key stripe:evt_123
```

Set `MARKETPLACE_LEDGER_SECRET` to store HMAC-signed entries and buyer HMAC
references. Do not commit a production ledger to a public repository.

## Governance

Governance lives in:

```text
marketplace/policies/governance.md
marketplace/governance/review-board.json
marketplace/governance/audit-log.jsonl
.github/ISSUE_TEMPLATE/
```

Public submissions should come through pull requests. Medium, high, and
critical risk capabilities require manual review before `status: listed`.

## Developer Submission Checklist

1. Add a plugin or capability package under `plugins/<plugin>`.
2. Add at least one portable `SKILL.md`.
3. Add `marketplace/listings/<plugin>.json`.
4. Declare supported adapters in `distribution.installCommands`.
5. Add or update the host-specific marketplace entry when an adapter needs it.
6. Run `python3 scripts/validate_marketplace.py --strict`.
7. Open a PR using the plugin submission template.
