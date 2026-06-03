#!/usr/bin/env python3
"""Check the official Meituan Paotui Skill source without redistributing it."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


UPSTREAM = "https://github.com/meituan/MT-Paotui-For-Client.git"


def main() -> None:
    local_root = os.environ.get("MEITUAN_PAOTUI_SKILL_ROOT", "")
    print("Meituan Paotui upstream check")
    print("official source: " + UPSTREAM)

    if local_root:
        root = Path(local_root).expanduser()
        print("MEITUAN_PAOTUI_SKILL_ROOT: " + str(root))
        skill_md = root / "SKILL.md"
        run_sh = root / "dist" / "run.sh"
        print("SKILL.md: " + ("present" if skill_md.is_file() else "missing"))
        print("dist/run.sh: " + ("present" if run_sh.is_file() else "missing"))
    else:
        print("MEITUAN_PAOTUI_SKILL_ROOT: not set")

    result = subprocess.run(
        ["git", "ls-remote", UPSTREAM, "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0 and result.stdout.strip():
        print("official source reachable: yes")
    else:
        print("official source reachable: no")
        if result.stderr.strip():
            print(result.stderr.strip())
        raise SystemExit(1)

    print("note: this adapter does not bundle upstream code without license or authorization.")


if __name__ == "__main__":
    main()

