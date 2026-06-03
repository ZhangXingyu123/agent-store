# Transaction Ledger

Production transaction ledgers should not be committed to this repository.

Use `scripts/record_transaction.py` to append purchase, refund, grant, and
revoke events to a private JSONL ledger. The validator checks hash-chain
integrity when a ledger is present.
