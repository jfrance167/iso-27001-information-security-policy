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

import password_reuse_lab as lab  # noqa: E402


class GenerationTests(unittest.TestCase):
    def test_generation_is_reproducible(self) -> None:
        self.assertEqual(lab.generate_responses(20, 7), lab.generate_responses(20, 7))

    def test_different_seed_changes_responses(self) -> None:
        self.assertNotEqual(lab.generate_responses(20, 7), lab.generate_responses(20, 8))

    def test_minimum_respondent_count_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            lab.generate_responses(lab.MIN_RESPONDENTS - 1)

    def test_maximum_respondent_count_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            lab.generate_responses(lab.MAX_RESPONDENTS + 1)

    def test_every_respondent_has_at_least_two_accounts(self) -> None:
        rows = lab.generate_responses(20)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.respondent_id] = counts.get(row.respondent_id, 0) + 1
        self.assertTrue(all(count >= 2 for count in counts.values()))

    def test_data_is_always_labeled_synthetic(self) -> None:
        self.assertTrue(
            all(row.data_classification == lab.MODEL_NOTICE for row in lab.generate_responses(20))
        )

    def test_reuse_labels_are_opaque(self) -> None:
        rows = lab.generate_responses(20)
        self.assertTrue(all(row.reuse_group.startswith("G") for row in rows))
        self.assertTrue(all("password" not in row.reuse_group.lower() for row in rows))


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.responses = lab.generate_responses(40, 19)
        self.metrics = lab.respondent_metrics(self.responses)

    def test_one_metric_per_respondent(self) -> None:
        self.assertEqual(len(self.metrics), 40)

    def test_normalized_metrics_are_bounded(self) -> None:
        for metric in self.metrics:
            self.assertGreater(metric.normalized_password_diversity, 0)
            self.assertLessEqual(metric.normalized_password_diversity, 1)
            self.assertGreaterEqual(metric.reused_account_pair_rate, 0)
            self.assertLessEqual(metric.reused_account_pair_rate, 1)

    def test_exposure_cascade_is_valid(self) -> None:
        for metric in self.metrics:
            self.assertGreaterEqual(metric.largest_exposure_cascade, 1)
            self.assertLessEqual(metric.largest_exposure_cascade, metric.account_count)

    def test_category_summary_covers_all_categories(self) -> None:
        categories = lab.category_summary(self.responses)
        self.assertEqual(
            {row["category"] for row in categories},
            {account.category for account in lab.ACCOUNTS},
        )

    def test_category_counts_sum_to_eligible(self) -> None:
        for row in lab.category_summary(self.responses):
            self.assertEqual(
                row["eligible_respondents"],
                row["all_same_count"] + row["all_different_count"] + row["mixed_count"],
            )

    def test_overall_summary_has_expected_count(self) -> None:
        self.assertEqual(lab.overall_summary(self.metrics)["respondent_count"], 40)

    def test_histogram_counts_every_respondent(self) -> None:
        histogram = lab.distinct_group_histogram(self.metrics)
        self.assertEqual(sum(row["respondent_count"] for row in histogram), 40)

    def test_analysis_rejects_empty_inputs(self) -> None:
        with self.assertRaises(ValueError):
            lab.respondent_metrics([])
        with self.assertRaises(ValueError):
            lab.category_summary([])
        with self.assertRaises(ValueError):
            lab.overall_summary([])
        with self.assertRaises(ValueError):
            lab.distinct_group_histogram([])


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = PROJECT_ROOT / "tests" / "output"

    def tearDown(self) -> None:
        for path in self.output_dir.glob("test-*"):
            if path.is_file():
                path.unlink()

    def test_csv_and_json_writers(self) -> None:
        responses = lab.generate_responses(20)
        metrics = lab.respondent_metrics(responses)
        responses_path = self.output_dir / "test-responses.csv"
        summary_path = self.output_dir / "test-summary.json"
        lab.write_csv(responses_path, responses)
        lab.write_summary(
            summary_path,
            lab.overall_summary(metrics),
            lab.category_summary(responses),
            lab.distinct_group_histogram(metrics),
        )
        with responses_path.open(encoding="utf-8", newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), len(responses))
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["notice"], lab.MODEL_NOTICE)

    def test_writer_rejects_empty_rows(self) -> None:
        with self.assertRaises(ValueError):
            lab.write_csv(self.output_dir / "test-empty.csv", [])

    def test_cli_writes_all_outputs_and_notice(self) -> None:
        responses = self.output_dir / "test-cli-responses.csv"
        metrics = self.output_dir / "test-cli-metrics.csv"
        summary = self.output_dir / "test-cli-summary.json"
        with redirect_stdout(StringIO()) as output:
            code = lab.main(
                [
                    "experiment",
                    "--respondents",
                    "20",
                    "--responses",
                    str(responses),
                    "--metrics",
                    str(metrics),
                    "--summary",
                    str(summary),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn(lab.MODEL_NOTICE, output.getvalue())
        self.assertTrue(responses.exists())
        self.assertTrue(metrics.exists())
        self.assertTrue(summary.exists())


if __name__ == "__main__":
    unittest.main()
