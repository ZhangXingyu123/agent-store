# Governance Policy

This marketplace is a curated catalog, not an unreviewed package dump.

## Roles

- `submitter`: proposes a plugin or listing update.
- `maintainer`: owns a plugin and responds to issues.
- `reviewer`: validates metadata, source boundaries, and user-risk claims.
- `security-reviewer`: handles credential, MCP, data, and abuse risk.
- `marketplace-admin`: can approve, suspend, delist, or restore listings.

## Submission path

1. Submit a pull request with a plugin folder and listing JSON.
2. Run `python3 scripts/validate_marketplace.py`.
3. Fill out the plugin submission checklist.
4. A reviewer assigns a risk tier.
5. Medium, high, and critical risk plugins receive manual review.
6. Approved listings move to `status: listed`.

## Suspension and takedown

A marketplace-admin can suspend a listing immediately when it has credible
security, privacy, abuse, licensing, payment, or user-harm risk. The action must
be recorded in `marketplace/governance/audit-log.jsonl`.

## Appeals

Maintainers may appeal by opening a governance report with:

- Plugin name.
- Decision being appealed.
- Evidence or remediation.
- Requested outcome.

The appeal should be reviewed by someone who did not make the original decision
when practical.

## Conflicts of interest

Reviewers should not approve plugins they maintain or financially benefit from
unless a second reviewer signs off.

## Public commitments

- Pricing must be visible before purchase.
- Data access and permissions must be listed before install.
- Paid entitlements must have refund and revocation records.
- High-risk actions must require explicit user confirmation.
- Redistribution boundaries must be clear for third-party upstream code.
