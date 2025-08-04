import json
from pathlib import Path
from typing import List

from models.constraints import BaseConstraint

# Map simple names → fully-qualified class
_CONSTRAINT_CLASS_MAP = {
    cls.__name__: cls for cls in BaseConstraint.__subclasses__()  # only 1 level deep
}


def _class_from_type(type_name: str):
    try:
        return _CONSTRAINT_CLASS_MAP[type_name]
    except KeyError:
        raise ValueError(f"Unknown constraint type: {type_name}")


def load_constraints(json_path: str | Path) -> List[BaseConstraint]:
    """Read JSON file -> list of instantiated constraints."""
    with open(json_path, "r", encoding="utf-8") as fh:
        specs = json.load(fh)

    constraints = []
    for spec in specs:
        spec = spec.copy()  # don't mutate original
        type_name = spec.pop("type")  # remove mandatory key
        cls = _class_from_type(type_name)
        constraints.append(cls(**spec))
    return constraints
