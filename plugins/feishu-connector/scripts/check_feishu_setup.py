#!/usr/bin/env python3
"""Check whether the Feishu/Lark connector has the minimum local setup."""

from __future__ import annotations

import os
import shutil
import subprocess


def main() -> None:
    missing = [
        name
        for name in ("FEISHU_APP_ID", "FEISHU_APP_SECRET")
        if not os.environ.get(name)
    ]

    print("Feishu Connector setup check")
    if missing:
        print("Missing environment variables: " + ", ".join(missing))
    else:
        print("Feishu app credentials: present")

    node = shutil.which("node")
    npm = shutil.which("npm")
    npx = shutil.which("npx")
    print(f"node: {node or 'missing'}")
    print(f"npm: {npm or 'missing'}")
    print(f"npx: {npx or 'missing'}")

    if node:
        result = subprocess.run(
            [node, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        print("node version: " + result.stdout.strip())

    if missing or not npx:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

