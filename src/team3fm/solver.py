"""Fresh-solver and assumption-based checks over the same finite trace."""

from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

from z3 import Bool, Implies, Solver, sat, unsat

from .model import encode_rule, make_trace, observation_formulas


class InconclusiveError(RuntimeError):
    """Z3 cannot decide a query within its current limits."""

    def __init__(self, reason):
        self.reason = reason
        self.status = "timeout" if "timeout" in reason.lower() else "unknown"
        super().__init__(f"Z3 returned unknown: {reason}")


_measurement = ContextVar("solver_measurement", default=None)


@contextmanager
def measure_solver(seed=0):
    """Collect timings and calls for one benchmark operation."""
    stats = {"build_seconds": 0.0, "solving_seconds": 0.0, "solver_calls": 0}
    token = _measurement.set((seed, stats))
    try:
        yield stats
    finally:
        _measurement.reset(token)


def _solver(timeout_ms):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("timeout_ms must be a positive integer")
    solver = Solver()
    measurement = _measurement.get()
    solver.set(timeout=timeout_ms, random_seed=measurement[0] if measurement else 0)
    return solver


def _record_build(start):
    measurement = _measurement.get()
    if measurement:
        measurement[1]["build_seconds"] += perf_counter() - start


def _check(solver, assumptions, decided):
    start = perf_counter()
    result = solver.check(*assumptions)
    measurement = _measurement.get()
    if measurement:
        stats = measurement[1]
        stats["solving_seconds"] += perf_counter() - start
        stats["solver_calls"] += 1
    if decided and result not in (sat, unsat):
        raise InconclusiveError(solver.reason_unknown())
    return result


def check_nonincremental(rules, N, timeout_ms=5000, observations=None, *, decided=False):
    """Construct a fresh solver per query and return SAT, UNSAT or UNKNOWN."""
    start = perf_counter()
    trace = make_trace(rules, N, observations)
    solver = _solver(timeout_ms)
    solver.add(*observation_formulas(observations, trace))
    solver.add(*(encode_rule(rule, trace, N) for rule in rules))
    _record_build(start)
    return _check(solver, (), decided)


class IncrementalChecker:
    """Encode each rule once and activate it through an assumption literal."""

    def __init__(self, rules, N, timeout_ms=5000, observations=None):
        start = perf_counter()
        self.trace = make_trace(rules, N, observations)
        self.rules = list(rules)
        self.N = N
        self.solver = _solver(timeout_ms)
        self.solver.add(*observation_formulas(observations, self.trace))
        self.switches = {}
        constraints = []
        for i, rule in enumerate(rules):
            flag = Bool(f"activation:{i}")
            self.switches[rule["id"]] = flag
            constraints.append(Implies(flag, encode_rule(rule, self.trace, N)))
        self.solver.add(*constraints)
        _record_build(start)

    def check(self, selected_rules=None, *, decided=False):
        if selected_rules is None:
            selected_rules = self.rules
        assumptions = []
        seen = set()
        for rule in selected_rules:
            rid = rule.get("id") if isinstance(rule, dict) else rule
            if not isinstance(rid, str) or rid not in self.switches:
                raise ValueError(f"unknown rule id: {rid}")
            if rid in seen:
                raise ValueError(f"duplicate selected rule id: {rid}")
            seen.add(rid)
            assumptions.append(self.switches[rid])
        return _check(self.solver, assumptions, decided)

    def core_ids(self):
        """Read the assumptions in the last UNSAT proof."""
        reverse = {flag: rid for rid, flag in self.switches.items()}
        return {reverse[flag] for flag in self.solver.unsat_core()}


def require_decided(result):
    if result not in (sat, unsat):
        raise InconclusiveError(str(result))
    return result
