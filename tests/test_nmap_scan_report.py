"""Regression tests for the Nmap report publication boundary."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest import mock

import nmap_scan_report


class NmapReportTests(unittest.TestCase):
    def test_successful_scan_stays_local(self) -> None:
        with (
            mock.patch.object(nmap_scan_report.shutil, "which", return_value="/usr/bin/nmap"),
            mock.patch.object(nmap_scan_report.subprocess, "run", return_value=subprocess.CompletedProcess(["nmap"], 0, "scan output", "")) as run,
            mock.patch.object(Path, "mkdir") as mkdir,
            mock.patch.object(Path, "write_text") as write_text,
            mock.patch.object(nmap_scan_report, "run_git") as run_git,
        ):
            self.assertEqual(0, nmap_scan_report.main(["scanme.nmap.org", "--authorized"]))

        run.assert_called_once()
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        write_text.assert_called_once_with("scan output", encoding="utf-8")
        run_git.assert_not_called()

    def test_failed_scan_preserves_partial_output_without_git(self) -> None:
        failure = subprocess.CalledProcessError(
            1, ["nmap"], output="partial output", stderr="scan error"
        )
        with (
            mock.patch.object(nmap_scan_report.shutil, "which", return_value="/usr/bin/nmap"),
            mock.patch.object(nmap_scan_report.subprocess, "run", side_effect=failure),
            mock.patch.object(Path, "mkdir"),
            mock.patch.object(Path, "write_text") as write_text,
            mock.patch.object(nmap_scan_report, "run_git") as run_git,
        ):
            self.assertEqual(1, nmap_scan_report.main(["scanme.nmap.org", "--authorized"]))

        self.assertIn("partial output", write_text.call_args.args[0])
        run_git.assert_not_called()

    def test_publication_requires_review_and_report_inside_directory(self) -> None:
        outside = Path(__file__).resolve().parent / "outside.txt"
        with self.assertRaises(SystemExit):
            nmap_scan_report.parse_args(["--publish-report", str(outside)])
        with (
            mock.patch.object(Path, "is_file", return_value=True),
            mock.patch.object(nmap_scan_report, "run_git") as run_git,
        ):
            self.assertEqual(
                1, nmap_scan_report.main(["--publish-report", str(outside), "--reviewed"])
            )
            run_git.assert_not_called()


if __name__ == "__main__":
    unittest.main()
