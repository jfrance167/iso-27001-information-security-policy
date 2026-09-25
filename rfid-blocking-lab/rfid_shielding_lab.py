"""Safe, reproducible model for an RFID shielding science experiment.

The generated values are simulated observations from an illustrative near-field
coupling model. They are not measurements from a physical RFID reader.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


MODEL_NOTICE = "SIMULATED DATA - NOT PHYSICAL RFID MEASUREMENTS"
DEFAULT_SEED = 20260924
DEFAULT_REPETITIONS = 10
MAX_REPETITIONS = 100
DISTANCES_CM = tuple(range(1, 16))


@dataclass(frozen=True)
class Material:
    name: str
    attenuation_db: float
    category: str


@dataclass(frozen=True)
class Tag:
    name: str
    unshielded_range_cm: float


@dataclass(frozen=True)
class Trial:
    data_classification: str
    seed: int
    tag: str
    material: str
    attenuation_db: float
    distance_cm: int
    repetition: int
    modeled_read_probability: float
    read_success: bool


MATERIALS = (
    Material("no_shield_control", 0.0, "control"),
    Material("paper", 0.2, "nonconductive control"),
    Material("aluminum_screen", 10.0, "conductive mesh"),
    Material("copper_mesh", 12.0, "conductive mesh"),
    Material("steel_sheet", 18.0, "solid metal"),
    Material("aluminum_foil", 24.0, "solid metal"),
    Material("copper_foil", 28.0, "solid metal"),
    Material("commercial_rfid_sleeve", 32.0, "commercial shield"),
)

TAGS = (
    Tag("small_key_fob", 5.0),
    Tag("id_card", 8.0),
    Tag("large_card", 11.0),
)


def effective_range_cm(tag: Tag, material: Material) -> float:
    """Return modeled read range using a near-field inverse-sixth-power model.

    For inductive coupling, power falls rapidly with distance. This classroom
    model treats received power as proportional to 1/r^6, so an attenuation of
    A dB scales maximum distance by 10^(-A/60). The material attenuation values
    are documented assumptions and must not be presented as measurements.
    """

    if tag.unshielded_range_cm <= 0:
        raise ValueError("tag range must be positive")
    if material.attenuation_db < 0:
        raise ValueError("attenuation must not be negative")
    return tag.unshielded_range_cm * 10 ** (-material.attenuation_db / 60.0)


def read_probability(distance_cm: float, tag: Tag, material: Material) -> float:
    """Return a smooth probability around the modeled maximum read range."""

    if distance_cm <= 0:
        raise ValueError("distance must be positive")
    midpoint = effective_range_cm(tag, material)
    transition_width = max(0.28, midpoint * 0.09)
    exponent = (distance_cm - midpoint) / transition_width
    if exponent >= 40:
        return 0.0
    if exponent <= -40:
        return 1.0
    return 1.0 / (1.0 + math.exp(exponent))


def run_experiment(
    repetitions: int = DEFAULT_REPETITIONS,
    seed: int = DEFAULT_SEED,
    distances_cm: Sequence[int] = DISTANCES_CM,
) -> list[Trial]:
    """Run deterministic Monte Carlo trials for every tag/material/distance."""

    if not 1 <= repetitions <= MAX_REPETITIONS:
        raise ValueError(f"repetitions must be between 1 and {MAX_REPETITIONS}")
    if not distances_cm or any(distance <= 0 for distance in distances_cm):
        raise ValueError("distances must contain positive values")

    # Seeded pseudorandomness is required for repeatable Monte Carlo data; no
    # secret, credential, or security decision is generated here.
    rng = random.Random(seed)  # nosec B311
    rows: list[Trial] = []
    for tag in TAGS:
        for material in MATERIALS:
            for distance in distances_cm:
                probability = read_probability(distance, tag, material)
                for repetition in range(1, repetitions + 1):
                    rows.append(
                        Trial(
                            data_classification=MODEL_NOTICE,
                            seed=seed,
                            tag=tag.name,
                            material=material.name,
                            attenuation_db=material.attenuation_db,
                            distance_cm=distance,
                            repetition=repetition,
                            modeled_read_probability=round(probability, 6),
                            read_success=rng.random() < probability,
                        )
                    )
    return rows


def summarize(trials: Sequence[Trial]) -> list[dict[str, object]]:
    """Aggregate trials and find farthest distance with >=80% read success."""

    if not trials:
        raise ValueError("at least one trial is required")

    groups: dict[tuple[str, str], list[Trial]] = {}
    for trial in trials:
        groups.setdefault((trial.tag, trial.material), []).append(trial)

    summary: list[dict[str, object]] = []
    for (tag_name, material_name), rows in sorted(groups.items()):
        by_distance: dict[int, list[Trial]] = {}
        for row in rows:
            by_distance.setdefault(row.distance_cm, []).append(row)
        rates = {
            distance: sum(item.read_success for item in items) / len(items)
            for distance, items in by_distance.items()
        }
        reliable = [distance for distance, rate in rates.items() if rate >= 0.8]
        material = next(item for item in MATERIALS if item.name == material_name)
        tag = next(item for item in TAGS if item.name == tag_name)
        summary.append(
            {
                "data_classification": MODEL_NOTICE,
                "tag": tag_name,
                "material": material_name,
                "category": material.category,
                "assumed_attenuation_db": material.attenuation_db,
                "modeled_effective_range_cm": round(effective_range_cm(tag, material), 3),
                "farthest_reliable_read_cm": max(reliable) if reliable else 0,
                "overall_read_success_rate": round(
                    sum(row.read_success for row in rows) / len(rows), 4
                ),
                "trial_count": len(rows),
            }
        )
    return summary


def write_results(path: Path, trials: Sequence[Trial]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(trials[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(trial) for trial in trials)


def write_summary(path: Path, summary: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "notice": MODEL_NOTICE,
        "model": "illustrative near-field inverse-sixth-power coupling model",
        "reliable_read_threshold": 0.8,
        "results": list(summary),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    experiment = subparsers.add_parser("experiment", help="generate simulated results")
    experiment.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    experiment.add_argument("--seed", type=int, default=DEFAULT_SEED)
    experiment.add_argument("--output", type=Path, default=Path("reports/results.csv"))
    experiment.add_argument("--summary", type=Path, default=Path("reports/summary.json"))
    estimate = subparsers.add_parser("estimate", help="show modeled range for one setup")
    estimate.add_argument("tag", choices=[tag.name for tag in TAGS])
    estimate.add_argument("material", choices=[material.name for material in MATERIALS])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "experiment":
        trials = run_experiment(args.repetitions, args.seed)
        result_summary = summarize(trials)
        write_results(args.output, trials)
        write_summary(args.summary, result_summary)
        print(MODEL_NOTICE)
        print(f"Wrote {len(trials)} trials to {args.output}")
        print(f"Wrote {len(result_summary)} summary rows to {args.summary}")
        return 0

    tag = next(item for item in TAGS if item.name == args.tag)
    material = next(item for item in MATERIALS if item.name == args.material)
    print(MODEL_NOTICE)
    print(f"Modeled effective range: {effective_range_cm(tag, material):.2f} cm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
