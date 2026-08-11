#!/usr/bin/env python3
"""Recommended build entrypoint for new ingests.

Runs the legacy/site indexes first, then ESS market/company intelligence indexes.
Use --check to validate both without writing.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, check):
    cmd = [sys.executable, os.path.join(HERE, script)]
    if check:
        cmd.append("--check")
    print("+", " ".join(cmd))
    return subprocess.call(cmd)


def main():
    check = "--check" in sys.argv
    rc = run("build_indexes.py", check)
    if rc != 0:
        return rc
    return run("build_ess_indexes.py", check)


if __name__ == "__main__":
    sys.exit(main())
