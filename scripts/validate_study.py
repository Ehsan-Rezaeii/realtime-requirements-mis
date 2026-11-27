"""Independently audit run outcomes by evaluating finite Boolean traces in Python."""

import argparse
import csv
import json
from collections import defaultdict
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from team3fm.study import FILES, consistency_queries  # workload selection only


def signals(rule):
    if rule["type"] in ("invariant", "absence", "recurrence"):
        return (rule["signal"],)
    return (rule["trigger"], rule["target"])


def possible(rule, trace, N):
    """A False means the current partial trace cannot satisfy this rule."""
    kind = rule["type"]
    if kind in ("invariant", "absence"):
        return all(value != (kind == "absence") for value in trace[rule["signal"]])
    if kind == "recurrence":
        sequence = trace[rule["signal"]]
        width = rule["window"]
        return all(any(x is not False for x in sequence[i:i + width])
                   for i in range(len(sequence) + 1 - width))
    lower, upper = (0, rule["deadline"]) if kind == "response" else (
        rule["min_delay"], rule["max_delay"]
    )
    target = trace[rule["target"]]
    for t, value in enumerate(trace[rule["trigger"]]):
        if value is True and all(x is False for x in target[t + lower:min(t + upper + 1, N + 1)]):
            return False
    return True


def component_status(names, rules, observations, N):
    fixed = {}

    def assign(key, value):
        old = fixed.setdefault(key, value)
        return old == value

    for obs in observations:
        if not assign((obs["signal"], obs["time"]), obs["value"]):
            return "unsat"
    for rule in rules:
        kind = rule["type"]
        if kind in ("invariant", "absence"):
            for t in range(N + 1):
                if not assign((rule["signal"], t), kind == "invariant"):
                    return "unsat"
    trace = {name: [fixed.get((name, t)) for t in range(N + 1)] for name in sorted(names)}
    if not all(possible(rule, trace, N) for rule in rules):
        return "unsat"

    free = [(name, t) for name, seq in trace.items() for t, value in enumerate(seq) if value is None]
    targets = {rule["target"] for rule in rules if rule["type"] in ("response", "bounded_delay")}
    for pattern in (set(), set(names), targets):
        for name, t in free:
            trace[name][t] = name in pattern
        if all(possible(rule, trace, N) for rule in rules):
            return "sat"

    if len(free) > 20:
        return "not_checked"
    for values in product((False, True), repeat=len(free)):
        for (name, t), value in zip(free, values):
            trace[name][t] = value
        if all(possible(rule, trace, N) for rule in rules):
            return "sat"
    return "unsat"


def independent_status(rules, N, observations=()):
    """Search exactly within small connected components, using direct witnesses for large SAT cases."""
    parent = {}

    def root(node):
        parent.setdefault(node, node)
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for rule in rules:
        names = signals(rule)
        parent[root(names[-1])] = root(names[0])
    for obs in observations:
        root(obs["signal"])
    components = defaultdict(set)
    groups = defaultdict(list)
    fixed = defaultdict(list)
    for name in parent:
        components[root(name)].add(name)
    for rule in rules:
        groups[root(signals(rule)[0])].append(rule)
    for obs in observations:
        fixed[root(obs["signal"])].append(obs)

    undecided = False
    for key, names in components.items():
        status = component_status(names, groups[key], fixed[key], N)
        if status == "unsat":
            return status
        undecided |= status == "not_checked"
    return "not_checked" if undecided else "sat"


def audit(study, output):
    cases = {path.stem: json.loads(path.read_text(encoding="utf-8"))
             for path in sorted((study / "cases").glob("*.json"))}
    observed = defaultdict(lambda: defaultdict(set))
    skips = defaultdict(int)
    for exp, filename in FILES.items():
        with (study / "raw" / filename).open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                if row["status"] == "ok":
                    observed[row["case_id"]][exp].add(row["result"])
                    if exp == "mis" and row["mis_ids"]:
                        observed[row["case_id"]]["candidates"].add(tuple(sorted(row["mis_ids"].split(";"))))
                else:
                    skips[row["case_id"]] += 1

    fields = ["case_id", "num_rules", "N", "test", "expected", "observed", "status"]
    rows = []
    for case_id, case in cases.items():
        rules, N = case["rules"], case["N"]
        assumptions = case.get("observations", [])
        by_id = {rule["id"]: rule for rule in rules}
        measured = observed[case_id]

        def check(subset):
            return independent_status(subset, N, assumptions)

        def record(test, expected, actual):
            status = "not_checked" if "not_checked" in actual else ("pass" if expected == actual else "fail")
            rows.append([case_id, len(rules), N, test, expected, actual, status])

        def validate_candidate(ids, label):
            if not set(ids) <= by_id.keys():
                record(label, "member", "nonmember")
                return
            candidate = [by_id[rid] for rid in ids]
            record(label + " " + ";".join(ids), "unsat", check(candidate))
            for i, rule in enumerate(candidate):
                record(f"{label} remove {rule['id']}", "sat", check(candidate[:i] + candidate[i + 1:]))

        oracle = check(rules)
        record("full set", case["expected_status"], oracle)
        for actual in sorted(measured["rq4"] | measured["mis"]):
            record("reported full set", actual, oracle)
        if measured["rq1"]:
            subsets, _ = consistency_queries(case)
            independently_computed = ";".join(check(subset) for subset in subsets)
            for actual in sorted(measured["rq1"]):
                record("RQ1 ordered outcomes", actual, independently_computed)
        injected = tuple(sorted(case.get("injected_ids", [])))
        if injected:
            record("background without injection", "sat",
                   check([r for r in rules if r["id"] not in injected]))
            validate_candidate(injected, "injected subset")
        for ids in sorted(measured["candidates"]):
            validate_candidate(ids, "reported MIS")
        if skips[case_id]:
            rows.append([case_id, len(rules), N, "non-ok run rows", "", str(skips[case_id]), "not_applicable"])

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)
    counts = {status: sum(row[-1] == status for row in rows)
              for status in ("pass", "fail", "not_checked", "not_applicable")}
    print(json.dumps(counts))
    return 1 if counts["fail"] or counts["not_checked"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("results/final"))
    parser.add_argument("--output", type=Path, default=Path("results/validation/independent_validation.csv"))
    args = parser.parse_args()
    raise SystemExit(audit(args.study, args.output))
