.PHONY: validate strict build transaction-dry-run

validate:
	python3 scripts/validate_marketplace.py

strict:
	python3 scripts/validate_marketplace.py --strict

build:
	python3 scripts/build_public_index.py --marketplace-source ZhangXingyu123/codex-skill-store

transaction-dry-run:
	python3 scripts/record_transaction.py purchase \
		--plugin zebra-image \
		--buyer demo@example.com \
		--provider manual \
		--provider-event-id demo_001 \
		--idempotency-key manual:demo_001 \
		--dry-run
