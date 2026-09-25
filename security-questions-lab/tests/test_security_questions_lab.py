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

import security_questions_lab as lab  # noqa: E402


class GenerationTests(unittest.TestCase):
    def test_expected_trial_count(self) -> None:
        self.assertEqual(len(lab.generate_trials(10)), 10 * len(lab.QUESTIONS))

    def test_generation_is_reproducible(self) -> None:
        self.assertEqual(lab.generate_trials(10, 7), lab.generate_trials(10, 7))

    def test_different_seed_changes_results(self) -> None:
        self.assertNotEqual(lab.generate_trials(10, 7), lab.generate_trials(10, 8))

    def test_participant_bounds_are_enforced(self) -> None:
        with self.assertRaises(ValueError):
            lab.generate_trials(lab.MIN_PARTICIPANTS - 1)
        with self.assertRaises(ValueError):
            lab.generate_trials(lab.MAX_PARTICIPANTS + 1)

    def test_empty_questions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.generate_trials(10, questions=())

    def test_invalid_probability_is_rejected(self) -> None:
        bad = lab.QuestionModel("bad", 1.1, 0.5, 0.5)
        with self.assertRaises(ValueError):
            lab.generate_trials(10, questions=(bad,))

    def test_correct_answer_requires_information_found(self) -> None:
        self.assertTrue(
            all(not row.correct_answer_found or row.information_found_online for row in lab.generate_trials(20))
        )

    def test_every_row_is_labeled_synthetic(self) -> None:
        self.assertTrue(
            all(row.data_classification == lab.MODEL_NOTICE for row in lab.generate_trials(10))
        )


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trials = lab.generate_trials(100, 17)
        self.summaries = lab.summarize_questions(self.trials)

    def test_summary_has_one_row_per_question(self) -> None:
        self.assertEqual(len(self.summaries), len(lab.QUESTIONS))

    def test_confusion_matrix_counts_every_participant(self) -> None:
        for row in self.summaries:
            total = (
                row["expected_yes_found_yes"]
                + row["expected_yes_found_no"]
                + row["expected_no_found_yes"]
                + row["expected_no_found_no"]
            )
            self.assertEqual(total, 100)

    def test_rates_are_bounded(self) -> None:
        rate_names = (
            "expected_online_rate",
            "found_online_rate",
            "correct_answer_found_rate",
            "unexpected_exposure_rate",
        )
        for row in self.summaries:
            for name in rate_names:
                self.assertGreaterEqual(row[name], 0)
                self.assertLessEqual(row[name], 1)

    def test_ranked_most_to_least_discoverable(self) -> None:
        rates = [row["correct_answer_found_rate"] for row in self.summaries]
        self.assertEqual(rates, sorted(rates, reverse=True))

    def test_portfolio_analysis_uses_six_questions(self) -> None:
        portfolio = lab.recovery_portfolio_risk(self.trials, self.summaries)
        self.assertEqual(len(portfolio["least_secure_questions"]), 3)
        self.assertEqual(len(portfolio["most_secure_questions"]), 3)

    def test_analysis_rejects_insufficient_input(self) -> None:
        with self.assertRaises(ValueError):
            lab.summarize_questions([])
        with self.assertRaises(ValueError):
            lab.recovery_portfolio_risk(self.trials, self.summaries[:5])


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = PROJECT_ROOT / "tests" / "output"

    def tearDown(self) -> None:
        for path in self.output_dir.glob("test-*"):
            if path.is_file():
                path.unlink()

    def test_writers_create_valid_files(self) -> None:
        trials = lab.generate_trials(10)
        summaries = lab.summarize_questions(trials)
        csv_path = self.output_dir / "test-trials.csv"
        json_path = self.output_dir / "test-summary.json"
        lab.write_trials(csv_path, trials)
        lab.write_summary(json_path, summaries, lab.recovery_portfolio_risk(trials, summaries))
        with csv_path.open(encoding="utf-8", newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), len(trials))
        self.assertEqual(
            json.loads(json_path.read_text(encoding="utf-8"))["notice"], lab.MODEL_NOTICE
        )

    def test_writer_rejects_empty_trials(self) -> None:
        with self.assertRaises(ValueError):
            lab.write_trials(self.output_dir / "test-empty.csv", [])

    def test_cli_writes_outputs_and_notice(self) -> None:
        csv_path = self.output_dir / "test-cli.csv"
        json_path = self.output_dir / "test-cli.json"
        with redirect_stdout(StringIO()) as output:
            code = lab.main(
                [
                    "experiment",
                    "--participants",
                    "10",
                    "--output",
                    str(csv_path),
                    "--summary",
                    str(json_path),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn(lab.MODEL_NOTICE, output.getvalue())
        self.assertTrue(csv_path.exists())
        self.assertTrue(json_path.exists())


if __name__ == "__main__":
    unittest.main()
