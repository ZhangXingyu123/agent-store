#!/usr/bin/env python3
"""Shared helpers for the public Agent Store marketplace."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

ALLOWED_INSTALLATION = {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
ALLOWED_AUTHENTICATION = {"ON_INSTALL", "ON_USE"}
ALLOWED_LISTING_STATUS = {"listed", "unlisted", "suspended", "deprecated"}
ALLOWED_PRICING_MODELS = {"free", "one_time", "subscription", "usage", "external"}
ALLOWED_REVIEW_STATES = {"pending", "approved", "rejected", "suspended"}
ALLOWED_RISK_TIERS = {"low", "medium", "high", "critical"}

MARKETPLACE_PATH = Path(".agents/plugins/marketplace.json")
LISTINGS_DIR = Path("marketplace/listings")
LEDGER_PATH = Path("marketplace/transactions/ledger.jsonl")
PLATFORMS_PATH = Path("marketplace/platforms.json")

SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic_token_assignment", re.compile(r"(?i)\b(?:secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
]

TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".js",
    ".ts",
    ".mjs",
    ".cjs",
    ".sh",
    ".csv",
}


@dataclass
class PluginContext:
    entry: dict[str, Any]
    plugin_path: Path
    manifest_path: Path
    manifest: dict[str, Any] | None
    listing_path: Path
    listing: dict[str, Any] | None
    skill_paths: list[Path]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_tree_files(path: Path) -> list[Path]:
    ignored_names = {".DS_Store"}
    ignored_dirs = {".git", "__pycache__", ".pytest_cache"}
    files: list[Path] = []
    for item in path.rglob("*"):
        if any(part in ignored_dirs for part in item.parts):
            continue
        if item.name in ignored_names or item.suffix == ".pyc":
            continue
        if item.is_file():
            files.append(item)
    return sorted(files, key=lambda p: p.relative_to(path).as_posix())


def sha256_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for item in iter_tree_files(path):
        rel = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(item).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def resolve_marketplace_source(root: Path, source_path: str) -> Path:
    if not source_path.startswith("./"):
        raise ValueError("source.path must start with ./")
    resolved = (root / source_path[2:]).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError("source.path must stay inside the marketplace root")
    return resolved


def load_marketplace(root: Path) -> dict[str, Any]:
    return read_json(root / MARKETPLACE_PATH)


def load_plugin_contexts(root: Path) -> list[PluginContext]:
    marketplace = load_marketplace(root)
    contexts: list[PluginContext] = []
    for entry in marketplace.get("plugins", []):
        plugin_name = str(entry.get("name", ""))
        source_path = str(entry.get("source", {}).get("path", ""))
        try:
            plugin_path = resolve_marketplace_source(root, source_path)
        except ValueError:
            plugin_path = root / "__invalid_source__" / plugin_name
        manifest_path = plugin_path / ".codex-plugin" / "plugin.json"
        manifest = read_json(manifest_path) if manifest_path.exists() else None
        listing_path = root / LISTINGS_DIR / f"{plugin_name}.json"
        listing = read_json(listing_path) if listing_path.exists() else None
        skill_paths: list[Path] = []
        if manifest:
            skills_rel = manifest.get("skills")
            if isinstance(skills_rel, str):
                skills_dir = (plugin_path / skills_rel).resolve()
                if skills_dir.exists():
                    skill_paths = sorted(skills_dir.rglob("SKILL.md"))
        contexts.append(
            PluginContext(
                entry=entry,
                plugin_path=plugin_path,
                manifest_path=manifest_path,
                manifest=manifest,
                listing_path=listing_path,
                listing=listing,
                skill_paths=skill_paths,
            )
        )
    return contexts


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return frontmatter
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')
    return {}


def scan_for_secret_like_values(path: Path) -> list[str]:
    findings: list[str] = []
    for item in iter_tree_files(path):
        if item.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = item.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = item.relative_to(path).as_posix()
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{rel}: potential {label}")
    return findings


def transaction_hash(entry: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in entry.items() if key not in {"entry_hash", "signature"}}
    return sha256_bytes(canonical_json(unsigned))


def sign_transaction(entry_hash: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), entry_hash.encode("ascii"), hashlib.sha256).hexdigest()


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            entries.append(entry)
    return entries


def append_ledger_entry(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        handle.write("\n")


def buyer_ref(raw_buyer: str) -> str:
    secret = os.environ.get("MARKETPLACE_LEDGER_SECRET")
    if secret:
        digest = hmac.new(secret.encode("utf-8"), raw_buyer.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"hmac-sha256:{digest}"
    return f"sha256:{sha256_bytes(raw_buyer.encode('utf-8'))}"


def build_public_catalog(root: Path) -> dict[str, Any]:
    marketplace = load_marketplace(root)
    platforms_path = root / PLATFORMS_PATH
    platforms = read_json(platforms_path) if platforms_path.exists() else None
    plugins: list[dict[str, Any]] = []
    for context in load_plugin_contexts(root):
        if not context.manifest or not context.listing:
            continue
        interface = context.manifest.get("interface", {})
        listing = context.listing
        plugins.append(
            {
                "name": context.manifest["name"],
                "version": context.manifest["version"],
                "status": listing["status"],
                "displayName": interface.get("displayName", context.manifest["name"]),
                "summary": interface.get("shortDescription", context.manifest.get("description", "")),
                "description": interface.get("longDescription", context.manifest.get("description", "")),
                "developer": listing["developer"],
                "category": listing.get("category", context.entry.get("category", "Other")),
                "capabilities": interface.get("capabilities", []),
                "pricing": listing["pricing"],
                "verification": listing["verification"],
                "governance": listing["governance"],
                "distribution": listing["distribution"],
                "checksums": {
                    "manifestSha256": sha256_file(context.manifest_path),
                    "pluginTreeSha256": sha256_tree(context.plugin_path),
                },
            }
        )
    return {
        "schemaVersion": "1.0",
        "name": marketplace["name"],
        "displayName": marketplace.get("interface", {}).get("displayName", marketplace["name"]),
        "primaryInstallCommand": "codex plugin marketplace add <marketplace-source>",
        "installCommands": [
            {
                "platform": "codex",
                "command": "codex plugin marketplace add <marketplace-source>",
            }
        ],
        "platforms": platforms,
        "plugins": plugins,
    }
