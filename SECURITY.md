# Security

Report security, privacy, unsafe-action, credential, and payment issues through
the security issue template or by contacting `security@example.com`.

Do not include private credentials, tokens, session cookies, or customer data in
public reports.

## Marketplace response

- Credible high-severity reports can trigger immediate suspension.
- Suspensions are recorded in `marketplace/governance/audit-log.jsonl`.
- Maintainers must provide remediation and a version bump before relisting.
- Payment and entitlement issues should include provider event IDs, not raw
  buyer credentials.

## Local checks

```bash
python3 scripts/validate_marketplace.py --strict
```

The validator includes a lightweight secret scan, but it is not a substitute
for manual review or dedicated security tooling.
