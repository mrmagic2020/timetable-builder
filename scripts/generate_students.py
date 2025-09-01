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
        "--min-cycles",
        type=int,
        default=60,
        help="Minimum total cycles per student",
    )
    p.add_argument(
        "--max-cycles",
        type=int,
        default=60,
        help="Maximum total cycles per student",
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


def read_subjects_data(path: Path, id_field: str) -> tuple[List[str], dict[str, int]]:
    """Read subject IDs and their cycle requirements from the subjects file."""
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("subjects.json must be a JSON array")
    ids: List[str] = []
    cycles: dict[str, int] = {}
    for i, obj in enumerate(raw):
        if not isinstance(obj, dict) or id_field not in obj:
            raise ValueError(f"subjects[{i}] must be an object with field '{id_field}'")
        sid = obj[id_field]
        if not isinstance(sid, str):
            sid = str(sid)
        ids.append(sid)
        
        # Read the required_per_cycle field
        cycles_required = obj.get("required_per_cycle", 0)
        if not isinstance(cycles_required, int):
            cycles_required = int(cycles_required)
        cycles[sid] = cycles_required
    return ids, cycles


def choose_subjects(
    available: List[str],
    subject_cycles: dict[str, int],
    rng: random.Random,
    min_cycles: int,
    max_cycles: int,
    must_subjects: List[str],
    must_like: List[str],
) -> List[str]:
    """Choose subjects based on total cycle requirements rather than subject count."""
    if not available:
        return []
    
    target_cycles = rng.randint(min_cycles, max_cycles)
    chosen: List[str] = []
    current_cycles = 0
    avset = set(available)

    # Seed with required subjects (dedup, and only those present)
    for sid in must_subjects:
        if sid in avset and sid not in chosen:
            chosen.append(sid)
            current_cycles += subject_cycles.get(sid, 0)

    # For each pattern, include one matched subject if present
    for pat in must_like:
        matches = [s for s in available if pat in s and s not in chosen]
        if matches:
            selected = rng.choice(matches)
            chosen.append(selected)
            current_cycles += subject_cycles.get(selected, 0)

    # Fill remaining from the rest to reach target cycles
    remaining = [s for s in available if s not in chosen]
    rng.shuffle(remaining)
    
    for subject in remaining:
        subject_cycle_cost = subject_cycles.get(subject, 0)
        if current_cycles + subject_cycle_cost <= target_cycles:
            chosen.append(subject)
            current_cycles += subject_cycle_cost
        # Stop if we've reached our target or if adding any remaining subject would exceed it
        if current_cycles >= min_cycles and all(
            current_cycles + subject_cycles.get(s, 0) > target_cycles 
            for s in remaining if s not in chosen
        ):
            break

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

    available_ids, subject_cycles = read_subjects_data(subjects_file, args.id_field)
    if not available_ids:
        raise SystemExit("No subjects found in subjects file")

    # Build students
    students = []
    next_id = int(args.id_start)
    for _ in range(int(args.count)):
        name = make_name(rng)
        subs = choose_subjects(
            available=available_ids,
            subject_cycles=subject_cycles,
            rng=rng,
            min_cycles=int(args.min_cycles),
            max_cycles=int(args.max_cycles),
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
