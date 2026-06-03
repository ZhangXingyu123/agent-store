# Transaction Policy

Host-specific marketplace installation is not a payment processor. This repository
implements a marketplace-side transaction and entitlement ledger that can be
connected to a provider such as Stripe, Paddle, WeChat Pay, Alipay, or an
internal billing system.

## Event model

Supported event types:

- `purchase`: paid entitlement created from a provider event.
- `refund`: paid entitlement revoked or reversed.
- `grant`: manual or promotional entitlement.
- `revoke`: entitlement removed for policy, fraud, or support reasons.

Each ledger entry stores:

- Plugin name.
- SKU.
- Buyer reference as a hash, not raw email or account text.
- Provider and provider event ID.
- Amount and currency.
- Entitlement status and validity window.
- Previous ledger hash.
- Current ledger hash.
- Optional HMAC signature when `MARKETPLACE_LEDGER_SECRET` is configured.

## Recording events

```bash
python3 scripts/record_transaction.py purchase \
  --plugin zebra-image \
  --buyer user@example.com \
  --provider stripe \
  --provider-event-id evt_123 \
  --idempotency-key stripe:evt_123
```

Refund:

```bash
python3 scripts/record_transaction.py refund \
  --plugin zebra-image \
  --buyer user@example.com \
  --provider stripe \
  --provider-event-id re_123 \
  --idempotency-key stripe:re_123 \
  --reason duplicate-payment
```

Grant:

```bash
python3 scripts/record_transaction.py grant \
  --plugin zebra-image \
  --buyer user@example.com \
  --idempotency-key manual:grant:user@example.com:zebra-image \
  --reason beta-program
```

## Privacy

Do not commit production ledgers to a public repository. The default
`marketplace/transactions/.gitignore` excludes local ledgers. Use a private
object store or database for production transaction history.

## Enforcement

For paid listings, the market should check entitlement before:

- Showing private download URLs.
- Enabling premium hosted runtimes.
- Issuing support or settlement.
- Granting developer revenue share.

Public demo code may remain visible even when a premium runtime requires
entitlement.
