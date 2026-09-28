#!/usr/bin/env python3
"""Run an authorized Nmap scan locally or publish one reviewed report."""

from __future__ import annotations

import argparse
import ipaddress
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an authorized Nmap scan locally or publish a separately reviewed report."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="IPv4/IPv6 address, localhost, or the authorized scanme.nmap.org host",
    )
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="Confirm that you own the target or have permission to scan it",
    )
    parser.add_argument(
        "--publish-report",
        type=Path,
        help="Publish this existing report from scan_reports instead of running a scan",
    )
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Confirm the report was reviewed and is safe to commit and push",
    )
    args = parser.parse_args(argv)

    if args.publish_report:
        if args.target or args.authorized:
            parser.error("--publish-report cannot be combined with a scan target")
        if not args.reviewed:
            parser.error("--publish-report requires --reviewed")
        return args

    if args.reviewed:
        parser.error("--reviewed is only valid with --publish-report")
    if not args.target:
        parser.error("a scan target or --publish-report is required")

    normalized_target = args.target.strip().lower().rstrip(".")
    if normalized_target == "localhost":
        args.target = "127.0.0.1"
    elif normalized_target == "scanme.nmap.org":
        args.target = normalized_target
    else:
        try:
            args.target = str(ipaddress.ip_address(normalized_target))
        except ValueError:
            parser.error(
                "target must be an IP address, localhost, or scanme.nmap.org"
            )

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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parent
    report_dir = repo / "scan_reports"

    if args.publish_report:
        report = args.publish_report.resolve()
        expected_dir = report_dir.resolve()
        if not report.is_file() or not report.is_relative_to(expected_dir):
            print("Error: publish target must be an existing file in scan_reports.", file=sys.stderr)
            return 1
        if shutil.which("git") is None:
            print("Error: git is not installed or is not on PATH.", file=sys.stderr)
            return 1
        relative_report = report.relative_to(repo)
        try:
            # New scan reports are ignored by default; only this reviewed path is forced in.
            run_git(repo, "add", "--force", "--", relative_report.as_posix())
            run_git(
                repo,
                "commit",
                "-m",
                "Publish reviewed scan report",
                "--",
                relative_report.as_posix(),
            )
            branch = run_git(repo, "branch", "--show-current").stdout.strip()
            if not branch:
                raise RuntimeError("cannot push a report from a detached Git HEAD")
            run_git(repo, "push", "origin", branch)
        except subprocess.CalledProcessError as exc:
            command = " ".join(str(part) for part in exc.cmd)
            details = (exc.stderr or exc.stdout or "No error output").strip()
            print(f"Error: command failed: {command}\n{details}", file=sys.stderr)
            return 1
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print("Reviewed report committed and pushed successfully.")
        return 0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = report_dir / f"nmap_vulnerability_scan_{timestamp}.txt"

    if shutil.which("nmap") is None:
        print("Error: nmap is not installed or is not on PATH.", file=sys.stderr)
        return 1
    report_dir.mkdir(parents=True, exist_ok=True)
    # Restrict NSE checks to scripts categorized as both vulnerability checks and
    # safe. This respects scanme.nmap.org's ban on exploit and denial-of-service
    # testing while still producing a lightweight vulnerability-oriented report.
    scan_command = ["nmap", "-sV", "--script", "vuln and safe", args.target]

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
    print(f"Scan report written to {report}")
    print("Report remains local. Review it before using --publish-report PATH --reviewed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
