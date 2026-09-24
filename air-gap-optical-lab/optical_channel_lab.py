"""Safe, deterministic model of a screen-brightness air-gap channel.

The module never changes a real display, captures a camera, accesses a network,
or reads user data. It transmits a synthetic packet through a mathematical
optical-channel model so distance, contrast, bit rate, and interference can be
studied reproducibly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


PREAMBLE = 0xD5
CRC_POLYNOMIAL = 0x07
DEFAULT_PAYLOAD = b"LAB"
DISTANCES_METERS = (0.5, 1.5, 3.0, 6.0, 9.0)
CONTRAST_LEVELS_PERCENT = (1.0, 3.0, 5.0)
BIT_RATES_BPS = (1.0, 5.0, 10.0)
INTERFERENCE_SIGMA = {
    "none": 0.0,
    "quiet": 0.04,
    "moderate": 0.10,
    "high": 0.20,
}
EXPERIMENT_INTERFERENCE = ("quiet", "moderate", "high")


@dataclass(frozen=True)
class ChannelConfig:
    distance_m: float
    contrast_percent: float
    bit_rate_bps: float
    interference: str

    def __post_init__(self) -> None:
        if self.distance_m <= 0:
            raise ValueError("distance_m must be positive")
        if not 0 < self.contrast_percent <= 100:
            raise ValueError("contrast_percent must be in (0, 100]")
        if self.bit_rate_bps <= 0:
            raise ValueError("bit_rate_bps must be positive")
        if self.interference not in INTERFERENCE_SIGMA:
            raise ValueError(f"unknown interference level: {self.interference}")


@dataclass(frozen=True)
class TrialResult:
    trial: int
    distance_m: float
    contrast_percent: float
    bit_rate_bps: float
    interference: str
    signal_amplitude: float
    noise_sigma: float
    signal_to_noise_ratio: float
    total_bits: int
    bit_errors: int
    bit_error_rate: float
    packet_recovered: bool
    visibility_band: str


def crc8(data: bytes) -> int:
    """Return CRC-8/ATM (polynomial 0x07, initial value 0)."""
    value = 0
    for byte in data:
        value ^= byte
        for _ in range(8):
            if value & 0x80:
                value = ((value << 1) ^ CRC_POLYNOMIAL) & 0xFF
            else:
                value = (value << 1) & 0xFF
    return value


def bytes_to_bits(data: bytes) -> tuple[int, ...]:
    return tuple((byte >> shift) & 1 for byte in data for shift in range(7, -1, -1))


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    if len(bits) % 8:
        raise ValueError("bit count must be divisible by eight")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("bits must contain only zero or one")
    output = bytearray()
    for offset in range(0, len(bits), 8):
        value = 0
        for bit in bits[offset : offset + 8]:
            value = (value << 1) | bit
        output.append(value)
    return bytes(output)


def build_packet(payload: bytes) -> bytes:
    if not payload:
        raise ValueError("payload must not be empty")
    if len(payload) > 255:
        raise ValueError("payload must be at most 255 bytes")
    body = bytes((PREAMBLE, len(payload))) + payload
    return body + bytes((crc8(body),))


def parse_packet(packet: bytes) -> bytes | None:
    if len(packet) < 4 or packet[0] != PREAMBLE:
        return None
    payload_size = packet[1]
    expected_size = payload_size + 3
    if len(packet) != expected_size:
        return None
    if crc8(packet[:-1]) != packet[-1]:
        return None
    return packet[2:-1]


def _normal_sample(seed: int, sample_index: int) -> float:
    """Generate a deterministic standard-normal sample from SHA-256 bytes."""
    digest = hashlib.sha256(f"{seed}:{sample_index}".encode("ascii")).digest()
    scale = float(1 << 64)
    first = (int.from_bytes(digest[:8], "big") + 0.5) / scale
    second = (int.from_bytes(digest[8:16], "big") + 0.5) / scale
    return math.sqrt(-2.0 * math.log(first)) * math.cos(2.0 * math.pi * second)


def signal_amplitude(config: ChannelConfig) -> float:
    """Model inverse-square optical attenuation in arbitrary sensor units."""
    return config.contrast_percent / (config.distance_m**2)


def noise_sigma(config: ChannelConfig) -> float:
    """Model shorter exposure at higher bit rates as increased sensor noise."""
    return INTERFERENCE_SIGMA[config.interference] * math.sqrt(config.bit_rate_bps / 5.0)


def visibility_band(contrast_percent: float) -> str:
    """Return a descriptive model band, not a human-subject measurement."""
    if contrast_percent <= 1.0:
        return "very-low-contrast"
    if contrast_percent <= 3.0:
        return "low-contrast"
    return "higher-contrast"


def transmit_bits(bits: Sequence[int], config: ChannelConfig, *, seed: int) -> tuple[int, ...]:
    amplitude = signal_amplitude(config)
    sigma = noise_sigma(config)
    received: list[int] = []
    for sample_index, bit in enumerate(bits):
        centered_signal = amplitude / 2.0 if bit else -amplitude / 2.0
        measurement = centered_signal
        if sigma:
            measurement += sigma * _normal_sample(seed, sample_index)
        received.append(int(measurement >= 0.0))
    return tuple(received)


def run_trial(
    config: ChannelConfig,
    *,
    trial: int,
    seed: int,
    payload: bytes = DEFAULT_PAYLOAD,
) -> TrialResult:
    packet = build_packet(payload)
    sent_bits = bytes_to_bits(packet)
    received_bits = transmit_bits(sent_bits, config, seed=seed)
    errors = sum(sent != received for sent, received in zip(sent_bits, received_bits, strict=True))
    recovered_packet = bits_to_bytes(received_bits)
    recovered_payload = parse_packet(recovered_packet)
    sigma = noise_sigma(config)
    amplitude = signal_amplitude(config)
    ratio = math.inf if sigma == 0 else amplitude / sigma
    return TrialResult(
        trial=trial,
        distance_m=config.distance_m,
        contrast_percent=config.contrast_percent,
        bit_rate_bps=config.bit_rate_bps,
        interference=config.interference,
        signal_amplitude=amplitude,
        noise_sigma=sigma,
        signal_to_noise_ratio=ratio,
        total_bits=len(sent_bits),
        bit_errors=errors,
        bit_error_rate=errors / len(sent_bits),
        packet_recovered=recovered_payload == payload,
        visibility_band=visibility_band(config.contrast_percent),
    )


def run_experiment(*, trials: int = 10, seed: int = 20260923) -> list[TrialResult]:
    if trials < 1:
        raise ValueError("trials must be positive")
    rows: list[TrialResult] = []
    scenario = 0
    for distance in DISTANCES_METERS:
        for contrast in CONTRAST_LEVELS_PERCENT:
            for bit_rate in BIT_RATES_BPS:
                for interference in EXPERIMENT_INTERFERENCE:
                    config = ChannelConfig(distance, contrast, bit_rate, interference)
                    scenario += 1
                    for trial in range(1, trials + 1):
                        rows.append(
                            run_trial(
                                config,
                                trial=trial,
                                seed=seed + scenario * 10_000 + trial,
                            )
                        )
    return rows


def summarize(results: Iterable[TrialResult]) -> list[dict[str, object]]:
    groups: dict[tuple[float, float, float, str], list[TrialResult]] = {}
    for result in results:
        key = (result.distance_m, result.contrast_percent, result.bit_rate_bps, result.interference)
        groups.setdefault(key, []).append(result)
    summary: list[dict[str, object]] = []
    for key in sorted(groups, key=lambda item: (item[0], item[1], item[2], item[3])):
        rows = groups[key]
        recovered = sum(row.packet_recovered for row in rows)
        summary.append(
            {
                "distance_m": key[0],
                "contrast_percent": key[1],
                "bit_rate_bps": key[2],
                "interference": key[3],
                "trials": len(rows),
                "packet_recovery_rate": recovered / len(rows),
                "mean_bit_error_rate": sum(row.bit_error_rate for row in rows) / len(rows),
                "mean_signal_to_noise_ratio": sum(row.signal_to_noise_ratio for row in rows) / len(rows),
                "visibility_band": rows[0].visibility_band,
            }
        )
    return summary


def write_results(path: str | Path, results: Sequence[TrialResult]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(TrialResult.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def write_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe optical air-gap channel simulation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    experiment = subparsers.add_parser("experiment", help="Run the completed factorial experiment.")
    experiment.add_argument("--trials", type=int, default=10)
    experiment.add_argument("--seed", type=int, default=20260923)
    experiment.add_argument("--output", default="reports/results.csv")
    experiment.add_argument("--summary", default="reports/summary.json")

    demo = subparsers.add_parser("demo", help="Transmit the synthetic LAB packet once.")
    demo.add_argument("--distance", type=float, default=3.0)
    demo.add_argument("--contrast", type=float, default=3.0)
    demo.add_argument("--bit-rate", type=float, default=5.0)
    demo.add_argument("--interference", choices=tuple(INTERFERENCE_SIGMA), default="quiet")
    demo.add_argument("--seed", type=int, default=20260923)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        config = ChannelConfig(args.distance, args.contrast, args.bit_rate, args.interference)
        print(json.dumps(asdict(run_trial(config, trial=1, seed=args.seed)), indent=2))
        return 0

    if args.trials < 1:
        raise SystemExit("--trials must be positive")
    results = run_experiment(trials=args.trials, seed=args.seed)
    summary_rows = summarize(results)
    write_results(args.output, results)
    write_summary(args.summary, summary_rows)
    print(f"Wrote {len(results)} trials and {len(summary_rows)} grouped scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
