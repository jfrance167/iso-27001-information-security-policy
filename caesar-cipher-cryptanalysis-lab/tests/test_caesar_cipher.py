from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import caesar_cipher as cipher  # noqa: E402


class CipherTests(unittest.TestCase):
    def test_known_shift_three_example(self) -> None:
        plaintext = "THIS IS A SECRET MESSAGE"
        ciphertext = "WKLV LV D VHFUHW PHVVDJH"
        self.assertEqual(cipher.encrypt(plaintext, 3), ciphertext)
        self.assertEqual(cipher.decrypt(ciphertext, 3), plaintext)

    def test_preserves_case_numbers_punctuation_and_spaces(self) -> None:
        self.assertEqual(cipher.encrypt("Attack at 09:00!", 5), "Fyyfhp fy 09:00!")

    def test_wraparound_and_equivalent_keys(self) -> None:
        self.assertEqual(cipher.encrypt("XYZ", 3), "ABC")
        self.assertEqual(cipher.encrypt("abc", 29), "def")
        self.assertEqual(cipher.decrypt("abc", -23), "xyz")

    def test_rejects_non_integer_key(self) -> None:
        with self.assertRaises(TypeError):
            cipher.encrypt("ABC", 3.5)  # type: ignore[arg-type]

    def test_brute_force_returns_each_nonzero_key(self) -> None:
        candidates = cipher.brute_force("KHOOR")
        self.assertEqual([candidate.key for candidate in candidates], list(range(1, 26)))
        self.assertEqual(candidates[2].plaintext, "HELLO")

    def test_frequency_analysis_recovers_controlled_long_sample(self) -> None:
        plaintext = "E" * 20 + " THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
        ciphertext = cipher.encrypt(plaintext, 11)
        result = cipher.frequency_analysis(ciphertext)
        self.assertEqual(result.key, 11)
        self.assertEqual(result.plaintext, plaintext)

    def test_frequency_analysis_rejects_text_without_letters(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            cipher.frequency_analysis("123 !?")

    def test_ranker_places_long_english_sample_first(self) -> None:
        plaintext = (
            "The Caesar cipher shifts every letter by the same key. Longer English "
            "messages provide a more stable frequency distribution for analysis."
        )
        ranked = cipher.rank_candidates(cipher.encrypt(plaintext, 14))
        self.assertEqual(ranked[0].key, 14)
        self.assertEqual(ranked[0].plaintext, plaintext)


class CommandLineTests(unittest.TestCase):
    def test_file_encrypt_and_decrypt_round_trip(self) -> None:
        source = PROJECT_ROOT / "tests" / ".round-trip-plain.txt"
        encrypted = PROJECT_ROOT / "tests" / ".round-trip-cipher.txt"
        recovered = PROJECT_ROOT / "tests" / ".round-trip-recovered.txt"
        try:
            source.write_text("Meet me at 5:30.", encoding="utf-8")

            with redirect_stdout(StringIO()):
                self.assertEqual(cipher.main(["encrypt", str(source), str(encrypted), "--key", "8"]), 0)
                self.assertEqual(cipher.main(["decrypt", str(encrypted), str(recovered), "--key", "8"]), 0)

            self.assertEqual(recovered.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
        finally:
            source.unlink(missing_ok=True)
            encrypted.unlink(missing_ok=True)
            recovered.unlink(missing_ok=True)

    def test_brute_force_json_report_has_25_candidates(self) -> None:
        source = PROJECT_ROOT / "tests" / ".brute-force-cipher.txt"
        report = PROJECT_ROOT / "tests" / ".brute-force-report.json"
        try:
            source.write_text("KHOOR", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(cipher.main(["brute-force", str(source), "--output", str(report)]), 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 25)
            self.assertEqual(data[2]["plaintext"], "HELLO")
        finally:
            source.unlink(missing_ok=True)
            report.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
