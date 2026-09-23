from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import password_lab as lab  # noqa: E402


def record(password: str) -> lab.PasswordRecord:
    return lab.make_record(password, salt=b"unit-test-salt", iterations=10)


class SearchSpaceTests(unittest.TestCase):
    def test_three_digit_lock_has_one_thousand_combinations(self) -> None:
        self.assertEqual(lab.search_space(10, 3), 1_000)

    def test_eight_character_alphanumeric_value_matches_project(self) -> None:
        self.assertEqual(lab.search_space(62, 8), 218_340_105_584_896)

    def test_search_space_rejects_nonpositive_inputs(self) -> None:
        with self.assertRaises(ValueError):
            lab.search_space(0, 3)
        with self.assertRaises(ValueError):
            lab.search_space(10, 0)

    def test_table_has_three_alphabets_and_eight_lengths(self) -> None:
        rows = lab.build_search_space_rows()
        self.assertEqual(len(rows), 24)
        self.assertEqual(rows[-1].alphabet_size, 62)
        self.assertEqual(rows[-1].length, 8)

    def test_human_duration(self) -> None:
        self.assertEqual(lab.human_duration(100), "1.67 minutes")
        self.assertEqual(lab.human_duration(3_600), "1 hours")


class VerifierTests(unittest.TestCase):
    def test_pbkdf2_record_verifies_only_correct_password(self) -> None:
        target = record("synthetic-only")
        self.assertTrue(lab.verify_guess(target, "synthetic-only"))
        self.assertFalse(lab.verify_guess(target, "different"))

    def test_record_requires_salt_and_password(self) -> None:
        with self.assertRaises(ValueError):
            lab.make_record("", salt=b"long-enough", iterations=10)
        with self.assertRaises(ValueError):
            lab.make_record("value", salt=b"bad", iterations=10)


class AttackTests(unittest.TestCase):
    def test_numeric_brute_force_preserves_leading_zeros(self) -> None:
        result = lab.numeric_brute_force(record("007"), length=3)
        self.assertTrue(result.found)
        self.assertEqual(result.password, "007")
        self.assertEqual(result.guesses, 8)

    def test_alphanumeric_brute_force_finds_short_value(self) -> None:
        result = lab.alphanumeric_brute_force(record("b0"), max_length=2)
        self.assertTrue(result.found)
        self.assertEqual(result.password, "b0")

    def test_dictionary_attack_tries_case_variants(self) -> None:
        result = lab.dictionary_attack(record("Sunshine"), ["password", "sunshine"])
        self.assertTrue(result.found)
        self.assertEqual(result.password, "Sunshine")

    def test_combined_attack_joins_distinct_words(self) -> None:
        result = lab.combined_word_attack(
            record("red+planet"), ["red", "planet"], separators=["+"]
        )
        self.assertTrue(result.found)
        self.assertEqual(result.password, "red+planet")

    def test_guess_limit_stops_search(self) -> None:
        result = lab.numeric_brute_force(record("999"), length=3, max_guesses=10)
        self.assertFalse(result.found)
        self.assertTrue(result.stopped_by_limit)
        self.assertEqual(result.guesses, 10)

    def test_exhausted_dictionary_is_reported(self) -> None:
        result = lab.dictionary_attack(record("not-listed"), ["red", "blue"])
        self.assertFalse(result.found)
        self.assertFalse(result.stopped_by_limit)


class CommandLineTests(unittest.TestCase):
    def test_estimate_command(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(lab.main(["estimate", "10", "4"]), 0)
        self.assertIn("10,000", output.getvalue())

    def test_demo_json_finds_all_synthetic_passwords(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(lab.main(["demo", "--iterations", "1", "--json"]), 0)
        results = json.loads(output.getvalue())
        self.assertEqual(len(results), 4)
        self.assertTrue(all(item["found"] for item in results))


if __name__ == "__main__":
    unittest.main()
