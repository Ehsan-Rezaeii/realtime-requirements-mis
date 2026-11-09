"""Simple JSON dataset validation, loading, and saving."""

import json
from pathlib import Path
from .model import validate_observations, validate_rules


def validate_dataset(data):
    if not isinstance(data, dict):
        raise ValueError("dataset must be a JSON object")
    if not isinstance(data.get("case_id"), str) or not data["case_id"].strip():
        raise ValueError("dataset needs a nonempty case_id")
    N, rules = data.get("N"), data.get("rules")
    validate_rules(rules, N)
    validate_observations(data.get("observations"), N)
    ids = {r["id"] for r in rules}
    injected = data.get("injected_ids", [])
    if not isinstance(injected, list) or any(not isinstance(x, str) for x in injected):
        raise ValueError("injected_ids must be a list of rule ids")
    if len(set(injected)) != len(injected) or not set(injected).issubset(ids):
        raise ValueError("injected_ids must be unique and included in rules")
    return data


def load_dataset(path):
    with open(path, encoding="utf-8") as f:
        return validate_dataset(json.load(f))


def save_dataset(data, path):
    validate_dataset(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path
