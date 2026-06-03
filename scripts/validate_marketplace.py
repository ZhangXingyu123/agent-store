#!/usr/bin/env python3
"""Validate the public Agent Store marketplace."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from marketplace_lib import (
    ALLOWED_AUTHENTICATION,
    ALLOWED_INSTALLATION,
    ALLOWED_LISTING_STATUS,
    ALLOWED_PRICING_MODELS,
    ALLOWED_REVIEW_STATES,
    ALLOWED_RISK_TIERS,
    LEDGER_PATH,
    MARKETPLACE_PATH,
    NAME_RE,
    SEMVER_RE,
    build_public_catalog,
    load_marketplace,
    load_plugin_contexts,
    parse_skill_frontmatter,
    read_ledger,
    resolve_marketplace_source,
    scan_for_secret_like_values,
    sign_transaction,
    transaction_hash,
    write_json,
)


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def add_warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


def validate_listing(name: str, listing: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    prefix = f"marketplace/listings/{name}.json"
    if listing.get("name") != name:
        add_error(errors, f"{prefix}: name must match marketplace entry")
    if listing.get("status") not in ALLOWED_LISTING_STATUS:
        add_error(errors, f"{prefix}: status must be one of {sorted(ALLOWED_LISTING_STATUS)}")
    if not listing.get("summary"):
        add_error(errors, f"{prefix}: summary is required")

    developer = listing.get("developer")
    if not isinstance(developer, dict) or not developer.get("name"):
        add_error(errors, f"{prefix}: developer.name is required")
    if not isinstance(developer, dict) or not developer.get("contact"):
        add_warning(warnings, f"{prefix}: developer.contact is recommended for public listings")

    distribution = listing.get("distribution")
    if not isinstance(distribution, dict):
        add_error(errors, f"{prefix}: distribution object is required")
    else:
        if not distribution.get("sourcePath"):
            add_error(errors, f"{prefix}: distribution.sourcePath is required")
        install_commands = distribution.get("installCommands")
        if not isinstance(install_commands, list) or not install_commands:
            add_warning(warnings, f"{prefix}: distribution.installCommands is recommended")
        else:
            for idx, command in enumerate(install_commands):
                if not isinstance(command, dict):
                    add_error(errors, f"{prefix}: distribution.installCommands[{idx}] must be an object")
                    continue
                if not command.get("platform"):
                    add_error(errors, f"{prefix}: distribution.installCommands[{idx}].platform is required")
                if not command.get("command"):
                    add_error(errors, f"{prefix}: distribution.installCommands[{idx}].command is required")

    verification = listing.get("verification")
    if not isinstance(verification, dict):
        add_error(errors, f"{prefix}: verification object is required")
    else:
        if verification.get("state") != "passed":
            add_warning(warnings, f"{prefix}: verification.state is not passed")
        if not verification.get("checkedAt"):
            add_warning(warnings, f"{prefix}: verification.checkedAt is recommended")

    pricing = listing.get("pricing")
    if not isinstance(pricing, dict):
        add_error(errors, f"{prefix}: pricing object is required")
    else:
        model = pricing.get("model")
        if model not in ALLOWED_PRICING_MODELS:
            add_error(errors, f"{prefix}: pricing.model must be one of {sorted(ALLOWED_PRICING_MODELS)}")
        price_cents = pricing.get("priceCents", 0)
        if model == "free" and price_cents != 0:
            add_error(errors, f"{prefix}: free listings must have priceCents 0")
        if model in {"one_time", "subscription", "usage"} and not pricing.get("currency"):
            add_error(errors, f"{prefix}: paid listings must declare pricing.currency")
        if model in {"one_time", "subscription"} and not isinstance(price_cents, int):
            add_error(errors, f"{prefix}: pricing.priceCents must be an integer")

    transactions = listing.get("transactions")
    if not isinstance(transactions, dict):
        add_error(errors, f"{prefix}: transactions object is required")
    else:
        if not transactions.get("sku"):
            add_error(errors, f"{prefix}: transactions.sku is required")
        if transactions.get("requiresEntitlement") and listing.get("pricing", {}).get("model") == "free":
            add_warning(warnings, f"{prefix}: free listing requires entitlement")

    governance = listing.get("governance")
    if not isinstance(governance, dict):
        add_error(errors, f"{prefix}: governance object is required")
    else:
        if governance.get("reviewState") not in ALLOWED_REVIEW_STATES:
            add_error(errors, f"{prefix}: governance.reviewState must be one of {sorted(ALLOWED_REVIEW_STATES)}")
        if governance.get("riskTier") not in ALLOWED_RISK_TIERS:
            add_error(errors, f"{prefix}: governance.riskTier must be one of {sorted(ALLOWED_RISK_TIERS)}")
        if governance.get("riskTier") in {"high", "critical"} and not governance.get("userConfirmationRequired"):
            add_warning(warnings, f"{prefix}: high-risk listings should require user confirmation")


def validate_ledger(root: Path, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    ledger_path = root / LEDGER_PATH
    report = {"path": str(LEDGER_PATH), "entries": 0, "lastHash": "GENESIS", "signed": False}
    try:
        entries = read_ledger(ledger_path)
    except ValueError as exc:
        add_error(errors, str(exc))
        return report
    previous_hash = "GENESIS"
    seen_idempotency: set[str] = set()
    secret = os.environ.get("MARKETPLACE_LEDGER_SECRET")
    for idx, entry in enumerate(entries, 1):
        entry_id = entry.get("id", f"line {idx}")
        if entry.get("prev_hash") != previous_hash:
            add_error(errors, f"{LEDGER_PATH}:{idx}: prev_hash mismatch for {entry_id}")
        calculated_hash = transaction_hash(entry)
        if entry.get("entry_hash") != calculated_hash:
            add_error(errors, f"{LEDGER_PATH}:{idx}: entry_hash mismatch for {entry_id}")
        if secret and entry.get("signature"):
            expected_signature = sign_transaction(calculated_hash, secret)
            if entry["signature"] != expected_signature:
                add_error(errors, f"{LEDGER_PATH}:{idx}: signature mismatch for {entry_id}")
            report["signed"] = True
        idempotency_hash = entry.get("idempotency_key_hash")
        if idempotency_hash:
            if idempotency_hash in seen_idempotency:
                add_error(errors, f"{LEDGER_PATH}:{idx}: duplicate idempotency_key_hash")
            seen_idempotency.add(idempotency_hash)
        previous_hash = str(entry.get("entry_hash", calculated_hash))
    if entries and not secret:
        add_warning(warnings, f"{LEDGER_PATH}: ledger signatures were not checked because MARKETPLACE_LEDGER_SECRET is not set")
    report["entries"] = len(entries)
    report["lastHash"] = previous_hash
    return report


def validate_marketplace(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    marketplace_file = root / MARKETPLACE_PATH
    if not marketplace_file.exists():
        return {
            "valid": False,
            "errors": [f"{MARKETPLACE_PATH}: file is missing"],
            "warnings": [],
            "plugins": [],
        }

    marketplace = load_marketplace(root)
    if not NAME_RE.match(str(marketplace.get("name", ""))):
        add_error(errors, f"{MARKETPLACE_PATH}: name must be kebab-case")
    if not marketplace.get("interface", {}).get("displayName"):
        add_warning(warnings, f"{MARKETPLACE_PATH}: interface.displayName is recommended")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        add_error(errors, f"{MARKETPLACE_PATH}: plugins must be a non-empty array")
        plugins = []

    seen_names: set[str] = set()
    plugin_reports: list[dict[str, Any]] = []
    contexts = load_plugin_contexts(root)
    for context in contexts:
        entry = context.entry
        name = str(entry.get("name", ""))
        entry_prefix = f"{MARKETPLACE_PATH}: plugins[{name or '?'}]"
        plugin_report: dict[str, Any] = {"name": name, "errors": [], "warnings": []}
        local_errors: list[str] = plugin_report["errors"]
        local_warnings: list[str] = plugin_report["warnings"]

        if not NAME_RE.match(name):
            add_error(local_errors, f"{entry_prefix}: name must be kebab-case")
        if name in seen_names:
            add_error(local_errors, f"{entry_prefix}: duplicate plugin name")
        seen_names.add(name)

        source = entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "local":
            add_error(local_errors, f"{entry_prefix}: source.source must be local")
        else:
            source_path = str(source.get("path", ""))
            try:
                resolve_marketplace_source(root, source_path)
            except ValueError as exc:
                add_error(local_errors, f"{entry_prefix}: {exc}")

        policy = entry.get("policy")
        if not isinstance(policy, dict):
            add_error(local_errors, f"{entry_prefix}: policy is required")
        else:
            if policy.get("installation") not in ALLOWED_INSTALLATION:
                add_error(local_errors, f"{entry_prefix}: invalid policy.installation")
            if policy.get("authentication") not in ALLOWED_AUTHENTICATION:
                add_error(local_errors, f"{entry_prefix}: invalid policy.authentication")
        if not entry.get("category"):
            add_error(local_errors, f"{entry_prefix}: category is required")

        if not context.plugin_path.exists():
            add_error(local_errors, f"{name}: plugin directory is missing at {context.plugin_path}")
        if not context.manifest_path.exists():
            add_error(local_errors, f"{name}: .codex-plugin/plugin.json is missing")
        if not context.manifest:
            errors.extend(local_errors)
            warnings.extend(local_warnings)
            plugin_reports.append(plugin_report)
            continue

        manifest = context.manifest
        manifest_prefix = f"plugins/{name}/.codex-plugin/plugin.json"
        if manifest.get("name") != name:
            add_error(local_errors, f"{manifest_prefix}: manifest name must match marketplace entry")
        if not SEMVER_RE.match(str(manifest.get("version", ""))):
            add_error(local_errors, f"{manifest_prefix}: version must be semver")
        if not manifest.get("description"):
            add_error(local_errors, f"{manifest_prefix}: description is required")
        if not manifest.get("skills"):
            add_error(local_errors, f"{manifest_prefix}: skills path is required")

        interface = manifest.get("interface", {})
        if not isinstance(interface, dict) or not interface.get("displayName"):
            add_warning(local_warnings, f"{manifest_prefix}: interface.displayName is recommended")
        if isinstance(interface, dict) and not interface.get("shortDescription"):
            add_warning(local_warnings, f"{manifest_prefix}: interface.shortDescription is recommended")

        mcp_servers = manifest.get("mcpServers")
        if mcp_servers:
            mcp_path = context.plugin_path / str(mcp_servers)
            if not mcp_path.exists():
                add_error(local_errors, f"{manifest_prefix}: mcpServers points to a missing file")

        if not context.skill_paths:
            add_error(local_errors, f"plugins/{name}: at least one SKILL.md is required")
        skill_names: set[str] = set()
        for skill_path in context.skill_paths:
            frontmatter = parse_skill_frontmatter(skill_path)
            rel_skill = skill_path.relative_to(root).as_posix()
            skill_name = frontmatter.get("name", "")
            if not NAME_RE.match(skill_name):
                add_error(local_errors, f"{rel_skill}: frontmatter name must be kebab-case")
            if skill_name in skill_names:
                add_error(local_errors, f"{rel_skill}: duplicate skill name in plugin")
            skill_names.add(skill_name)
            if len(frontmatter.get("description", "")) < 40:
                add_warning(local_warnings, f"{rel_skill}: description should be specific enough for routing")

        if not context.listing:
            add_error(local_errors, f"marketplace/listings/{name}.json is missing")
        else:
            validate_listing(name, context.listing, local_errors, local_warnings)

        secret_findings = scan_for_secret_like_values(context.plugin_path)
        for finding in secret_findings:
            add_warning(local_warnings, f"plugins/{name}/{finding}")

        plugin_reports.append(plugin_report)
        errors.extend(local_errors)
        warnings.extend(local_warnings)

    ledger_report = validate_ledger(root, errors, warnings)
    catalog = build_public_catalog(root) if not errors else None
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "pluginCount": len(contexts),
        "plugins": plugin_reports,
        "ledger": ledger_report,
        "catalogPreview": catalog,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the public Agent Store marketplace.")
    parser.add_argument("--root", default=".", help="Marketplace repository root.")
    parser.add_argument("--output", help="Write a JSON validation report.")
    parser.add_argument("--json", action="store_true", help="Print the validation report as JSON.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = validate_marketplace(root)
    if args.output:
        write_json(root / args.output, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if report["valid"] and not (args.strict and report["warnings"]) else "FAIL"
        print(f"{status}: {report.get('pluginCount', 0)} plugins checked")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")

    if report["errors"]:
        return 1
    if args.strict and report["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
