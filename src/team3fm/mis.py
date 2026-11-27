"""One inclusion-minimal inconsistent subset with fixed observations."""

from z3 import sat, unsat

from .solver import IncrementalChecker, check_nonincremental


def _delete(candidate, check):
    for rule in list(candidate):
        reduced = [r for r in candidate if r["id"] != rule["id"]]
        if check(reduced) == unsat:
            candidate = reduced
    return candidate


def mis_nonincremental(rules, N, timeout_ms=5000, observations=None):
    """Deletion using a fresh solver for every subset query."""
    def check(subset):
        return check_nonincremental(subset, N, timeout_ms, observations, decided=True)

    return [] if check(rules) == sat else _delete(list(rules), check)


def mis_incremental(rules, N, timeout_ms=5000, observations=None):
    """Deletion using one assumption-based solver."""
    checker = IncrementalChecker(rules, N, timeout_ms, observations)

    def check(subset):
        return checker.check(subset, decided=True)

    return [] if check(rules) == sat else _delete(list(rules), check)


def mis_core_deletion(rules, N, timeout_ms=5000, observations=None):
    """Return the raw core and its inclusion-minimal reduction."""
    checker = IncrementalChecker(rules, N, timeout_ms, observations)
    if checker.check(decided=True) == sat:
        return [], []
    core_ids = checker.core_ids()
    core = [r for r in rules if r["id"] in core_ids]
    if not core:
        raise ValueError("UNSAT has empty requirement core: check fixed observations")
    return core, _delete(core, lambda subset: checker.check(subset, decided=True))


def mis_quickxplain(rules, N, timeout_ms=5000, observations=None):
    """Split and explain a conflict using an incremental consistency oracle."""
    checker = IncrementalChecker(rules, N, timeout_ms, observations)
    if checker.check(decided=True) == sat:
        return []

    def explain(background, added, candidates):
        if added and checker.check(background, decided=True) == unsat:
            return []
        if len(candidates) == 1:
            return candidates
        mid = len(candidates) // 2
        left, right = candidates[:mid], candidates[mid:]
        right_conflict = explain(background + left, left, right)
        left_conflict = explain(background + right_conflict, right_conflict, left)
        return left_conflict + right_conflict

    return explain([], [], list(rules))


def validate_mis(mis, N, timeout_ms=5000, observations=None, *, rules=None):
    """Verify membership, inconsistency and SAT after every single deletion."""
    if not mis:
        return False
    if rules is not None:
        original = {rule["id"]: rule for rule in rules}
        if any(original.get(rule["id"]) != rule for rule in mis):
            return False

    def check(subset):
        return check_nonincremental(subset, N, timeout_ms, observations, decided=True)

    return check(mis) == unsat and all(
        check(mis[:i] + mis[i + 1:]) == sat for i in range(len(mis))
    )


MIS_METHODS = {
    "nonincremental": mis_nonincremental,
    "incremental": mis_incremental,
    "core": lambda rules, N, timeout_ms=5000, observations=None:
        mis_core_deletion(rules, N, timeout_ms, observations)[1],
    "quickxplain": mis_quickxplain,
}
