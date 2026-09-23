"""Safe, deterministic deleted-file recovery experiment.

This module models a small block device in memory. It never scans, deletes, or
overwrites files on the host computer. The model is intentionally simple, but
it demonstrates the distinction between directory metadata and file content,
and why later writes can make deleted content partially or fully unrecoverable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


MAGIC = b"DFL1"
HEADER = struct.Struct(">4sHQ32s")
DEFAULT_CLUSTER_SIZE = 128
DEFAULT_CLUSTER_COUNT = 128


@dataclass(frozen=True)
class FileEntry:
    """Directory metadata for one simulated file."""

    name: str
    clusters: tuple[int, ...]
    payload_size: int
    digest: str


@dataclass(frozen=True)
class RecoveredFile:
    """A file reconstructed from directory metadata or raw carving."""

    name: str
    content: bytes
    expected_digest: str
    actual_digest: str
    exact_match: bool
    method: str


@dataclass(frozen=True)
class TrialResult:
    file_type: str
    scenario: str
    overwrite_fraction: float
    trial: int
    recovered: bool
    exact_match: bool
    matching_bytes: int
    total_bytes: int
    recovery_ratio: float
    method: str


class SimulatedVolume:
    """A bounded, in-memory cluster allocation model."""

    def __init__(
        self,
        *,
        cluster_size: int = DEFAULT_CLUSTER_SIZE,
        cluster_count: int = DEFAULT_CLUSTER_COUNT,
    ) -> None:
        if cluster_size < HEADER.size + 1:
            raise ValueError("cluster_size is too small for the file header")
        if cluster_count < 1:
            raise ValueError("cluster_count must be positive")
        self.cluster_size = cluster_size
        self.cluster_count = cluster_count
        self.data = bytearray(cluster_size * cluster_count)
        self._free = set(range(cluster_count))
        self.active: dict[str, FileEntry] = {}
        self.recycle_bin: dict[str, FileEntry] = {}

    def _container(self, name: str, payload: bytes) -> bytes:
        encoded_name = name.encode("utf-8")
        if not encoded_name or len(encoded_name) > 255:
            raise ValueError("name must encode to 1-255 bytes")
        digest = hashlib.sha256(payload).digest()
        return HEADER.pack(MAGIC, len(encoded_name), len(payload), digest) + encoded_name + payload

    def _find_contiguous_run(self, needed: int) -> tuple[int, ...]:
        for start in range(self.cluster_count - needed + 1):
            run = tuple(range(start, start + needed))
            if all(cluster in self._free for cluster in run):
                return run
        raise ValueError("simulated volume has insufficient contiguous space")

    def write_file(self, name: str, payload: bytes) -> FileEntry:
        if name in self.active or name in self.recycle_bin:
            raise ValueError(f"file already exists: {name}")
        container = self._container(name, payload)
        needed = math.ceil(len(container) / self.cluster_size)
        clusters = self._find_contiguous_run(needed)
        padded = container.ljust(needed * self.cluster_size, b"\x00")
        for offset, cluster in enumerate(clusters):
            start = cluster * self.cluster_size
            block = padded[offset * self.cluster_size : (offset + 1) * self.cluster_size]
            self.data[start : start + self.cluster_size] = block
            self._free.remove(cluster)
        entry = FileEntry(
            name=name,
            clusters=clusters,
            payload_size=len(payload),
            digest=hashlib.sha256(payload).hexdigest(),
        )
        self.active[name] = entry
        return entry

    def move_to_recycle_bin(self, name: str) -> FileEntry:
        entry = self.active.pop(name)
        self.recycle_bin[name] = entry
        return entry

    def empty_recycle_bin(self) -> tuple[FileEntry, ...]:
        removed = tuple(self.recycle_bin.values())
        for entry in removed:
            self._free.update(entry.clusters)
        self.recycle_bin.clear()
        return removed

    def delete_file(self, name: str) -> FileEntry:
        entry = self.active.pop(name)
        self._free.update(entry.clusters)
        return entry

    def overwrite_deleted_clusters(
        self,
        entry: FileEntry,
        fraction: float,
        *,
        seed: int,
    ) -> tuple[int, ...]:
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("fraction must be between zero and one")
        candidates = [cluster for cluster in entry.clusters if cluster in self._free]
        count = math.ceil(len(entry.clusters) * fraction)
        count = min(count, len(candidates))
        ranked = sorted(
            candidates,
            key=lambda cluster: hashlib.sha256(f"{seed}:{cluster}".encode()).digest(),
        )
        selected = tuple(sorted(ranked[:count]))
        for cluster in selected:
            start = cluster * self.cluster_size
            noise = bytearray()
            counter = 0
            while len(noise) < self.cluster_size:
                material = f"noise:{seed}:{cluster}:{counter}".encode()
                noise.extend(hashlib.sha256(material).digest())
                counter += 1
            self.data[start : start + self.cluster_size] = noise[: self.cluster_size]
            self._free.remove(cluster)
        return selected

    def _decode_at_cluster(self, cluster: int, *, method: str) -> RecoveredFile | None:
        start = cluster * self.cluster_size
        if self.data[start : start + len(MAGIC)] != MAGIC:
            return None
        header_bytes = bytes(self.data[start : start + HEADER.size])
        try:
            magic, name_size, payload_size, expected_digest = HEADER.unpack(header_bytes)
        except struct.error:
            return None
        if magic != MAGIC or name_size < 1 or name_size > 255:
            return None
        container_size = HEADER.size + name_size + payload_size
        if container_size > len(self.data) - start:
            return None
        raw = bytes(self.data[start : start + container_size])
        name_start = HEADER.size
        name_end = name_start + name_size
        try:
            name = raw[name_start:name_end].decode("utf-8")
        except UnicodeDecodeError:
            return None
        content = raw[name_end:]
        actual_digest = hashlib.sha256(content).hexdigest()
        expected_hex = expected_digest.hex()
        return RecoveredFile(
            name=name,
            content=content,
            expected_digest=expected_hex,
            actual_digest=actual_digest,
            exact_match=actual_digest == expected_hex,
            method=method,
        )

    def recover_from_recycle_bin(self, name: str) -> RecoveredFile | None:
        entry = self.recycle_bin.get(name)
        if entry is None:
            return None
        return self._decode_at_cluster(entry.clusters[0], method="directory-metadata")

    def carve(self) -> list[RecoveredFile]:
        recovered: list[RecoveredFile] = []
        seen: set[tuple[str, str]] = set()
        for cluster in range(self.cluster_count):
            candidate = self._decode_at_cluster(cluster, method="signature-carving")
            if candidate is None:
                continue
            identity = (candidate.name, candidate.expected_digest)
            if identity not in seen:
                recovered.append(candidate)
                seen.add(identity)
        return recovered

    def export_image(self, path: str | Path) -> None:
        """Save the simulated bytes for inspection; no host disk is scanned."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.data)


def sample_files() -> dict[str, bytes]:
    """Return deterministic, synthetic evidence fixtures."""
    return {
        "text": (b"FORENSIC-LAB-TEXT-LINE\n" * 90)[:2048],
        "image": b"\x89PNG\r\n\x1a\n" + bytes((index * 17) % 256 for index in range(4088)),
        "document": b"%PDF-1.7\n" + bytes((index * 29 + 7) % 256 for index in range(3063)),
    }


def _matching_bytes(original: bytes, recovered: bytes) -> int:
    return sum(left == right for left, right in zip(original, recovered, strict=False))


def run_trial(
    file_type: str,
    payload: bytes,
    scenario: str,
    overwrite_fraction: float,
    trial: int,
    *,
    seed: int,
) -> TrialResult:
    volume = SimulatedVolume()
    name = f"synthetic-{file_type}.bin"
    volume.write_file(name, payload)

    if scenario == "recycle-bin":
        volume.move_to_recycle_bin(name)
        recovered = volume.recover_from_recycle_bin(name)
    elif scenario == "emptied-recycle-bin":
        volume.move_to_recycle_bin(name)
        volume.empty_recycle_bin()
        recovered = next((item for item in volume.carve() if item.name == name), None)
    elif scenario == "overwritten":
        deleted = volume.delete_file(name)
        volume.overwrite_deleted_clusters(
            deleted,
            overwrite_fraction,
            seed=seed + trial,
        )
        recovered = next((item for item in volume.carve() if item.name == name), None)
    else:
        raise ValueError(f"unknown scenario: {scenario}")

    matching = _matching_bytes(payload, recovered.content) if recovered else 0
    return TrialResult(
        file_type=file_type,
        scenario=scenario,
        overwrite_fraction=overwrite_fraction,
        trial=trial,
        recovered=recovered is not None,
        exact_match=bool(recovered and recovered.exact_match),
        matching_bytes=matching,
        total_bytes=len(payload),
        recovery_ratio=matching / len(payload),
        method=recovered.method if recovered else "not-recovered",
    )


def run_experiment(*, trials: int = 25, seed: int = 20260923) -> list[TrialResult]:
    if trials < 1:
        raise ValueError("trials must be positive")
    scenarios = (
        ("recycle-bin", 0.0),
        ("emptied-recycle-bin", 0.0),
        ("overwritten", 0.25),
        ("overwritten", 0.50),
        ("overwritten", 0.75),
        ("overwritten", 1.00),
    )
    rows: list[TrialResult] = []
    for file_index, (file_type, payload) in enumerate(sample_files().items()):
        for scenario_index, (scenario, fraction) in enumerate(scenarios):
            scenario_seed = seed + file_index * 100_000 + scenario_index * 10_000
            for trial in range(1, trials + 1):
                rows.append(
                    run_trial(
                        file_type,
                        payload,
                        scenario,
                        fraction,
                        trial,
                        seed=scenario_seed,
                    )
                )
    return rows


def summarize(results: Iterable[TrialResult]) -> list[dict[str, object]]:
    groups: dict[tuple[str, float], list[TrialResult]] = {}
    for result in results:
        groups.setdefault((result.scenario, result.overwrite_fraction), []).append(result)
    summary: list[dict[str, object]] = []
    for (scenario, fraction), rows in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0])):
        total = len(rows)
        recovered = sum(row.recovered for row in rows)
        exact = sum(row.exact_match for row in rows)
        summary.append(
            {
                "scenario": scenario,
                "overwrite_fraction": fraction,
                "trials": total,
                "recovered_files": recovered,
                "exact_files": exact,
                "recovery_rate": recovered / total,
                "exact_recovery_rate": exact / total,
                "mean_matching_byte_ratio": sum(row.recovery_ratio for row in rows) / total,
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
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe deleted-file recovery simulation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    experiment = subparsers.add_parser("experiment", help="Run repeated recovery trials.")
    experiment.add_argument("--trials", type=int, default=25)
    experiment.add_argument("--seed", type=int, default=20260923)
    experiment.add_argument("--output", default="reports/results.csv")
    experiment.add_argument("--summary", default="reports/summary.json")

    image = subparsers.add_parser("image", help="Create one harmless simulated disk image.")
    image.add_argument("output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "image":
        volume = SimulatedVolume()
        volume.write_file("synthetic-evidence.txt", sample_files()["text"])
        volume.export_image(args.output)
        print(f"Saved simulated image to {args.output}")
        return 0

    if args.trials < 1:
        raise SystemExit("--trials must be positive")
    results = run_experiment(trials=args.trials, seed=args.seed)
    summary_rows = summarize(results)
    write_results(args.output, results)
    write_summary(args.summary, summary_rows)
    print(json.dumps(summary_rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
