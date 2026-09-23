from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import forensic_lab as lab  # noqa: E402


class VolumeTests(unittest.TestCase):
    def test_volume_rejects_invalid_geometry(self) -> None:
        with self.assertRaises(ValueError):
            lab.SimulatedVolume(cluster_size=10)
        with self.assertRaises(ValueError):
            lab.SimulatedVolume(cluster_count=0)

    def test_write_and_carve_preserve_content_and_hash(self) -> None:
        volume = lab.SimulatedVolume()
        payload = b"synthetic evidence" * 20
        volume.write_file("evidence.txt", payload)
        recovered = volume.carve()[0]
        self.assertEqual(recovered.content, payload)
        self.assertTrue(recovered.exact_match)

    def test_duplicate_names_are_rejected(self) -> None:
        volume = lab.SimulatedVolume()
        volume.write_file("same.txt", b"first")
        with self.assertRaises(ValueError):
            volume.write_file("same.txt", b"second")

    def test_recycle_bin_retains_directory_metadata(self) -> None:
        volume = lab.SimulatedVolume()
        payload = b"recover me"
        volume.write_file("recover.txt", payload)
        volume.move_to_recycle_bin("recover.txt")
        recovered = volume.recover_from_recycle_bin("recover.txt")
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.content, payload)  # type: ignore[union-attr]
        self.assertEqual(recovered.method, "directory-metadata")  # type: ignore[union-attr]

    def test_empty_recycle_bin_removes_metadata_but_carving_works(self) -> None:
        volume = lab.SimulatedVolume()
        volume.write_file("carve.txt", b"content" * 100)
        volume.move_to_recycle_bin("carve.txt")
        volume.empty_recycle_bin()
        self.assertIsNone(volume.recover_from_recycle_bin("carve.txt"))
        self.assertTrue(volume.carve()[0].exact_match)

    def test_full_overwrite_prevents_recovery(self) -> None:
        volume = lab.SimulatedVolume()
        entry = volume.write_file("gone.txt", b"content" * 100)
        volume.delete_file("gone.txt")
        overwritten = volume.overwrite_deleted_clusters(entry, 1.0, seed=7)
        self.assertEqual(len(overwritten), len(entry.clusters))
        self.assertEqual(volume.carve(), [])

    def test_overwrite_rejects_invalid_fraction(self) -> None:
        volume = lab.SimulatedVolume()
        entry = volume.write_file("value.txt", b"value")
        volume.delete_file("value.txt")
        with self.assertRaises(ValueError):
            volume.overwrite_deleted_clusters(entry, 1.1, seed=1)

    def test_overwrite_selection_is_repeatable(self) -> None:
        def selected() -> tuple[int, ...]:
            volume = lab.SimulatedVolume()
            entry = volume.write_file("large.bin", b"A" * 2048)
            volume.delete_file("large.bin")
            return volume.overwrite_deleted_clusters(entry, 0.5, seed=42)

        self.assertEqual(selected(), selected())

    def test_exported_image_has_expected_size(self) -> None:
        volume = lab.SimulatedVolume(cluster_size=128, cluster_count=10)
        volume.write_file("tiny.txt", b"tiny")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "image.bin"
            volume.export_image(output)
            self.assertEqual(output.stat().st_size, 1280)


class ExperimentTests(unittest.TestCase):
    def test_sample_files_are_synthetic_and_distinct(self) -> None:
        fixtures = lab.sample_files()
        self.assertEqual(set(fixtures), {"text", "image", "document"})
        self.assertEqual(len({value for value in fixtures.values()}), 3)

    def test_recycle_and_emptied_scenarios_recover_exactly(self) -> None:
        payload = b"controlled" * 100
        for scenario in ("recycle-bin", "emptied-recycle-bin"):
            result = lab.run_trial("text", payload, scenario, 0.0, 1, seed=1)
            self.assertTrue(result.recovered)
            self.assertTrue(result.exact_match)
            self.assertEqual(result.recovery_ratio, 1.0)

    def test_unknown_scenario_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_trial("text", b"x", "unknown", 0.0, 1, seed=1)

    def test_experiment_row_count_and_reproducibility(self) -> None:
        first = lab.run_experiment(trials=2, seed=99)
        second = lab.run_experiment(trials=2, seed=99)
        self.assertEqual(len(first), 36)
        self.assertEqual(first, second)
        with self.assertRaises(ValueError):
            lab.run_experiment(trials=0)

    def test_summary_rates_are_bounded(self) -> None:
        summary = lab.summarize(lab.run_experiment(trials=2, seed=5))
        self.assertEqual(len(summary), 6)
        for row in summary:
            self.assertGreaterEqual(row["recovery_rate"], 0.0)
            self.assertLessEqual(row["recovery_rate"], 1.0)
            self.assertGreaterEqual(row["mean_matching_byte_ratio"], 0.0)
            self.assertLessEqual(row["mean_matching_byte_ratio"], 1.0)

    def test_result_writers_create_csv_and_json(self) -> None:
        results = lab.run_experiment(trials=1, seed=3)
        summary = lab.summarize(results)
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "nested" / "results.csv"
            json_path = Path(directory) / "nested" / "summary.json"
            lab.write_results(csv_path, results)
            lab.write_summary(json_path, summary)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 18)
            self.assertEqual(len(json.loads(json_path.read_text(encoding="utf-8"))), 6)


class CommandLineTests(unittest.TestCase):
    def test_image_command_creates_only_requested_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "simulation.bin"
            stdout = StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(lab.main(["image", str(output)]), 0)
            self.assertTrue(output.exists())
            self.assertIn("simulated image", stdout.getvalue())

    def test_experiment_command_writes_requested_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / "results.csv"
            summary = Path(directory) / "summary.json"
            with redirect_stdout(StringIO()):
                code = lab.main(
                    [
                        "experiment",
                        "--trials",
                        "1",
                        "--output",
                        str(results),
                        "--summary",
                        str(summary),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue(results.exists())
            self.assertTrue(summary.exists())


if __name__ == "__main__":
    unittest.main()
