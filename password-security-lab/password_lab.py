"""Local, synthetic password-security experiment.

The module demonstrates password search-space growth and compares several
guess-generation strategies. It has no networking or account-login features.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import itertools
import json
import string
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence


ALPHANUMERIC = string.digits + string.ascii_lowercase + string.ascii_uppercase
DEFAULT_MAX_GUESSES = 1_000_000
DEFAULT_ITERATIONS = 200_000


@dataclass(frozen=True)
class PasswordRecord:
    """A salted PBKDF2 verifier for one synthetic lab password."""

    algorithm: str
    iterations: int
    salt_hex: str
    digest_hex: str


@dataclass(frozen=True)
class CrackResult:
    method: str
    found: bool
    password: str | None
    guesses: int
    elapsed_seconds: float
    stopped_by_limit: bool = False


@dataclass(frozen=True)
class SearchSpaceRow:
    alphabet_size: int
    length: int
    combinations: int
    seconds_at_one_guess_per_second: int
    seconds_at_one_million_guesses_per_second: float


def search_space(alphabet_size: int, length: int) -> int:
    """Return the number of fixed-length strings in the given alphabet."""

    if alphabet_size < 1:
        raise ValueError("alphabet_size must be positive")
    if length < 1:
        raise ValueError("length must be positive")
    return alphabet_size**length


def build_search_space_rows(
    alphabet_sizes: Iterable[int] = (10, 26, 62),
    lengths: Iterable[int] = range(1, 9),
) -> list[SearchSpaceRow]:
    rows: list[SearchSpaceRow] = []
    for alphabet_size in alphabet_sizes:
        for length in lengths:
            combinations = search_space(alphabet_size, length)
            rows.append(
                SearchSpaceRow(
                    alphabet_size=alphabet_size,
                    length=length,
                    combinations=combinations,
                    seconds_at_one_guess_per_second=combinations,
                    seconds_at_one_million_guesses_per_second=combinations / 1_000_000,
                )
            )
    return rows


def human_duration(seconds: float) -> str:
    """Format a duration using the largest useful unit."""

    if seconds < 0:
        raise ValueError("seconds cannot be negative")
    units = (
        (365.25 * 24 * 60 * 60, "years"),
        (24 * 60 * 60, "days"),
        (60 * 60, "hours"),
        (60, "minutes"),
    )
    for divisor, label in units:
        if seconds >= divisor:
            return f"{seconds / divisor:,.3g} {label}"
    return f"{seconds:,.3g} seconds"


def make_record(
    password: str,
    *,
    salt: bytes,
    iterations: int = DEFAULT_ITERATIONS,
) -> PasswordRecord:
    """Create a deterministic lab verifier using PBKDF2-HMAC-SHA-256."""

    if not password:
        raise ValueError("password cannot be empty")
    if len(salt) < 4:
        raise ValueError("salt must contain at least four bytes")
    if iterations < 1:
        raise ValueError("iterations must be positive")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return PasswordRecord("pbkdf2_sha256", iterations, salt.hex(), digest.hex())


def verify_guess(record: PasswordRecord, guess: str) -> bool:
    """Compare a guess to a lab verifier in constant time."""

    if record.algorithm != "pbkdf2_sha256":
        raise ValueError(f"unsupported algorithm: {record.algorithm}")
    salt = bytes.fromhex(record.salt_hex)
    expected = bytes.fromhex(record.digest_hex)
    actual = hashlib.pbkdf2_hmac(
        "sha256", guess.encode("utf-8"), salt, record.iterations
    )
    return hmac.compare_digest(actual, expected)


def _run_candidates(
    record: PasswordRecord,
    candidates: Iterable[str],
    *,
    method: str,
    max_guesses: int = DEFAULT_MAX_GUESSES,
    clock: Callable[[], float] = time.perf_counter,
) -> CrackResult:
    if max_guesses < 1:
        raise ValueError("max_guesses must be positive")
    started = clock()
    for guesses, candidate in enumerate(candidates, start=1):
        if guesses > max_guesses:
            return CrackResult(method, False, None, max_guesses, clock() - started, True)
        if verify_guess(record, candidate):
            return CrackResult(method, True, candidate, guesses, clock() - started)
    return CrackResult(method, False, None, guesses if "guesses" in locals() else 0, clock() - started)


def numeric_candidates(length: int) -> Iterator[str]:
    if length < 1:
        raise ValueError("length must be positive")
    for number in range(10**length):
        yield f"{number:0{length}d}"


def numeric_brute_force(
    record: PasswordRecord,
    *,
    length: int,
    max_guesses: int = DEFAULT_MAX_GUESSES,
) -> CrackResult:
    return _run_candidates(
        record,
        numeric_candidates(length),
        method=f"numeric-{length}",
        max_guesses=max_guesses,
    )


def alphanumeric_candidates(
    max_length: int,
    *,
    alphabet: str = ALPHANUMERIC,
) -> Iterator[str]:
    if max_length < 1:
        raise ValueError("max_length must be positive")
    if not alphabet or len(set(alphabet)) != len(alphabet):
        raise ValueError("alphabet must contain unique characters")
    for length in range(1, max_length + 1):
        for characters in itertools.product(alphabet, repeat=length):
            yield "".join(characters)


def alphanumeric_brute_force(
    record: PasswordRecord,
    *,
    max_length: int,
    alphabet: str = ALPHANUMERIC,
    max_guesses: int = DEFAULT_MAX_GUESSES,
) -> CrackResult:
    return _run_candidates(
        record,
        alphanumeric_candidates(max_length, alphabet=alphabet),
        method=f"alphanumeric-1-to-{max_length}",
        max_guesses=max_guesses,
    )


def dictionary_candidates(words: Iterable[str]) -> Iterator[str]:
    """Yield common human variations, once each, in a deterministic order."""

    seen: set[str] = set()
    for raw_word in words:
        word = raw_word.strip()
        if not word:
            continue
        for candidate in (word.lower(), word.capitalize(), word.upper(), word[::-1]):
            if candidate not in seen:
                seen.add(candidate)
                yield candidate


def dictionary_attack(
    record: PasswordRecord,
    words: Iterable[str],
    *,
    max_guesses: int = DEFAULT_MAX_GUESSES,
) -> CrackResult:
    return _run_candidates(
        record,
        dictionary_candidates(words),
        method="dictionary",
        max_guesses=max_guesses,
    )


def combined_word_candidates(
    words: Iterable[str],
    separators: Iterable[str] = ("", "+", "-", "_", "1"),
) -> Iterator[str]:
    cleaned = [word.strip().lower() for word in words if word.strip()]
    for first in cleaned:
        for separator in separators:
            for second in cleaned:
                if first == second:
                    continue
                for candidate in (
                    first + separator + second,
                    first.capitalize() + separator + second.capitalize(),
                ):
                    yield candidate


def combined_word_attack(
    record: PasswordRecord,
    words: Iterable[str],
    *,
    separators: Iterable[str] = ("", "+", "-", "_", "1"),
    max_guesses: int = DEFAULT_MAX_GUESSES,
) -> CrackResult:
    return _run_candidates(
        record,
        combined_word_candidates(words, separators),
        method="combined-words",
        max_guesses=max_guesses,
    )


def load_words(path: str | Path) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def demo_results(iterations: int = 2_000) -> list[CrackResult]:
    """Run bounded attacks against four explicitly synthetic passwords."""

    words = load_words(Path(__file__).with_name("samples") / "synthetic_words.txt")
    cases = (
        (make_record("042", salt=b"numeric-demo", iterations=iterations), lambda record: numeric_brute_force(record, length=3)),
        (make_record("A7", salt=b"alpha-demo-01", iterations=iterations), lambda record: alphanumeric_brute_force(record, max_length=2)),
        (make_record("Sunshine", salt=b"dict-demo-001", iterations=iterations), lambda record: dictionary_attack(record, words)),
        (make_record("red+planet", salt=b"combo-demo-01", iterations=iterations), lambda record: combined_word_attack(record, words)),
    )
    return [attack(record) for record, attack in cases]


def write_csv(path: str | Path, rows: Sequence[SearchSpaceRow]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SearchSpaceRow.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe, local password-security experiment.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    table_parser = subparsers.add_parser("table", help="Calculate search-space tables.")
    table_parser.add_argument("--output", help="optional CSV output path")

    estimate_parser = subparsers.add_parser("estimate", help="Estimate one fixed-length search space.")
    estimate_parser.add_argument("alphabet_size", type=int)
    estimate_parser.add_argument("length", type=int)
    estimate_parser.add_argument("--guesses-per-second", type=float, default=1.0)

    demo_parser = subparsers.add_parser("demo", help="Run attacks on bundled synthetic examples.")
    demo_parser.add_argument("--iterations", type=int, default=2_000)
    demo_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "table":
        rows = build_search_space_rows()
        if args.output:
            write_csv(args.output, rows)
            print(f"Saved {len(rows)} rows to {args.output}")
        else:
            print("alphabet,length,combinations,time_at_1_guess_per_second")
            for row in rows:
                print(
                    f"{row.alphabet_size},{row.length},{row.combinations},"
                    f"{human_duration(row.seconds_at_one_guess_per_second)}"
                )
        return 0

    if args.command == "estimate":
        if args.guesses_per_second <= 0:
            raise SystemExit("--guesses-per-second must be positive")
        combinations = search_space(args.alphabet_size, args.length)
        seconds = combinations / args.guesses_per_second
        print(f"Combinations: {combinations:,}")
        print(f"Worst-case time: {human_duration(seconds)}")
        return 0

    if args.iterations < 1:
        raise SystemExit("--iterations must be positive")
    results = demo_results(args.iterations)
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            state = f"found {result.password!r}" if result.found else "not found"
            print(
                f"{result.method:22} {state:24} guesses={result.guesses:6d} "
                f"seconds={result.elapsed_seconds:.6f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
