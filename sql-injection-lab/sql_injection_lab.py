"""Safe, deterministic SQL-injection prevention experiment.

The lab never executes a dynamically constructed SQL statement.  It models the
effect of a small, fixed set of classroom attack scenarios, while the secure
path is exercised against a real in-memory SQLite database using parameters.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_SEED = 20260924
MAX_USERS = 200
SCENARIOS = (
    "valid_credentials",
    "wrong_password",
    "username_tautology",
    "password_tautology",
    "comment_bypass",
    "union_exposure",
)

LOGIN_QUERY = "SELECT username FROM users WHERE username = ? AND password = ?"
SEARCH_QUERY = "SELECT username, favorite_color FROM users WHERE username = ?"
COUNT_QUERY = "SELECT COUNT(*) FROM users"


@dataclass(frozen=True)
class SyntheticUser:
    username: str
    password: str
    email: str
    favorite_color: str


@dataclass(frozen=True)
class Attempt:
    scenario: str
    target_user: str
    supplied_username: str
    supplied_password: str
    authorized_attempt: bool


@dataclass(frozen=True)
class TrialResult:
    scenario: str
    repetition: int
    target_user: str
    payload_sha256: str
    authorized_attempt: bool
    legacy_authenticated: bool
    secure_authenticated: bool
    legacy_unauthorized_access: bool
    secure_unauthorized_access: bool
    legacy_rows_exposed: int
    secure_rows_exposed: int
    database_intact: bool


def _digest(label: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{label}".encode("utf-8")).hexdigest()


def make_synthetic_users(count: int, seed: int = DEFAULT_SEED) -> tuple[SyntheticUser, ...]:
    """Create deterministic, fictional accounts for the local experiment."""
    if not 1 <= count <= MAX_USERS:
        raise ValueError(f"count must be between 1 and {MAX_USERS}")

    colors = ("blue", "green", "orange", "purple", "red")
    users = []
    for index in range(count):
        token = _digest(f"user:{index}", seed)[:12]
        users.append(
            SyntheticUser(
                username=f"student_{index:03d}",
                password=f"Synthetic-{token}",
                email=f"student_{index:03d}@example.invalid",
                favorite_color=colors[index % len(colors)],
            )
        )
    return tuple(users)


def create_database(users: Sequence[SyntheticUser]) -> sqlite3.Connection:
    """Create an isolated SQLite database containing only synthetic records."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            favorite_color TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO users (username, password, email, favorite_color) VALUES (?, ?, ?, ?)",
        [(user.username, user.password, user.email, user.favorite_color) for user in users],
    )
    connection.commit()
    return connection


def secure_login(connection: sqlite3.Connection, username: str, password: str) -> str | None:
    """Authenticate with a parameterized query; inputs remain literal data."""
    row = connection.execute(LOGIN_QUERY, (username, password)).fetchone()
    return None if row is None else str(row[0])


def secure_search(connection: sqlite3.Connection, username: str) -> tuple[tuple[str, str], ...]:
    """Search public fields with a parameterized query."""
    rows = connection.execute(SEARCH_QUERY, (username,)).fetchall()
    return tuple((str(row[0]), str(row[1])) for row in rows)


def legacy_query_plan(attempt: Attempt) -> dict[str, object]:
    """Describe unsafe interpolation without constructing or executing SQL."""
    return {
        "operation": "look up a user by supplied username and password",
        "binding_strategy": "legacy string interpolation (modeled only)",
        "scenario": attempt.scenario,
        "input_digest": hashlib.sha256(
            f"{attempt.supplied_username}\0{attempt.supplied_password}".encode("utf-8")
        ).hexdigest(),
        "executed": False,
    }


def _attempt_for(user: SyntheticUser, scenario: str) -> Attempt:
    """Return one bounded classroom input for a named scenario."""
    if scenario == "valid_credentials":
        return Attempt(scenario, user.username, user.username, user.password, True)
    if scenario == "wrong_password":
        return Attempt(scenario, user.username, user.username, "definitely-wrong", False)
    if scenario == "username_tautology":
        return Attempt(scenario, user.username, "' OR '1'='1' --", "unused", False)
    if scenario == "password_tautology":
        return Attempt(scenario, user.username, user.username, "' OR '1'='1' --", False)
    if scenario == "comment_bypass":
        return Attempt(scenario, user.username, f"{user.username}' --", "unused", False)
    if scenario == "union_exposure":
        return Attempt(
            scenario,
            user.username,
            "' UNION SELECT username, email FROM users --",
            "unused",
            False,
        )
    raise ValueError(f"unknown scenario: {scenario}")


def _legacy_model(attempt: Attempt, user_count: int) -> tuple[bool, int]:
    """Model expected behavior of an unsafe legacy query for fixed scenarios."""
    if attempt.scenario == "valid_credentials":
        return True, 1
    if attempt.scenario == "wrong_password":
        return False, 0
    if attempt.scenario in {"username_tautology", "password_tautology", "comment_bypass"}:
        return True, 1
    if attempt.scenario == "union_exposure":
        return False, user_count
    raise ValueError(f"unknown scenario: {attempt.scenario}")


def run_trial(
    connection: sqlite3.Connection,
    user: SyntheticUser,
    scenario: str,
    repetition: int,
    user_count: int,
) -> TrialResult:
    """Compare the legacy model with real parameterized SQLite behavior."""
    if repetition < 1:
        raise ValueError("repetition must be positive")

    attempt = _attempt_for(user, scenario)
    legacy_authenticated, legacy_rows = _legacy_model(attempt, user_count)
    secure_username = secure_login(
        connection, attempt.supplied_username, attempt.supplied_password
    )
    secure_authenticated = secure_username is not None
    if scenario == "union_exposure":
        secure_rows = len(secure_search(connection, attempt.supplied_username))
    else:
        secure_rows = int(secure_authenticated)
    database_intact = connection.execute(COUNT_QUERY).fetchone()[0] == user_count
    payload_sha256 = str(legacy_query_plan(attempt)["input_digest"])

    return TrialResult(
        scenario=scenario,
        repetition=repetition,
        target_user=user.username,
        payload_sha256=payload_sha256,
        authorized_attempt=attempt.authorized_attempt,
        legacy_authenticated=legacy_authenticated,
        secure_authenticated=secure_authenticated,
        legacy_unauthorized_access=legacy_authenticated and not attempt.authorized_attempt,
        secure_unauthorized_access=secure_authenticated and not attempt.authorized_attempt,
        legacy_rows_exposed=legacy_rows,
        secure_rows_exposed=secure_rows,
        database_intact=bool(database_intact),
    )


def run_experiment(
    user_count: int = 25,
    repetitions: int = 4,
    seed: int = DEFAULT_SEED,
) -> list[TrialResult]:
    """Run all scenarios against each synthetic account."""
    if repetitions < 1:
        raise ValueError("repetitions must be positive")

    users = make_synthetic_users(user_count, seed)
    connection = create_database(users)
    try:
        return [
            run_trial(connection, user, scenario, repetition, user_count)
            for scenario in SCENARIOS
            for user in users
            for repetition in range(1, repetitions + 1)
        ]
    finally:
        connection.close()


def summarize(results: Iterable[TrialResult]) -> list[dict[str, object]]:
    """Aggregate outcomes by scenario."""
    groups: dict[str, list[TrialResult]] = defaultdict(list)
    for result in results:
        groups[result.scenario].append(result)

    summary = []
    for scenario in SCENARIOS:
        rows = groups.get(scenario, [])
        if not rows:
            continue
        trial_count = len(rows)
        summary.append(
            {
                "scenario": scenario,
                "trials": trial_count,
                "legacy_authentication_rate": sum(row.legacy_authenticated for row in rows)
                / trial_count,
                "secure_authentication_rate": sum(row.secure_authenticated for row in rows)
                / trial_count,
                "legacy_unauthorized_access_rate": sum(
                    row.legacy_unauthorized_access for row in rows
                )
                / trial_count,
                "secure_unauthorized_access_rate": sum(
                    row.secure_unauthorized_access for row in rows
                )
                / trial_count,
                "legacy_mean_rows_exposed": sum(row.legacy_rows_exposed for row in rows)
                / trial_count,
                "secure_mean_rows_exposed": sum(row.secure_rows_exposed for row in rows)
                / trial_count,
                "database_integrity_rate": sum(row.database_intact for row in rows) / trial_count,
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
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    experiment = subparsers.add_parser("experiment", help="Run the full safe experiment.")
    experiment.add_argument("--users", type=int, default=25)
    experiment.add_argument("--repetitions", type=int, default=4)
    experiment.add_argument("--seed", type=int, default=DEFAULT_SEED)
    experiment.add_argument("--output", default="reports/results.csv")
    experiment.add_argument("--summary", default="reports/summary.json")

    demo = subparsers.add_parser("demo", help="Run one redacted classroom scenario.")
    demo.add_argument("--scenario", choices=SCENARIOS, default="username_tautology")
    demo.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        user = make_synthetic_users(1, args.seed)[0]
        connection = create_database((user,))
        try:
            result = run_trial(connection, user, args.scenario, 1, 1)
        finally:
            connection.close()
        print(json.dumps(asdict(result), indent=2))
        return 0

    results = run_experiment(args.users, args.repetitions, args.seed)
    summary_rows = summarize(results)
    write_results(args.output, results)
    write_summary(args.summary, summary_rows)
    print(f"Wrote {len(results)} safe trials and {len(summary_rows)} scenario summaries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
