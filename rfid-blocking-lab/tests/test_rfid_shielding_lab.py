from __future__ import annotations

import csv
import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import rfid_shielding_lab as lab  # noqa: E402


class ModelTests(unittest.TestCase):
    def test_more_attenuation_reduces_effective_range(self) -> None:
        tag = lab.TAGS[1]
        ranges = [lab.effective_range_cm(tag, material) for material in lab.MATERIALS]
        self.assertEqual(ranges, sorted(ranges, reverse=True))

    def test_unshielded_range_matches_tag_assumption(self) -> None:
        self.assertEqual(lab.effective_range_cm(lab.TAGS[1], lab.MATERIALS[0]), 8.0)

    def test_probability_decreases_with_distance(self) -> None:
        probabilities = [
            lab.read_probability(distance, lab.TAGS[2], lab.MATERIALS[0])
            for distance in range(1, 16)
        ]
        self.assertEqual(probabilities, sorted(probabilities, reverse=True))

    def test_probability_is_bounded(self) -> None:
        for tag in lab.TAGS:
            for material in lab.MATERIALS:
                probability = lab.read_probability(4, tag, material)
                self.assertGreaterEqual(probability, 0.0)
                self.assertLessEqual(probability, 1.0)

    def test_invalid_distance_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.read_probability(0, lab.TAGS[0], lab.MATERIALS[0])

    def test_invalid_material_attenuation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.effective_range_cm(lab.TAGS[0], lab.Material("bad", -1, "test"))


class ExperimentTests(unittest.TestCase):
    def test_expected_trial_count(self) -> None:
        rows = lab.run_experiment(repetitions=2, distances_cm=(1, 2, 3))
        self.assertEqual(len(rows), len(lab.TAGS) * len(lab.MATERIALS) * 3 * 2)

    def test_experiment_is_reproducible(self) -> None:
        self.assertEqual(
            lab.run_experiment(repetitions=2, seed=42, distances_cm=(1, 2)),
            lab.run_experiment(repetitions=2, seed=42, distances_cm=(1, 2)),
        )

    def test_different_seed_changes_outcomes(self) -> None:
        first = lab.run_experiment(repetitions=5, seed=1, distances_cm=(3, 4, 5))
        second = lab.run_experiment(repetitions=5, seed=2, distances_cm=(3, 4, 5))
        self.assertNotEqual(first, second)

    def test_rows_are_clearly_labeled_as_simulated(self) -> None:
        rows = lab.run_experiment(repetitions=1, distances_cm=(1,))
        self.assertTrue(all(row.data_classification == lab.MODEL_NOTICE for row in rows))

    def test_nonpositive_repetitions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_experiment(repetitions=0)

    def test_excessive_repetitions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_experiment(repetitions=lab.MAX_REPETITIONS + 1)

    def test_empty_distances_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_experiment(distances_cm=())

    def test_summary_has_one_row_per_tag_and_material(self) -> None:
        rows = lab.run_experiment(repetitions=2, distances_cm=(1, 2))
        summary = lab.summarize(rows)
        self.assertEqual(len(summary), len(lab.TAGS) * len(lab.MATERIALS))

    def test_summary_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            lab.summarize([])

    def test_foil_reduces_reliable_range_in_completed_experiment(self) -> None:
        summary = lab.summarize(lab.run_experiment())
        card = {row["material"]: row for row in summary if row["tag"] == "id_card"}
        self.assertGreater(
            card["no_shield_control"]["farthest_reliable_read_cm"],
            card["aluminum_foil"]["farthest_reliable_read_cm"],
        )


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = PROJECT_ROOT / "tests" / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        for path in self.output_dir.glob("test-*"):
            if path.is_file():
                path.unlink()

    def test_writers_create_valid_outputs(self) -> None:
        rows = lab.run_experiment(repetitions=1, distances_cm=(1, 2))
        summary = lab.summarize(rows)
        csv_path = self.output_dir / "test-results.csv"
        json_path = self.output_dir / "test-summary.json"
        lab.write_results(csv_path, rows)
        lab.write_summary(json_path, summary)
        with csv_path.open(encoding="utf-8", newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), len(rows))
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["notice"], lab.MODEL_NOTICE)
        self.assertEqual(len(payload["results"]), len(summary))

    def test_experiment_cli_writes_outputs(self) -> None:
        results = self.output_dir / "test-cli-results.csv"
        summary = self.output_dir / "test-cli-summary.json"
        with redirect_stdout(StringIO()) as output:
            code = lab.main(
                [
                    "experiment",
                    "--repetitions",
                    "1",
                    "--output",
                    str(results),
                    "--summary",
                    str(summary),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn(lab.MODEL_NOTICE, output.getvalue())
        self.assertTrue(results.exists())
        self.assertTrue(summary.exists())

    def test_estimate_cli_labels_output(self) -> None:
        with redirect_stdout(StringIO()) as output:
            code = lab.main(["estimate", "id_card", "aluminum_foil"])
        self.assertEqual(code, 0)
        self.assertIn(lab.MODEL_NOTICE, output.getvalue())


if __name__ == "__main__":
    unittest.main()
