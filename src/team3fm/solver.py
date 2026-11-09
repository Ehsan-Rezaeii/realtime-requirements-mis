"""Non-incremental and assumption-based incremental consistency checking."""

from z3 import Bool, Implies, Solver, sat, unsat
from .model import encode_rule, make_trace, observation_formulas, validate_rules


class InconclusiveError(RuntimeError):
    """The Z3 solver answered unknown (e.g. timeout), not SAT or UNSAT."""


def _solver(timeout_ms):
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise ValueError("timeout_ms must be a positive integer")
    solver = Solver()
    solver.set(timeout=timeout_ms)
    return solver


def check_nonincremental(rules, N, timeout_ms=5000, observations=None):
    """Create a fresh solver for *each* query. Returns z3.sat/unsat/unknown."""
    validate_rules(rules, N)
    trace = make_trace(rules, N, observations)
    solver = _solver(timeout_ms)
    solver.add(*observation_formulas(observations, trace))
    for rule in rules:
        solver.add(encode_rule(rule, trace, N))
    return solver.check()


class IncrementalChecker:
    """Encode each rule once and turn it on/off through assumption literals."""

    def __init__(self, rules, N, timeout_ms=5000, observations=None):
        validate_rules(rules, N)
        self.rules = list(rules)
        self.N = N
        self.trace = make_trace(rules, N, observations)
        self.solver = _solver(timeout_ms)
        self.solver.add(*observation_formulas(observations, self.trace))
        self.switches = {}
        for i, rule in enumerate(rules):
            flag = Bool(f"__rule_enabled_{i}")
            self.switches[rule["id"]] = flag
            self.solver.add(Implies(flag, encode_rule(rule, self.trace, N)))

    def check(self, selected_rules=None):
        if selected_rules is None:
            selected_rules = self.rules
        assumptions = []
        seen = set()
        for rule in selected_rules:
            rid = rule["id"] if isinstance(rule, dict) else rule
            if rid not in self.switches:
                raise ValueError(f"unknown rule id: {rid}")
            if rid in seen:
                raise ValueError(f"duplicate selected rule id: {rid}")
            seen.add(rid)
            assumptions.append(self.switches[rid])
        return self.solver.check(*assumptions)

    def core_ids(self):
        """Call immediately after an UNSAT result on the same checker."""
        reverse = {str(flag): rid for rid, flag in self.switches.items()}
        return {reverse[str(flag)] for flag in self.solver.unsat_core()}


def require_decided(result):
    if result not in (sat, unsat):
        raise InconclusiveError(f"Z3 returned {result}; do not treat unknown as SAT/UNSAT")
    return result
