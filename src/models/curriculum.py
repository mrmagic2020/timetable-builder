from dataclasses import dataclass


@dataclass
class Subject:
    id: str
    name: str
    intensity: int  # Intensity of the subject (1-5 scale)
    required_per_cycle: int  # Number of times the subject must be taught in a cycle
    constraints: list[str]  # List of constraint IDs that apply to this subject
