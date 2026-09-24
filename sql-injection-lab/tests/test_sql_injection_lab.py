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

import sql_injection_lab as lab  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.users = lab.make_synthetic_users(5, seed=7)
        self.connection = lab.create_database(self.users)

    def tearDown(self) -> None:
        self.connection.close()

    def test_users_are_deterministic(self) -> None:
        self.assertEqual(self.users, lab.make_synthetic_users(5, seed=7))

    def test_users_change_with_seed(self) -> None:
        self.assertNotEqual(self.users[0].password, lab.make_synthetic_users(5, seed=8)[0].password)

    def test_user_count_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            lab.make_synthetic_users(0)
        with self.assertRaises(ValueError):
            lab.make_synthetic_users(lab.MAX_USERS + 1)

    def test_database_contains_only_requested_users(self) -> None:
        count = self.connection.execute(lab.COUNT_QUERY).fetchone()[0]
        self.assertEqual(count, len(self.users))

    def test_secure_login_accepts_valid_credentials(self) -> None:
        user = self.users[2]
        self.assertEqual(
            lab.secure_login(self.connection, user.username, user.password), user.username
        )

    def test_secure_login_rejects_wrong_password(self) -> None:
        user = self.users[2]
        self.assertIsNone(lab.secure_login(self.connection, user.username, "wrong"))

    def test_secure_login_treats_injection_as_literal_data(self) -> None:
        self.assertIsNone(lab.secure_login(self.connection, "' OR '1'='1' --", "unused"))

    def test_secure_search_treats_union_as_literal_data(self) -> None:
        rows = lab.secure_search(
            self.connection, "' UNION SELECT username, email FROM users --"
        )
        self.assertEqual(rows, ())

    def test_legacy_plan_is_never_executed(self) -> None:
        attempt = lab._attempt_for(self.users[0], "username_tautology")
        plan = lab.legacy_query_plan(attempt)
        self.assertFalse(plan["executed"])
        self.assertEqual(plan["binding_strategy"], "legacy string interpolation (modeled only)")


class TrialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.users = lab.make_synthetic_users(3, seed=11)
        self.connection = lab.create_database(self.users)

    def tearDown(self) -> None:
        self.connection.close()

    def test_valid_credentials_succeed_in_both_paths(self) -> None:
        result = lab.run_trial(self.connection, self.users[0], "valid_credentials", 1, 3)
        self.assertTrue(result.legacy_authenticated)
        self.assertTrue(result.secure_authenticated)
        self.assertFalse(result.secure_unauthorized_access)

    def test_wrong_password_fails_in_both_paths(self) -> None:
        result = lab.run_trial(self.connection, self.users[0], "wrong_password", 1, 3)
        self.assertFalse(result.legacy_authenticated)
        self.assertFalse(result.secure_authenticated)

    def test_modeled_tautology_bypasses_only_legacy_path(self) -> None:
        result = lab.run_trial(self.connection, self.users[0], "username_tautology", 1, 3)
        self.assertTrue(result.legacy_unauthorized_access)
        self.assertFalse(result.secure_unauthorized_access)

    def test_modeled_union_exposes_only_legacy_rows(self) -> None:
        result = lab.run_trial(self.connection, self.users[0], "union_exposure", 1, 3)
        self.assertEqual(result.legacy_rows_exposed, 3)
        self.assertEqual(result.secure_rows_exposed, 0)

    def test_every_scenario_preserves_database(self) -> None:
        for scenario in lab.SCENARIOS:
            result = lab.run_trial(self.connection, self.users[0], scenario, 1, 3)
            self.assertTrue(result.database_intact)
        self.assertEqual(self.connection.execute(lab.COUNT_QUERY).fetchone()[0], 3)

    def test_unknown_scenario_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_trial(self.connection, self.users[0], "unknown", 1, 3)

    def test_nonpositive_repetition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_trial(self.connection, self.users[0], "valid_credentials", 0, 3)


class ExperimentTests(unittest.TestCase):
    def test_experiment_has_expected_row_count(self) -> None:
        rows = lab.run_experiment(user_count=5, repetitions=2, seed=13)
        self.assertEqual(len(rows), len(lab.SCENARIOS) * 5 * 2)

    def test_experiment_is_reproducible(self) -> None:
        self.assertEqual(
            lab.run_experiment(user_count=2, repetitions=1, seed=17),
            lab.run_experiment(user_count=2, repetitions=1, seed=17),
        )

    def test_experiment_rejects_nonpositive_repetitions(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_experiment(repetitions=0)

    def test_summary_shows_parameterization_blocks_unauthorized_access(self) -> None:
        summary = {row["scenario"]: row for row in lab.summarize(lab.run_experiment(3, 1))}
        self.assertEqual(summary["username_tautology"]["legacy_unauthorized_access_rate"], 1.0)
        self.assertEqual(summary["username_tautology"]["secure_unauthorized_access_rate"], 0.0)
        self.assertEqual(summary["union_exposure"]["legacy_mean_rows_exposed"], 3.0)
        self.assertEqual(summary["union_exposure"]["secure_mean_rows_exposed"], 0.0)

    def test_writers_create_csv_and_json(self) -> None:
        rows = lab.run_experiment(2, 1)
        summary = lab.summarize(rows)
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "nested" / "results.csv"
            json_path = Path(directory) / "nested" / "summary.json"
            lab.write_results(csv_path, rows)
            lab.write_summary(json_path, summary)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), len(rows))
            self.assertEqual(len(json.loads(json_path.read_text(encoding="utf-8"))), 6)


class CommandLineTests(unittest.TestCase):
    def test_demo_output_contains_no_raw_password(self) -> None:
        user = lab.make_synthetic_users(1)[0]
        with redirect_stdout(StringIO()) as output:
            code = lab.main(["demo", "--scenario", "username_tautology"])
        self.assertEqual(code, 0)
        self.assertNotIn(user.password, output.getvalue())

    def test_experiment_command_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / "results.csv"
            summary = Path(directory) / "summary.json"
            with redirect_stdout(StringIO()):
                code = lab.main(
                    [
                        "experiment",
                        "--users",
                        "2",
                        "--repetitions",
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
