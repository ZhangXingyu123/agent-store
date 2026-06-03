#!/usr/bin/env python3
"""Record marketplace transaction and entitlement events."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from marketplace_lib import (
    LEDGER_PATH,
    append_ledger_entry,
    buyer_ref,
    load_plugin_contexts,
    read_ledger,
    sha256_bytes,
    sign_transaction,
    transaction_hash,
)


EVENT_TYPES = {"purchase", "refund", "grant", "revoke"}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_listing(root: Path, plugin_name: str) -> dict:
    for context in load_plugin_contexts(root):
        if context.entry.get("name") == plugin_name and context.listing:
            return context.listing
    raise SystemExit(f"Unknown plugin or missing listing: {plugin_name}")


def last_hash(entries: list[dict]) -> str:
    if not entries:
        return "GENESIS"
    return str(entries[-1].get("entry_hash", "GENESIS"))


def make_entry(args: argparse.Namespace, listing: dict, previous_hash: str) -> dict:
    idempotency_hash = sha256_bytes(args.idempotency_key.encode("utf-8"))
    entitlement_status = "active"
    if args.event_type in {"refund", "revoke"}:
        entitlement_status = "revoked"

    amount_cents = args.amount_cents
    currency = args.currency
    if args.event_type in {"grant", "revoke"}:
        amount_cents = 0
    if amount_cents is None:
        amount_cents = int(listing.get("pricing", {}).get("priceCents", 0))
    if currency is None:
        currency = listing.get("pricing", {}).get("currency", "USD")

    entry = {
        "schema_version": "1.0",
        "id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "type": args.event_type,
        "plugin": args.plugin,
        "sku": listing["transactions"]["sku"],
        "buyer_ref": buyer_ref(args.buyer),
        "amount_cents": amount_cents,
        "currency": currency,
        "provider": args.provider,
        "provider_event_id": args.provider_event_id,
        "idempotency_key_hash": idempotency_hash,
        "entitlement": {
            "status": entitlement_status,
            "starts_at": args.starts_at or now_iso(),
            "ends_at": args.ends_at,
        },
        "reason": args.reason,
        "prev_hash": previous_hash,
    }
    entry_hash = transaction_hash(entry)
    entry["entry_hash"] = entry_hash
    secret = os.environ.get("MARKETPLACE_LEDGER_SECRET")
    if secret:
        entry["signature"] = sign_transaction(entry_hash, secret)
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a marketplace transaction event.")
    parser.add_argument("event_type", choices=sorted(EVENT_TYPES), help="Transaction event type.")
    parser.add_argument("--root", default=".", help="Marketplace repository root.")
    parser.add_argument("--ledger", default=str(LEDGER_PATH), help="Ledger JSONL path relative to root.")
    parser.add_argument("--plugin", required=True, help="Plugin name.")
    parser.add_argument("--buyer", required=True, help="Buyer identifier. Stored as a hash, not raw text.")
    parser.add_argument("--idempotency-key", required=True, help="Stable key for this provider event.")
    parser.add_argument("--provider", default="manual", help="Payment or authorization provider.")
    parser.add_argument("--provider-event-id", default=None, help="Provider event ID.")
    parser.add_argument("--amount-cents", type=int, default=None, help="Override amount in minor units.")
    parser.add_argument("--currency", default=None, help="Override currency.")
    parser.add_argument("--starts-at", default=None, help="Entitlement start timestamp.")
    parser.add_argument("--ends-at", default=None, help="Entitlement end timestamp.")
    parser.add_argument("--reason", default=None, help="Review, refund, grant, or revoke reason.")
    parser.add_argument("--dry-run", action="store_true", help="Print the entry without appending.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    listing = load_listing(root, args.plugin)
    if args.event_type == "purchase" and listing.get("pricing", {}).get("model") == "free":
        raise SystemExit(f"{args.plugin} is free; use grant if you need to create an entitlement record.")

    ledger_path = root / args.ledger
    entries = read_ledger(ledger_path)
    idempotency_hash = sha256_bytes(args.idempotency_key.encode("utf-8"))
    if any(entry.get("idempotency_key_hash") == idempotency_hash for entry in entries):
        raise SystemExit("Duplicate idempotency key; refusing to append.")

    entry = make_entry(args, listing, last_hash(entries))
    if args.dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    append_ledger_entry(ledger_path, entry)
    print(json.dumps({"id": entry["id"], "entry_hash": entry["entry_hash"], "ledger": str(ledger_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
