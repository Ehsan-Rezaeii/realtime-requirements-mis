"""Deletion-based minimal UNSAT subsets (MIS/MUS), with and without core."""

from z3 import sat, unsat
from .model import validate_rules
from .solver import (
    IncrementalChecker,
    check_nonincremental,
    require_decided,
)


def _check_result(result):
    return require_decided(result)


def mis_nonincremental(rules, N, timeout_ms=5000, observations=None):
    """Repeat fresh-solver checks for deletion-based MIS extraction."""
    validate_rules(rules, N)
    overall = _check_result(check_nonincremental(rules, N, timeout_ms, observations))
    if overall == sat:
        return []
    candidate = list(rules)
    for rule in rules:
        reduced = [r for r in candidate if r["id"] != rule["id"]]
        if _check_result(check_nonincremental(reduced, N, timeout_ms, observations)) == unsat:
            candidate = reduced
    return candidate


def mis_incremental(rules, N, timeout_ms=5000, observations=None):
    """Deletion MIS using one assumption-based solver for all subset checks."""
    checker = IncrementalChecker(rules, N, timeout_ms, observations)
    if _check_result(checker.check()) == sat:
        return []
    candidate = list(rules)
    for rule in rules:
        reduced = [r for r in candidate if r["id"] != rule["id"]]
        if _check_result(checker.check(reduced)) == unsat:
            candidate = reduced
    return candidate


def mis_core_deletion(rules, N, timeout_ms=5000, observations=None):
    """Return (initial_unsat_core, minimized_MIS). Core is NOT necessarily minimal."""
    checker = IncrementalChecker(rules, N, timeout_ms, observations)
    if _check_result(checker.check()) == sat:
        return [], []
    core_ids = checker.core_ids()
    core = [r for r in rules if r["id"] in core_ids]
    # A contradictory fixed environment cannot be diagnosed as an MIS of rules.
    if not core:
        raise ValueError("UNSAT has empty requirement core: check external observations")
    candidate = list(core)
    for rule in core:
        reduced = [r for r in candidate if r["id"] != rule["id"]]
        if _check_result(checker.check(reduced)) == unsat:
            candidate = reduced
    return core, candidate


def validate_mis(mis, N, timeout_ms=5000, observations=None):
    """MUS test: whole set UNSAT, removing *each* member makes it SAT."""
    if not mis:
        return False
    if _check_result(check_nonincremental(mis, N, timeout_ms, observations)) != unsat:
        return False
    for rule in mis:
        subset = [r for r in mis if r["id"] != rule["id"]]
        if _check_result(check_nonincremental(subset, N, timeout_ms, observations)) != sat:
            return False
    return True


MIS_METHODS = {
    "nonincremental": mis_nonincremental,
    "incremental": mis_incremental,
    "core": lambda rules, N, timeout_ms=5000, observations=None:
        mis_core_deletion(rules, N, timeout_ms, observations)[1],
}
