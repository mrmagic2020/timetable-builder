#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import List


DEFAULT_SUBJECTS_FILE = Path("data/subjects.json")
DEFAULT_OUTPUT_FILE = Path("data/students.json")

FIRST_NAMES = [
    "Daniel",
    "Arnold",
    "Alice",
    "Bob",
    "Chloe",
    "David",
    "Emily",
    "Felix",
    "Grace",
    "Henry",
    "Isabella",
    "Jack",
    "Liam",
    "Mia",
    "Noah",
    "Olivia",
    "Poppy",
    "Quinn",
    "Ruby",
    "Sophia",
]

LAST_NAMES = [
    "Cox",
    "Zhou",
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Garcia",
    "Rodriguez",
    "Wilson",
    "Martinez",
    "Anderson",
    "Taylor",
    "Thomas",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate random student data based on available subjects."
    )
    p.add_argument(
        "--subjects-file",
        type=Path,
        default=DEFAULT_SUBJECTS_FILE,
        help="Path to subjects.json (must be an array of objects with an ID field)",
    )
    p.add_argument(
        "--id-field",
        type=str,
        default="id",
        help="Field name in subjects.json objects to read as the subject ID (default: id)",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output path for students.json",
    )
    p.add_argument(
        "--count", type=int, default=50, help="Number of students to generate"
    )
    p.add_argument(
        "--min-subjects",
        type=int,
        default=6,
        help="Minimum subjects per student",
    )
    p.add_argument(
        "--max-subjects",
        type=int,
        default=7,
        help="Maximum subjects per student",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    p.add_argument(
        "--id-start",
        type=int,
        default=1540000,
        help="Starting integer for generated student IDs (IDs increment from here)",
    )
    p.add_argument(
        "--must-subject",
        action="append",
        default=[],
        help=(
            "Exact subject IDs that must be included for every student (repeatable). "
            "Subjects not present are ignored with a warning."
        ),
    )
    p.add_argument(
        "--must-like",
        action="append",
        default=[],
        help=(
            "Substring patterns; for each pattern, if any subject contains it, include one match. "
            "Repeat flag to require multiple patterns."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated JSON to stdout instead of writing to file",
    )
    return p.parse_args()


def read_subject_ids(path: Path, id_field: str) -> List[str]:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("subjects.json must be a JSON array")
    ids: List[str] = []
    for i, obj in enumerate(raw):
        if not isinstance(obj, dict) or id_field not in obj:
            raise ValueError(f"subjects[{i}] must be an object with field '{id_field}'")
        sid = obj[id_field]
        if not isinstance(sid, str):
            sid = str(sid)
        ids.append(sid)
    return ids


def choose_subjects(
    available: List[str],
    rng: random.Random,
    min_count: int,
    max_count: int,
    must_subjects: List[str],
    must_like: List[str],
) -> List[str]:
    if not available:
        return []
    k = rng.randint(min_count, max_count)
    # Seed with required subjects (dedup, and only those present)
    chosen: List[str] = []
    avset = set(available)

    for sid in must_subjects:
        if sid in avset and sid not in chosen:
            chosen.append(sid)

    # For each pattern, include one matched subject if present
    for pat in must_like:
        matches = [s for s in available if pat in s and s not in chosen]
        if matches:
            chosen.append(rng.choice(matches))

    # Fill remaining from the rest
    remaining = [s for s in available if s not in chosen]
    rng.shuffle(remaining)
    needed = max(0, min(k, len(available)) - len(chosen))
    chosen.extend(remaining[:needed])

    # If we overshot due to required subjects > k, randomly trim but keep required elements biased to stay
    if len(chosen) > k:
        # Try to trim non-required first
        required = set(must_subjects) | set(
            [c for c in chosen if any(p in c for p in must_like)]
        )
        non_required = [s for s in chosen if s not in required]
        rng.shuffle(non_required)
        to_trim = len(chosen) - k
        for s in non_required[:to_trim]:
            chosen.remove(s)
        # If still too many, trim randomly
        while len(chosen) > k:
            chosen.pop(rng.randrange(len(chosen)))

    return chosen


def make_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def main() -> None:
    args = parse_args()

    # Always use a Random instance (not the random module) for type-safety and isolation
    rng: random.Random = (
        random.Random(args.seed) if args.seed is not None else random.Random()
    )

    subjects_file: Path = args.subjects_file
    if not subjects_file.exists():
        raise SystemExit(f"Subjects file not found: {subjects_file}")

    available_ids = read_subject_ids(subjects_file, args.id_field)
    if not available_ids:
        raise SystemExit("No subjects found in subjects file")

    # Build students
    students = []
    next_id = int(args.id_start)
    for _ in range(int(args.count)):
        name = make_name(rng)
        subs = choose_subjects(
            available=available_ids,
            rng=rng,
            min_count=int(args.min_subjects),
            max_count=int(args.max_subjects),
            must_subjects=list(args.must_subject or []),
            must_like=list(args.must_like or []),
        )
        students.append({"id": next_id, "name": name, "subjects": subs})
        next_id += 1

    if args.dry_run:
        print(json.dumps(students, indent=4))
    else:
        out: Path = args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(students, f, indent=4)
        print(f"Wrote {len(students)} students -> {out}")


if __name__ == "__main__":
    main()
