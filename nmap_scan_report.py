#!/usr/bin/env python3
"""Run an authorized Nmap vulnerability scan and commit its report."""

from __future__ import annotations

import argparse
import ipaddress
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an authorized Nmap vulnerability scan and push the report."
    )
    parser.add_argument("target", help="IPv4 or IPv6 address to scan")
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="Confirm that you own the target or have permission to scan it",
    )
    args = parser.parse_args()

    try:
        args.target = str(ipaddress.ip_address(args.target))
    except ValueError:
        parser.error("target must be a valid IPv4 or IPv6 address")

    if not args.authorized:
        parser.error("--authorized is required; scan only systems you may test")

    return args


def run_git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parent
    report_dir = repo / "scan_reports"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = report_dir / f"nmap_vulnerability_scan_{timestamp}.txt"

    if shutil.which("nmap") is None:
        print("Error: nmap is not installed or is not on PATH.", file=sys.stderr)
        return 1
    if shutil.which("git") is None:
        print("Error: git is not installed or is not on PATH.", file=sys.stderr)
        return 1

    report_dir.mkdir(parents=True, exist_ok=True)
    scan_command = ["nmap", "-sV", "--script", "vuln", args.target]

    try:
        scan = subprocess.run(
            scan_command,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        # Preserve partial output for troubleshooting, but do not publish a failed scan.
        report.write_text(
            (exc.stdout or "") + "\n--- Nmap stderr ---\n" + (exc.stderr or ""),
            encoding="utf-8",
        )
        print(
            f"Error: Nmap failed with exit code {exc.returncode}. "
            f"Partial output was saved to {report}.",
            file=sys.stderr,
        )
        return 1

    report.write_text(scan.stdout, encoding="utf-8")
    relative_report = report.relative_to(repo)
    print(f"Scan report written to {report}")

    try:
        # Stage only this run's report so unrelated working-tree files are untouched.
        run_git(repo, "add", "--", relative_report.as_posix())
        run_git(repo, "commit", "-m", "Automated scan report", "--", relative_report.as_posix())
        run_git(repo, "push")
    except subprocess.CalledProcessError as exc:
        command = " ".join(str(part) for part in exc.cmd)
        details = (exc.stderr or exc.stdout or "No error output").strip()
        print(f"Error: command failed: {command}\n{details}", file=sys.stderr)
        return 1

    print("Report committed and pushed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
