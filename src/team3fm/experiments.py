"""Small reproducible pilot experiments; append one raw result per completed run."""

import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import z3
from z3 import sat, unsat

from .generator import generate_case
from .mis import MIS_METHODS, validate_mis
from .solver import IncrementalChecker, check_nonincremental


class RawCsv:
    def __init__(self, path, fields):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fields = fields
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()

    def add(self, row):
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writerow(row)


def _env(config, out_dir):
    metadata = {
        "experiment_note": "pilot; raw times are local and not guarantees of general performance",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "z3": z3.get_version_string(),
        "system": platform.platform(),
        "config": config,
        "timeout_scope": "per Z3 Solver.check, not end-to-end operation",
        "timing_scope": "end-to-end construction and solving; external MIS validation not timed",
    }
    path = Path(out_dir) / "environment.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _cfg(config):
    sizes = config["sizes"]
    if not isinstance(sizes, list) or not sizes or any(type(x) is not int or x < 5 for x in sizes):
        raise ValueError("sizes must be a nonempty list of integers >= 5")
    if type(config["repeats"]) is not int or config["repeats"] < 1:
        raise ValueError("repeats must be >= 1")
    if type(config["timeout_ms"]) is not int or config["timeout_ms"] <= 0:
        raise ValueError("timeout_ms must be positive")
    if type(config["N"]) is not int or config["N"] < 2:
        raise ValueError("N must be >= 2")
    if config["mis_size"] not in (2, 3, 4):
        raise ValueError("mis_size must be 2, 3, or 4")
    if min(sizes) < config["mis_size"]:
        raise ValueError("sizes too small for mis_size")
    if config["style"] not in ("mixed", "simple"):
        raise ValueError("style must be mixed or simple")
    if type(config["seed"]) is not int:
        raise ValueError("seed must be an integer")
    bounds = config["rq4_N_values"]
    if not isinstance(bounds, list) or not bounds or any(type(x) is not int or x < 0 for x in bounds):
        raise ValueError("rq4_N_values must be nonnegative integers")


def benchmark_mis(config, out_dir):
    """RQ2+RQ3+RQ5: MIS timing, correctness, and scaling with rule count."""
    _cfg(config)
    out_dir = Path(out_dir)
    fields = ["num_rules", "N", "seed", "repetition", "method", "time_seconds",
              "mis_size", "mis_ids", "minimal", "injection_recovered", "status", "error"]
    sink = RawCsv(out_dir / "rq2_rq3_rq5_mis.csv", fields)
    for size in config["sizes"]:
        case = generate_case(size, config["mis_size"], config["N"], config["seed"], config["style"])
        rules = case["rules"]
        expected_ids = set(case["injected_ids"])
        for rep in range(1, config["repeats"] + 1):
            names = list(MIS_METHODS)
            shift = (rep - 1) % len(names)
            for method_name in names[shift:] + names[:shift]:
                status, error, minimal, recovered, mis, elapsed = "ok", "", False, False, [], None
                start = time.perf_counter()
                try:
                    mis = MIS_METHODS[method_name](rules, config["N"], config["timeout_ms"])
                    elapsed = time.perf_counter() - start
                    # Independent validation deliberately EXCLUDED from timed operation.
                    minimal = validate_mis(mis, config["N"], config["timeout_ms"])
                    recovered = {r["id"] for r in mis} == expected_ids
                    if not minimal or not recovered:
                        status = "invalid"
                except Exception as exc:
                    if elapsed is None:
                        elapsed = time.perf_counter() - start
                    status = "unknown" if "unknown" in str(exc).lower() else "error"
                    error = f"{type(exc).__name__}: {exc}"
                sink.add({
                    "num_rules": size, "N": config["N"], "seed": config["seed"],
                    "repetition": rep, "method": method_name, "time_seconds": elapsed,
                    "mis_size": len(mis), "mis_ids": ",".join(r["id"] for r in mis),
                    "minimal": minimal, "injection_recovered": recovered,
                    "status": status, "error": error,
                })
        print(f"MIS: finished size={size}")
    return sink.path


def _subsets(case):
    rules = case["rules"]
    injected = case["injected_ids"]
    background = next((r["id"] for r in rules if r["id"] not in injected), None)
    items = [("all", rules, "unsat")]
    for rid in injected:
        items.append((f"without_{rid}", [r for r in rules if r["id"] != rid], "sat"))
    if background:
        items.append(("without_background", [r for r in rules if r["id"] != background], "unsat"))
    return items


def _consistency_batch(method, rules, N, subsets, timeout):
    if method == "incremental":
        checker = IncrementalChecker(rules, N, timeout)
        return [str(checker.check(subset)) for _, subset, _ in subsets]
    return [str(check_nonincremental(subset, N, timeout)) for _, subset, _ in subsets]


def benchmark_consistency(config, out_dir):
    """RQ1: same subsets, total construction + solving time per batch."""
    _cfg(config)
    sink = RawCsv(Path(out_dir) / "rq1_consistency.csv", [
        "num_rules", "N", "seed", "repetition", "method", "num_checks",
        "batch_seconds", "outcomes", "expected", "status", "error",
    ])
    for size in config["sizes"]:
        case = generate_case(size, config["mis_size"], config["N"], config["seed"], config["style"])
        rules, N = case["rules"], case["N"]
        subsets = _subsets(case)
        expected = [item[2] for item in subsets]
        for rep in range(1, config["repeats"] + 1):
            methods = ["nonincremental", "incremental"]
            if rep % 2 == 0:
                methods.reverse()
            for method in methods:
                start = time.perf_counter()
                outcomes, error = [], ""
                try:
                    outcomes = _consistency_batch(method, rules, N, subsets, config["timeout_ms"])
                    status = "unknown" if "unknown" in outcomes else ("ok" if outcomes == expected else "mismatch")
                except Exception as exc:
                    status, error = "error", f"{type(exc).__name__}: {exc}"
                elapsed = time.perf_counter() - start
                sink.add({
                    "num_rules": size, "N": N, "seed": config["seed"],
                    "repetition": rep, "method": method, "num_checks": len(subsets),
                    "batch_seconds": elapsed, "outcomes": ",".join(outcomes),
                    "expected": ",".join(expected), "status": status, "error": error,
                })
        print(f"RQ1: finished size={size}")
    return sink.path


def _bound_case(name, N):
    if name == "late_conflict":
        rules = [
            {"id": "R1", "type": "response", "trigger": "request", "target": "grant", "deadline": 1},
            {"id": "R2", "type": "absence", "signal": "grant"},
        ]
        # The event is only within the modeled horizon if N >= 3.
        observations = [{"signal": "request", "time": 3, "value": True}] if N >= 3 else []
        expected = "unsat" if N >= 3 else "sat"
    elif name == "always_unsat":
        rules = [{"id": "R1", "type": "invariant", "signal": "a"},
                 {"id": "R2", "type": "absence", "signal": "a"}]
        observations, expected = [], "unsat"
    elif name == "always_sat":
        rules = [{"id": "R1", "type": "absence", "signal": "a"},
                 {"id": "R2", "type": "absence", "signal": "b"}]
        observations, expected = [], "sat"
    else:
        raise ValueError(name)
    return rules, observations, expected


def benchmark_bounds(config, out_dir):
    """RQ4: horizon sensitivity; uniform end-to-end time for all three scenarios."""
    _cfg(config)
    sink = RawCsv(Path(out_dir) / "rq4_bound_effect.csv", [
        "scenario", "N", "repetition", "method", "time_seconds", "result", "expected", "status", "error",
    ])
    for name in ("late_conflict", "always_unsat", "always_sat"):
        for N in config["rq4_N_values"]:
            rules, observations, expected = _bound_case(name, N)
            for rep in range(1, config["repeats"] + 1):
                start = time.perf_counter()
                try:
                    result = str(check_nonincremental(rules, N, config["timeout_ms"], observations))
                    status = "unknown" if result == "unknown" else ("ok" if result == expected else "mismatch")
                    error = ""
                except Exception as exc:
                    result, status, error = "", "error", f"{type(exc).__name__}: {exc}"
                elapsed = time.perf_counter() - start
                sink.add({
                    "scenario": name, "N": N, "repetition": rep,
                    "method": "nonincremental", "time_seconds": elapsed,
                    "result": result, "expected": expected, "status": status, "error": error,
                })
    return sink.path


def run_experiments(config, mode="all"):
    _cfg(config)
    out_dir = Path(config["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    _env(config, out_dir)
    files = []
    if mode in ("mis", "all"):
        files.append(benchmark_mis(config, out_dir))
    if mode in ("consistency", "all"):
        files.append(benchmark_consistency(config, out_dir))
    if mode in ("bounds", "all"):
        files.append(benchmark_bounds(config, out_dir))
    return files
