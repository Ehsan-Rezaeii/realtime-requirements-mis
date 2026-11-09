"""Reproducible controlled synthetic requirement sets with a 2/3/4-rule MIS."""

import random


def generate_case(total_rules, mis_size=3, N=5, seed=42, style="mixed"):
    """Generate a known MIS and consistent background; no GPU/LLM needed.

    style='simple': independent absence constraints.
    style='mixed': linked but satisfiable, deliberately simple patterns.
    Seeds alter rule ordering, not the underlying logical background.
    """
    if isinstance(total_rules, bool) or not isinstance(total_rules, int):
        raise ValueError("total_rules must be an integer")
    if mis_size not in (2, 3, 4) or total_rules < mis_size:
        raise ValueError("mis_size must be 2, 3, or 4 and total_rules >= mis_size")
    if isinstance(N, bool) or not isinstance(N, int) or N < 2:
        raise ValueError("N must be an integer >= 2 for the synthetic generator")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if style not in ("simple", "mixed"):
        raise ValueError("style must be 'simple' or 'mixed'")

    if mis_size == 2:
        injected = [
            {"id": "R1", "type": "invariant", "signal": "alarm"},
            {"id": "R2", "type": "absence", "signal": "alarm"},
        ]
    elif mis_size == 3:
        injected = [
            {"id": "R1", "type": "recurrence", "signal": "request", "window": N + 1},
            {"id": "R2", "type": "response", "trigger": "request", "target": "grant", "deadline": 2},
            {"id": "R3", "type": "absence", "signal": "grant"},
        ]
    else:
        injected = [
            {"id": "R1", "type": "invariant", "signal": "a"},
            {"id": "R2", "type": "response", "trigger": "a", "target": "b", "deadline": 0},
            {"id": "R3", "type": "response", "trigger": "b", "target": "c", "deadline": 0},
            {"id": "R4", "type": "absence", "signal": "c"},
        ]

    background = []
    for i in range(total_rules - mis_size):
        if style == "simple":
            rule = {"type": "absence", "signal": f"noise_{i+1:04d}"}
        else:
            group, kind = divmod(i, 6)
            a, b, c = f"bg_on_{group}", f"bg_ack_{group}", f"bg_off_{group}"
            if kind == 0:
                rule = {"type": "invariant", "signal": a}
            elif kind == 1:
                rule = {"type": "invariant", "signal": b}
            elif kind == 2:
                rule = {"type": "response", "trigger": a, "target": b, "deadline": 1}
            elif kind == 3:
                rule = {"type": "recurrence", "signal": a, "window": 2}
            elif kind == 4:
                rule = {"type": "bounded_delay", "trigger": a, "target": b,
                        "min_delay": 0, "max_delay": 2}
            else:
                rule = {"type": "absence", "signal": c}
        background.append({"id": f"B{i+1:04d}", **rule})

    rules = injected + background
    random.Random(seed).shuffle(rules)
    return {
        "case_id": f"{style}_mis{mis_size}_{total_rules}",
        "N": N,
        "seed": seed,
        "generator": style,
        "injected_ids": [r["id"] for r in injected],
        "rules": rules,
    }
