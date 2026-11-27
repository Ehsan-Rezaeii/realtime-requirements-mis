"""Run one timed operation in an isolated process."""

import json
import sys
from pathlib import Path
from time import perf_counter

if __name__ == "__main__" and sys.platform.startswith("linux"):
    import resource

    limit_bytes = int(sys.argv[5]) * 1024**2
    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

# Direct script invocation supports both source checkouts and an installed package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from team3fm.dataio import load_dataset
from team3fm.mis import MIS_METHODS, mis_core_deletion, validate_mis
from team3fm.solver import InconclusiveError, IncrementalChecker, check_nonincremental, measure_solver
from team3fm.study import consistency_queries


def evaluate(case, experiment, method, timeout, seed):
    rules, N = case["rules"], case["N"]
    observations = case.get("observations")
    expected = case["expected_status"]
    result = {}
    start = perf_counter()

    try:
        with measure_solver(seed) as stats:
            if experiment == "mis":
                if method == "core":
                    core, mis = mis_core_deletion(rules, N, timeout, observations)
                    result["core_size"] = len(core)
                else:
                    mis = MIS_METHODS[method](rules, N, timeout, observations)
                result.update(result="unsat" if mis else "sat", mis_size=len(mis),
                              mis_ids=";".join(rule["id"] for rule in mis))
            else:
                subsets, expected_outcomes = consistency_queries(case) if experiment == "rq1" else ([rules], [expected])
                outcomes = []
                result["num_checks"] = len(subsets)
                if method == "incremental":
                    checker = IncrementalChecker(rules, N, timeout, observations)
                    for subset in subsets:
                        outcomes.append(str(checker.check(subset, decided=True)))
                else:
                    for subset in subsets:
                        outcomes.append(str(check_nonincremental(subset, N, timeout, observations, decided=True)))
                result["result"] = ";".join(outcomes)
                result["status"] = "ok" if outcomes == expected_outcomes else "invalid"
            result.update(stats, wall_time_seconds=perf_counter() - start)
    except InconclusiveError as exc:
        if experiment != "mis":
            outcomes.append("unknown")
            result["outcomes"] = ";".join(outcomes)
        return {**result, **stats, "result": "unknown", "status": exc.status,
                "wall_time_seconds": perf_counter() - start, "error": str(exc)}

    if experiment == "mis":
        validation_start = perf_counter()
        try:
            valid = validate_mis(mis, N, timeout, observations, rules=rules) if mis else None
            result["minimal"] = valid
            result["status"] = "ok" if result["result"] == expected and valid is not False else "invalid"
            injected = case.get("injected_ids")
            if injected:
                result["injection_recovered"] = set(injected) == {rule["id"] for rule in mis}
        except InconclusiveError as exc:
            result.update(status=exc.status, error=f"MIS validation: {exc}")
        result["validation_seconds"] = perf_counter() - validation_start
    return result


if __name__ == "__main__":
    try:
        data, experiment, method, timeout, _, seed = sys.argv[1:]
        print(json.dumps(evaluate(load_dataset(data), experiment, method, int(timeout), int(seed))))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}))
