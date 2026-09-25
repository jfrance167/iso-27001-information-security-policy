"""Synthetic security-question discoverability experiment.

The program never searches for people, stores recovery answers, or accesses an
account. All profiles and outcomes are generated locally for method validation.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


MODEL_NOTICE = "SYNTHETIC DATA - NO REAL PEOPLE OR RECOVERY ANSWERS"
DEFAULT_SEED = 20260925
DEFAULT_PARTICIPANTS = 200
MIN_PARTICIPANTS = 10
MAX_PARTICIPANTS = 2000


@dataclass(frozen=True)
class QuestionModel:
    name: str
    public_probability: float
    expected_public_probability: float
    correctness_if_found: float


@dataclass(frozen=True)
class Trial:
    data_classification: str
    participant_id: str
    question: str
    expected_online: bool
    information_found_online: bool
    correct_answer_found: bool


QUESTIONS = (
    QuestionModel("current_employer", 0.82, 0.68, 0.94),
    QuestionModel("high_school", 0.72, 0.52, 0.90),
    QuestionModel("birth_city", 0.65, 0.48, 0.88),
    QuestionModel("mothers_maiden_name", 0.46, 0.22, 0.84),
    QuestionModel("first_pet_name", 0.41, 0.20, 0.76),
    QuestionModel("wedding_location", 0.36, 0.28, 0.84),
    QuestionModel("street_grew_up_on", 0.30, 0.16, 0.78),
    QuestionModel("first_car_model", 0.27, 0.18, 0.71),
    QuestionModel("favorite_sports_team", 0.34, 0.27, 0.68),
    QuestionModel("favorite_food", 0.20, 0.13, 0.52),
)


def _validate_probability(value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError("probabilities must be between 0 and 1")


def generate_trials(
    participant_count: int = DEFAULT_PARTICIPANTS,
    seed: int = DEFAULT_SEED,
    questions: Sequence[QuestionModel] = QUESTIONS,
) -> list[Trial]:
    """Generate deterministic fictional observations for every question."""

    if not MIN_PARTICIPANTS <= participant_count <= MAX_PARTICIPANTS:
        raise ValueError(
            f"participant_count must be between {MIN_PARTICIPANTS} and {MAX_PARTICIPANTS}"
        )
    if not questions:
        raise ValueError("at least one question is required")
    for question in questions:
        _validate_probability(question.public_probability)
        _validate_probability(question.expected_public_probability)
        _validate_probability(question.correctness_if_found)

    # Seeded pseudorandomness provides repeatable classroom data, not secrets.
    rng = random.Random(seed)  # nosec B311
    trials: list[Trial] = []
    for participant_number in range(1, participant_count + 1):
        participant_id = f"F{participant_number:04d}"
        for question in questions:
            expected = rng.random() < question.expected_public_probability
            found = rng.random() < question.public_probability
            correct = found and rng.random() < question.correctness_if_found
            trials.append(
                Trial(
                    data_classification=MODEL_NOTICE,
                    participant_id=participant_id,
                    question=question.name,
                    expected_online=expected,
                    information_found_online=found,
                    correct_answer_found=correct,
                )
            )
    return trials


def summarize_questions(trials: Sequence[Trial]) -> list[dict[str, object]]:
    if not trials:
        raise ValueError("at least one trial is required")
    grouped: dict[str, list[Trial]] = {}
    for trial in trials:
        grouped.setdefault(trial.question, []).append(trial)

    results: list[dict[str, object]] = []
    for question, rows in grouped.items():
        count = len(rows)
        expected_yes_found_yes = sum(
            row.expected_online and row.information_found_online for row in rows
        )
        expected_yes_found_no = sum(
            row.expected_online and not row.information_found_online for row in rows
        )
        expected_no_found_yes = sum(
            not row.expected_online and row.information_found_online for row in rows
        )
        expected_no_found_no = sum(
            not row.expected_online and not row.information_found_online for row in rows
        )
        expected_rate = sum(row.expected_online for row in rows) / count
        found_rate = sum(row.information_found_online for row in rows) / count
        correct_rate = sum(row.correct_answer_found for row in rows) / count
        results.append(
            {
                "data_classification": MODEL_NOTICE,
                "question": question,
                "participant_count": count,
                "expected_yes_found_yes": expected_yes_found_yes,
                "expected_yes_found_no": expected_yes_found_no,
                "expected_no_found_yes": expected_no_found_yes,
                "expected_no_found_no": expected_no_found_no,
                "expected_online_rate": round(expected_rate, 4),
                "found_online_rate": round(found_rate, 4),
                "correct_answer_found_rate": round(correct_rate, 4),
                "unexpected_exposure_rate": round(expected_no_found_yes / count, 4),
                "expectation_gap": round(found_rate - expected_rate, 4),
            }
        )
    return sorted(results, key=lambda item: (-item["correct_answer_found_rate"], item["question"]))


def recovery_portfolio_risk(
    trials: Sequence[Trial], summaries: Sequence[dict[str, object]]
) -> dict[str, object]:
    """Model all-three-known risk for the three least/most secure questions."""

    if not trials or len(summaries) < 6:
        raise ValueError("portfolio analysis requires trials and at least six questions")
    least_secure = [str(row["question"]) for row in summaries[:3]]
    most_secure = [str(row["question"]) for row in summaries[-3:]]
    by_participant: dict[str, dict[str, bool]] = {}
    for trial in trials:
        by_participant.setdefault(trial.participant_id, {})[trial.question] = (
            trial.correct_answer_found
        )

    def all_known_rate(question_names: Sequence[str]) -> float:
        successes = sum(
            all(question_map.get(name, False) for name in question_names)
            for question_map in by_participant.values()
        )
        return successes / len(by_participant)

    return {
        "data_classification": MODEL_NOTICE,
        "participant_count": len(by_participant),
        "least_secure_questions": least_secure,
        "least_secure_all_three_known_rate": round(all_known_rate(least_secure), 4),
        "most_secure_questions": most_secure,
        "most_secure_all_three_known_rate": round(all_known_rate(most_secure), 4),
        "warning": "Illustrative exposure metric only; no authentication was attempted.",
    }


def write_trials(path: Path, trials: Sequence[Trial]) -> None:
    if not trials:
        raise ValueError("at least one trial is required")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(trials[0])))
        writer.writeheader()
        writer.writerows(asdict(trial) for trial in trials)


def write_summary(
    path: Path,
    summaries: Sequence[dict[str, object]],
    portfolio: dict[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "notice": MODEL_NOTICE,
        "method": "deterministic fictional-profile simulation; no OSINT performed",
        "question_rankings": list(summaries),
        "recovery_portfolio_risk": portfolio,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    experiment = subparsers.add_parser("experiment", help="run the synthetic experiment")
    experiment.add_argument("--participants", type=int, default=DEFAULT_PARTICIPANTS)
    experiment.add_argument("--seed", type=int, default=DEFAULT_SEED)
    experiment.add_argument("--output", type=Path, default=Path("reports/trials.csv"))
    experiment.add_argument("--summary", type=Path, default=Path("reports/summary.json"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    trials = generate_trials(args.participants, args.seed)
    summaries = summarize_questions(trials)
    portfolio = recovery_portfolio_risk(trials, summaries)
    write_trials(args.output, trials)
    write_summary(args.summary, summaries, portfolio)
    print(MODEL_NOTICE)
    print(f"Wrote {len(trials)} fictional observations for {args.participants} profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
