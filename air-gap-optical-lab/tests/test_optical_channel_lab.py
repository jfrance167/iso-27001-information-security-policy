from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import optical_channel_lab as lab  # noqa: E402


class ProtocolTests(unittest.TestCase):
    def test_crc_standard_vector(self) -> None:
        self.assertEqual(lab.crc8(b"123456789"), 0xF4)

    def test_bits_round_trip(self) -> None:
        value = b"\x00\x7f\x80\xff"
        self.assertEqual(lab.bits_to_bytes(lab.bytes_to_bits(value)), value)

    def test_bits_reject_invalid_values_and_length(self) -> None:
        with self.assertRaises(ValueError):
            lab.bits_to_bytes((0, 1, 0))
        with self.assertRaises(ValueError):
            lab.bits_to_bytes((0, 1, 2, 0, 0, 0, 0, 0))

    def test_packet_round_trip(self) -> None:
        payload = b"synthetic"
        self.assertEqual(lab.parse_packet(lab.build_packet(payload)), payload)

    def test_packet_rejects_corruption(self) -> None:
        packet = bytearray(lab.build_packet(b"LAB"))
        packet[2] ^= 1
        self.assertIsNone(lab.parse_packet(bytes(packet)))

    def test_packet_rejects_invalid_payload_sizes(self) -> None:
        with self.assertRaises(ValueError):
            lab.build_packet(b"")
        with self.assertRaises(ValueError):
            lab.build_packet(b"x" * 256)


class ChannelTests(unittest.TestCase):
    def test_config_validation(self) -> None:
        with self.assertRaises(ValueError):
            lab.ChannelConfig(0, 3, 5, "quiet")
        with self.assertRaises(ValueError):
            lab.ChannelConfig(1, 0, 5, "quiet")
        with self.assertRaises(ValueError):
            lab.ChannelConfig(1, 3, 0, "quiet")
        with self.assertRaises(ValueError):
            lab.ChannelConfig(1, 3, 5, "unknown")

    def test_inverse_square_attenuation(self) -> None:
        near = lab.signal_amplitude(lab.ChannelConfig(1, 3, 5, "quiet"))
        far = lab.signal_amplitude(lab.ChannelConfig(2, 3, 5, "quiet"))
        self.assertAlmostEqual(near / far, 4.0)

    def test_higher_rate_increases_noise(self) -> None:
        slow = lab.noise_sigma(lab.ChannelConfig(1, 3, 1, "quiet"))
        fast = lab.noise_sigma(lab.ChannelConfig(1, 3, 10, "quiet"))
        self.assertGreater(fast, slow)

    def test_no_noise_recovers_exact_packet(self) -> None:
        config = lab.ChannelConfig(20, 1, 10, "none")
        result = lab.run_trial(config, trial=1, seed=1)
        self.assertTrue(result.packet_recovered)
        self.assertEqual(result.bit_errors, 0)
        self.assertTrue(math.isinf(result.signal_to_noise_ratio))

    def test_transmission_is_repeatable(self) -> None:
        config = lab.ChannelConfig(6, 3, 10, "moderate")
        first = lab.run_trial(config, trial=1, seed=42)
        second = lab.run_trial(config, trial=1, seed=42)
        self.assertEqual(first, second)

    def test_near_channel_recovers_more_packets_than_far_channel(self) -> None:
        near = lab.ChannelConfig(0.5, 3, 1, "quiet")
        far = lab.ChannelConfig(9, 3, 1, "quiet")
        near_recovered = sum(
            lab.run_trial(near, trial=trial, seed=100 + trial).packet_recovered
            for trial in range(1, 11)
        )
        far_recovered = sum(
            lab.run_trial(far, trial=trial, seed=100 + trial).packet_recovered
            for trial in range(1, 11)
        )
        self.assertGreater(near_recovered, far_recovered)

    def test_visibility_bands_are_descriptive(self) -> None:
        self.assertEqual(lab.visibility_band(1), "very-low-contrast")
        self.assertEqual(lab.visibility_band(3), "low-contrast")
        self.assertEqual(lab.visibility_band(5), "higher-contrast")


class ExperimentTests(unittest.TestCase):
    def test_experiment_row_count(self) -> None:
        rows = lab.run_experiment(trials=2, seed=5)
        self.assertEqual(len(rows), 270)

    def test_experiment_rejects_nonpositive_trials(self) -> None:
        with self.assertRaises(ValueError):
            lab.run_experiment(trials=0)

    def test_summary_rates_are_bounded(self) -> None:
        summary = lab.summarize(lab.run_experiment(trials=1, seed=7))
        self.assertEqual(len(summary), 135)
        for row in summary:
            self.assertGreaterEqual(row["packet_recovery_rate"], 0.0)
            self.assertLessEqual(row["packet_recovery_rate"], 1.0)
            self.assertGreaterEqual(row["mean_bit_error_rate"], 0.0)
            self.assertLessEqual(row["mean_bit_error_rate"], 1.0)

    def test_writers_create_csv_and_json(self) -> None:
        rows = lab.run_experiment(trials=1, seed=9)
        summary = lab.summarize(rows)
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "nested" / "results.csv"
            json_path = Path(directory) / "nested" / "summary.json"
            lab.write_results(csv_path, rows)
            lab.write_summary(json_path, summary)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 135)
            self.assertEqual(len(json.loads(json_path.read_text(encoding="utf-8"))), 135)


class CommandLineTests(unittest.TestCase):
    def test_demo_command(self) -> None:
        with redirect_stdout(StringIO()) as output:
            code = lab.main(["demo", "--distance", "1", "--interference", "none"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["packet_recovered"])

    def test_experiment_command_writes_outputs(self) -> None:
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
