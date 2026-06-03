# Public Codex Plugin Marketplace

This repository is a complete public-marketplace skeleton for Codex plugins. It
keeps the Codex-compatible marketplace catalog small, then layers public
listing metadata, validation, distribution artifacts, transaction records, and
governance policy around it.

## User install flow

```bash
codex plugin marketplace add ZhangXingyu123/codex-skill-store
```

Then open **Plugins** in the Codex app or run `/plugins` in Codex CLI, switch
to this marketplace source, and install a plugin.

For local testing from a clone:

```bash
codex plugin marketplace add /path/to/codex-skill-store
```

## Marketplace layout

```text
.agents/plugins/marketplace.json          # Codex-readable marketplace catalog
plugins/<plugin>/.codex-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
marketplace/listings/<plugin>.json        # Public listing, pricing, governance
marketplace/policies/                     # Validation, distribution, trade, governance
marketplace/transactions/                 # Private ledger location, ignored by git
scripts/validate_marketplace.py           # Validation gate
scripts/build_public_index.py             # Generates public storefront artifacts
scripts/record_transaction.py             # Purchase/refund/grant/revoke ledger events
public/index.html                         # Generated public storefront
public/marketplace.json                   # Generated public catalog
```

## Current listings

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

- Codex marketplace entry shape.
- Plugin manifest shape.
- Skill frontmatter.
- Local source-path boundaries.
- Listing metadata.
- Pricing and SKU metadata.
- Governance and risk metadata.
- Optional MCP config paths.
- Lightweight secret patterns.
- Transaction ledger hash chain when a local ledger exists.

## Build public distribution artifacts

```bash
python3 scripts/build_public_index.py --marketplace-source ZhangXingyu123/codex-skill-store
```

This writes:

```text
public/marketplace.json
public/index.html
```

Publish `public/` with GitHub Pages or any static host. Codex installation still
uses `.agents/plugins/marketplace.json`; the public files are for discovery,
indexing, verification display, and commercial metadata.

## Transaction ledger

The marketplace ledger records transaction events outside the Codex install
flow. It can be connected to payment-provider webhooks.

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
critical risk plugins require manual review before `status: listed`.

## Developer submission checklist

1. Add `plugins/<plugin>/.codex-plugin/plugin.json`.
2. Add at least one `plugins/<plugin>/skills/<skill>/SKILL.md`.
3. Add `marketplace/listings/<plugin>.json`.
4. Add a marketplace entry in `.agents/plugins/marketplace.json`.
5. Run `python3 scripts/validate_marketplace.py --strict`.
6. Open a PR using the plugin submission template.
