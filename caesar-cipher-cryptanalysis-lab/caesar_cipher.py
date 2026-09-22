"""Caesar-cipher encryption and cryptanalysis lab.

This module intentionally demonstrates a historically important but insecure
cipher. It preserves case and leaves non-alphabetic characters unchanged.
"""

from __future__ import annotations

import argparse
import json
import secrets
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from string import ascii_uppercase
from typing import Sequence


ENGLISH_FREQUENCIES = {
    "A": 8.167,
    "B": 1.492,
    "C": 2.782,
    "D": 4.253,
    "E": 12.702,
    "F": 2.228,
    "G": 2.015,
    "H": 6.094,
    "I": 6.966,
    "J": 0.153,
    "K": 0.772,
    "L": 4.025,
    "M": 2.406,
    "N": 6.749,
    "O": 7.507,
    "P": 1.929,
    "Q": 0.095,
    "R": 5.987,
    "S": 6.327,
    "T": 9.056,
    "U": 2.758,
    "V": 0.978,
    "W": 2.360,
    "X": 0.150,
    "Y": 1.974,
    "Z": 0.074,
}


@dataclass(frozen=True)
class Candidate:
    """One possible decryption and its English-frequency score."""

    key: int
    plaintext: str
    chi_squared: float


@dataclass(frozen=True)
class FrequencyResult:
    """Result of assuming that the most common ciphertext letter represents E."""

    key: int
    most_common_cipher_letter: str
    count: int
    plaintext: str


def _validate_key(key: int) -> int:
    if isinstance(key, bool) or not isinstance(key, int):
        raise TypeError("key must be an integer")
    return key % 26


def shift_text(text: str, key: int) -> str:
    """Shift ASCII letters by *key*, preserving case and other characters."""

    normalized_key = _validate_key(key)
    output: list[str] = []
    for character in text:
        if "A" <= character <= "Z":
            output.append(chr((ord(character) - ord("A") + normalized_key) % 26 + ord("A")))
        elif "a" <= character <= "z":
            output.append(chr((ord(character) - ord("a") + normalized_key) % 26 + ord("a")))
        else:
            output.append(character)
    return "".join(output)


def encrypt(plaintext: str, key: int) -> str:
    """Encrypt plaintext with a Caesar shift."""

    return shift_text(plaintext, key)


def decrypt(ciphertext: str, key: int) -> str:
    """Decrypt ciphertext that was encrypted with *key*."""

    return shift_text(ciphertext, -_validate_key(key))


def letter_counts(text: str) -> Counter[str]:
    """Count ASCII letters without regard to case."""

    return Counter(character for character in text.upper() if character in ascii_uppercase)


def chi_squared_score(text: str) -> float:
    """Return distance from expected English letter frequencies; lower is better."""

    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return float("inf")

    return sum(
        ((counts.get(letter, 0) - total * frequency / 100) ** 2)
        / (total * frequency / 100)
        for letter, frequency in ENGLISH_FREQUENCIES.items()
    )


def brute_force(ciphertext: str) -> list[Candidate]:
    """Try every non-identity Caesar key in numeric key order."""

    return [
        Candidate(key=key, plaintext=decrypt(ciphertext, key), chi_squared=chi_squared_score(decrypt(ciphertext, key)))
        for key in range(1, 26)
    ]


def rank_candidates(ciphertext: str) -> list[Candidate]:
    """Rank all 25 possible non-identity keys by English letter frequencies."""

    return sorted(brute_force(ciphertext), key=lambda candidate: (candidate.chi_squared, candidate.key))


def frequency_analysis(ciphertext: str) -> FrequencyResult:
    """Decrypt by assuming the most frequent ciphertext letter represents E."""

    counts = letter_counts(ciphertext)
    if not counts:
        raise ValueError("ciphertext must contain at least one ASCII letter")

    # Alphabetical tie-breaking makes the experiment deterministic.
    most_common, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    key = (ord(most_common) - ord("E")) % 26
    return FrequencyResult(
        key=key,
        most_common_cipher_letter=most_common,
        count=count,
        plaintext=decrypt(ciphertext, key),
    )


def random_nonzero_key() -> int:
    """Return a uniformly selected Caesar key from 1 through 25."""

    return secrets.randbelow(25) + 1


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Encrypt and crack Caesar-cipher text files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a plaintext file.")
    encrypt_parser.add_argument("input", help="UTF-8 plaintext file")
    encrypt_parser.add_argument("output", help="destination ciphertext file")
    encrypt_parser.add_argument("--key", type=int, help="key from 1 to 25; omitted selects one randomly")

    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt using a known key.")
    decrypt_parser.add_argument("input", help="UTF-8 ciphertext file")
    decrypt_parser.add_argument("output", help="destination plaintext file")
    decrypt_parser.add_argument("--key", type=int, required=True)

    brute_parser = subparsers.add_parser("brute-force", help="Print or save all 25 possible plaintexts.")
    brute_parser.add_argument("input", help="UTF-8 ciphertext file")
    brute_parser.add_argument("--output", help="optional JSON report path")

    frequency_parser = subparsers.add_parser("frequency", help="Analyze ciphertext letter frequencies.")
    frequency_parser.add_argument("input", help="UTF-8 ciphertext file")
    frequency_parser.add_argument("--rank", type=int, default=5, help="number of ranked candidates to show")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "encrypt":
        if args.key is not None and not 1 <= args.key <= 25:
            raise SystemExit("--key must be between 1 and 25")
        key = args.key if args.key is not None else random_nonzero_key()
        write_text(args.output, encrypt(read_text(args.input), key))
        print(f"Encrypted {args.input} -> {args.output} with key {key}")
        return 0

    if args.command == "decrypt":
        if not 1 <= args.key <= 25:
            raise SystemExit("--key must be between 1 and 25")
        write_text(args.output, decrypt(read_text(args.input), args.key))
        print(f"Decrypted {args.input} -> {args.output} with key {args.key}")
        return 0

    ciphertext = read_text(args.input)
    if args.command == "brute-force":
        candidates = brute_force(ciphertext)
        if args.output:
            write_text(args.output, json.dumps([asdict(item) for item in candidates], indent=2) + "\n")
            print(f"Saved 25 candidates to {args.output}")
        else:
            for candidate in candidates:
                print(f"KEY {candidate.key:2d} | {candidate.plaintext.rstrip()}")
        return 0

    result = frequency_analysis(ciphertext)
    print(
        f"Simple E assumption: {result.most_common_cipher_letter} occurs {result.count} times; "
        f"predicted key {result.key}\n{result.plaintext.rstrip()}"
    )
    print("\nBest chi-squared candidates:")
    for candidate in rank_candidates(ciphertext)[: max(1, args.rank)]:
        print(f"KEY {candidate.key:2d} | score {candidate.chi_squared:8.3f} | {candidate.plaintext.rstrip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
