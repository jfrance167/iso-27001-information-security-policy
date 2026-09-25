"""Privacy-safe simulation and analysis of password reuse across accounts.

No real passwords, account names, usernames, or human responses are collected.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Sequence


MODEL_NOTICE = "SYNTHETIC SURVEY DATA - NO HUMAN PASSWORDS OR RESPONSES"
DEFAULT_SEED = 20260925
DEFAULT_RESPONDENTS = 120
MIN_RESPONDENTS = 20
MAX_RESPONDENTS = 1000


@dataclass(frozen=True)
class Account:
    name: str
    category: str
    ownership_probability: float


@dataclass(frozen=True)
class Response:
    data_classification: str
    respondent_id: str
    synthetic_profile: str
    account: str
    category: str
    reuse_group: str


@dataclass(frozen=True)
class RespondentMetric:
    data_classification: str
    respondent_id: str
    synthetic_profile: str
    account_count: int
    distinct_password_groups: int
    normalized_password_diversity: float
    reused_account_pair_rate: float
    largest_exposure_cascade: int


ACCOUNTS = (
    Account("personal_email", "email", 0.96),
    Account("secondary_email", "email", 0.62),
    Account("school_or_work_email", "work_school", 0.82),
    Account("school_or_work_portal", "work_school", 0.88),
    Account("cloud_productivity", "work_school", 0.78),
    Account("banking", "finance", 0.74),
    Account("payment_service", "finance", 0.68),
    Account("shopping_primary", "shopping", 0.91),
    Account("shopping_secondary", "shopping", 0.57),
    Account("social_primary", "social", 0.86),
    Account("social_secondary", "social", 0.70),
    Account("messaging", "social", 0.89),
    Account("gaming", "entertainment", 0.66),
    Account("music_streaming", "entertainment", 0.76),
    Account("video_streaming", "entertainment", 0.84),
    Account("computer_login", "device", 0.83),
    Account("phone_or_tablet", "device", 0.94),
)

PROFILE_WEIGHTS = (
    ("low_reuse", 0.42, 0.15),
    ("moderate_reuse", 0.38, 0.45),
    ("high_reuse", 0.20, 0.75),
)


def _choose_profile(rng: random.Random) -> tuple[str, float]:  # nosec B311
    draw = rng.random()
    cumulative = 0.0
    for name, weight, reuse_probability in PROFILE_WEIGHTS:
        cumulative += weight
        if draw <= cumulative:
            return name, reuse_probability
    return PROFILE_WEIGHTS[-1][0], PROFILE_WEIGHTS[-1][2]


def _owned_accounts(rng: random.Random) -> list[Account]:  # nosec B311
    owned = [account for account in ACCOUNTS if rng.random() < account.ownership_probability]
    if len(owned) < 2:
        return list(ACCOUNTS[:2])
    return owned


def generate_responses(
    respondent_count: int = DEFAULT_RESPONDENTS,
    seed: int = DEFAULT_SEED,
) -> list[Response]:
    """Generate deterministic synthetic survey responses with opaque labels."""

    if not MIN_RESPONDENTS <= respondent_count <= MAX_RESPONDENTS:
        raise ValueError(
            f"respondent_count must be between {MIN_RESPONDENTS} and {MAX_RESPONDENTS}"
        )

    # Deterministic Monte Carlo sampling; never used for credentials or secrets.
    rng = random.Random(seed)  # nosec B311
    rows: list[Response] = []
    for index in range(1, respondent_count + 1):
        respondent_id = f"S{index:04d}"
        profile, reuse_probability = _choose_profile(rng)
        owned = _owned_accounts(rng)
        groups: list[tuple[str, str]] = []
        next_group = 1
        for account in owned:
            reuse = bool(groups) and rng.random() < reuse_probability
            if reuse:
                same_category = [group for group in groups if group[1] == account.category]
                candidates = same_category if same_category and rng.random() < 0.70 else groups
                reuse_group = rng.choice(candidates)[0]
            else:
                reuse_group = f"G{next_group:02d}"
                next_group += 1
            groups.append((reuse_group, account.category))
            rows.append(
                Response(
                    data_classification=MODEL_NOTICE,
                    respondent_id=respondent_id,
                    synthetic_profile=profile,
                    account=account.name,
                    category=account.category,
                    reuse_group=reuse_group,
                )
            )
    return rows


def respondent_metrics(responses: Sequence[Response]) -> list[RespondentMetric]:
    if not responses:
        raise ValueError("at least one response is required")
    grouped: dict[str, list[Response]] = defaultdict(list)
    for response in responses:
        grouped[response.respondent_id].append(response)

    metrics: list[RespondentMetric] = []
    for respondent_id, rows in sorted(grouped.items()):
        account_count = len(rows)
        group_counts = Counter(row.reuse_group for row in rows)
        reused_pairs = sum(count * (count - 1) // 2 for count in group_counts.values())
        possible_pairs = account_count * (account_count - 1) // 2
        metrics.append(
            RespondentMetric(
                data_classification=MODEL_NOTICE,
                respondent_id=respondent_id,
                synthetic_profile=rows[0].synthetic_profile,
                account_count=account_count,
                distinct_password_groups=len(group_counts),
                normalized_password_diversity=round(len(group_counts) / account_count, 4),
                reused_account_pair_rate=round(reused_pairs / possible_pairs, 4),
                largest_exposure_cascade=max(group_counts.values()),
            )
        )
    return metrics


def category_summary(responses: Sequence[Response]) -> list[dict[str, object]]:
    if not responses:
        raise ValueError("at least one response is required")
    by_respondent: dict[str, list[Response]] = defaultdict(list)
    for response in responses:
        by_respondent[response.respondent_id].append(response)

    categories = sorted({response.category for response in responses})
    output: list[dict[str, object]] = []
    for category in categories:
        same = different = mixed = eligible = 0
        pair_rates: list[float] = []
        for rows in by_respondent.values():
            category_rows = [row for row in rows if row.category == category]
            if len(category_rows) < 2:
                continue
            eligible += 1
            labels = [row.reuse_group for row in category_rows]
            unique = len(set(labels))
            if unique == 1:
                same += 1
            elif unique == len(labels):
                different += 1
            else:
                mixed += 1
            pairs = list(combinations(labels, 2))
            pair_rates.append(sum(left == right for left, right in pairs) / len(pairs))
        output.append(
            {
                "data_classification": MODEL_NOTICE,
                "category": category,
                "eligible_respondents": eligible,
                "all_same_count": same,
                "all_different_count": different,
                "mixed_count": mixed,
                "mean_pair_reuse_rate": round(sum(pair_rates) / len(pair_rates), 4)
                if pair_rates
                else 0.0,
            }
        )
    return output


def overall_summary(metrics: Sequence[RespondentMetric]) -> dict[str, object]:
    if not metrics:
        raise ValueError("at least one metric is required")
    diversity = [item.normalized_password_diversity for item in metrics]
    pair_reuse = [item.reused_account_pair_rate for item in metrics]
    cascades = [item.largest_exposure_cascade for item in metrics]
    return {
        "data_classification": MODEL_NOTICE,
        "respondent_count": len(metrics),
        "mean_account_count": round(sum(item.account_count for item in metrics) / len(metrics), 3),
        "mean_distinct_password_groups": round(
            sum(item.distinct_password_groups for item in metrics) / len(metrics), 3
        ),
        "mean_normalized_password_diversity": round(sum(diversity) / len(diversity), 4),
        "mean_reused_account_pair_rate": round(sum(pair_reuse) / len(pair_reuse), 4),
        "mean_largest_exposure_cascade": round(sum(cascades) / len(cascades), 3),
    }


def distinct_group_histogram(metrics: Sequence[RespondentMetric]) -> list[dict[str, int]]:
    """Count respondents by their number of distinct opaque password groups."""

    if not metrics:
        raise ValueError("at least one metric is required")
    counts = Counter(item.distinct_password_groups for item in metrics)
    return [
        {"distinct_password_groups": group_count, "respondent_count": counts[group_count]}
        for group_count in range(min(counts), max(counts) + 1)
    ]


def write_csv(path: Path, rows: Sequence[object]) -> None:
    if not rows:
        raise ValueError("at least one row is required")
    path.parent.mkdir(parents=True, exist_ok=True)
    dictionaries = [asdict(row) for row in rows]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dictionaries[0]))
        writer.writeheader()
        writer.writerows(dictionaries)


def write_summary(
    path: Path,
    overall: dict[str, object],
    categories: Sequence[dict[str, object]],
    histogram: Sequence[dict[str, int]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "notice": MODEL_NOTICE,
        "method": "deterministic synthetic survey simulation",
        "overall": overall,
        "distinct_password_group_histogram": list(histogram),
        "categories": list(categories),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    experiment = subparsers.add_parser("experiment", help="generate and analyze synthetic data")
    experiment.add_argument("--respondents", type=int, default=DEFAULT_RESPONDENTS)
    experiment.add_argument("--seed", type=int, default=DEFAULT_SEED)
    experiment.add_argument(
        "--responses", type=Path, default=Path("reports/synthetic_responses.csv")
    )
    experiment.add_argument(
        "--metrics", type=Path, default=Path("reports/respondent_metrics.csv")
    )
    experiment.add_argument("--summary", type=Path, default=Path("reports/summary.json"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    responses = generate_responses(args.respondents, args.seed)
    metrics = respondent_metrics(responses)
    categories = category_summary(responses)
    write_csv(args.responses, responses)
    write_csv(args.metrics, metrics)
    write_summary(
        args.summary,
        overall_summary(metrics),
        categories,
        distinct_group_histogram(metrics),
    )
    print(MODEL_NOTICE)
    print(f"Wrote {len(responses)} synthetic account rows for {len(metrics)} respondents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
