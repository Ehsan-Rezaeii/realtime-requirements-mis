"""Finite-trace Boolean temporal patterns over time steps 0..N (inclusive)."""

from z3 import And, Bool, Implies, Not, Or

PATTERNS = {"invariant", "absence", "response", "recurrence", "bounded_delay"}


def _nonnegative_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def validate_rules(rules, N):
    """Validate a list of simple requirement dictionaries before encoding."""
    _nonnegative_int(N, "N")
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")

    ids = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("each rule must be a dictionary")
        rid, kind = rule.get("id"), rule.get("type")
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError("every rule needs a nonempty string id")
        if rid in ids:
            raise ValueError(f"duplicate rule id: {rid}")
        ids.add(rid)
        if kind not in PATTERNS:
            raise ValueError(f"unsupported requirement type: {kind}")

        fields = ("signal",) if kind in ("invariant", "absence", "recurrence") else ("trigger", "target")
        for field in fields:
            if not isinstance(rule.get(field), str) or not rule[field].strip():
                raise ValueError(f"{rid}: {field} must be a nonempty string")

        if kind == "response":
            _nonnegative_int(rule.get("deadline"), f"{rid}.deadline")
        elif kind == "recurrence":
            window = _nonnegative_int(rule.get("window"), f"{rid}.window")
            if not 1 <= window <= N + 1:
                raise ValueError(f"{rid}: window must be between 1 and N+1")
        elif kind == "bounded_delay":
            lower = _nonnegative_int(rule.get("min_delay"), f"{rid}.min_delay")
            upper = _nonnegative_int(rule.get("max_delay"), f"{rid}.max_delay")
            if lower > upper:
                raise ValueError(f"{rid}: min_delay cannot exceed max_delay")


def validate_observations(observations, N):
    """Validate fixed, external observations; they are NOT candidate MIS members."""
    _nonnegative_int(N, "N")
    if observations is None:
        return []
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    seen = {}
    for obs in observations:
        if not isinstance(obs, dict):
            raise ValueError("observation must be a dictionary")
        sig, t, value = obs.get("signal"), obs.get("time"), obs.get("value")
        if not isinstance(sig, str) or not sig.strip():
            raise ValueError("observation signal must be nonempty")
        if isinstance(t, bool) or not isinstance(t, int) or not 0 <= t <= N:
            raise ValueError(f"observation time must be between 0 and N={N}")
        if not isinstance(value, bool):
            raise ValueError("observation value must be true or false")
        key = (sig, t)
        if key in seen and seen[key] != value:
            raise ValueError(f"conflicting observations at {sig}[{t}]")
        seen[key] = value
    return observations


def make_trace(rules, N, observations=None):
    validate_rules(rules, N)
    observations = validate_observations(observations, N)
    names = set()
    for rule in rules:
        for key in ("signal", "trigger", "target"):
            if key in rule:
                names.add(rule[key])
    for obs in observations:
        names.add(obs["signal"])
    return {name: [Bool(f"{name}_{t}") for t in range(N + 1)] for name in sorted(names)}


def encode_rule(rule, trace, N):
    """Translate one validated rule into a Z3 Boolean formula."""
    kind = rule["type"]
    if kind == "invariant":
        x = trace[rule["signal"]]
        return And([x[t] for t in range(N + 1)])
    if kind == "absence":
        x = trace[rule["signal"]]
        return And([Not(x[t]) for t in range(N + 1)])
    if kind == "response":
        a, b, d = trace[rule["trigger"]], trace[rule["target"]], rule["deadline"]
        return And([
            Implies(a[t], Or([b[j] for j in range(t, min(t + d, N) + 1)]))
            for t in range(N + 1)
        ])
    if kind == "recurrence":
        x, window = trace[rule["signal"]], rule["window"]
        return And([
            Or([x[j] for j in range(start, start + window)])
            for start in range(N - window + 2)
        ])
    if kind == "bounded_delay":
        a, b = trace[rule["trigger"]], trace[rule["target"]]
        lower, upper = rule["min_delay"], rule["max_delay"]
        # If no legal response time exists inside 0..N, Or([]) is False.
        return And([
            Implies(a[t], Or([b[j] for j in range(t + lower, min(t + upper, N) + 1)]))
            for t in range(N + 1)
        ])
    raise ValueError(f"unsupported requirement type: {kind}")


def observation_formulas(observations, trace):
    return [
        trace[obs["signal"]][obs["time"]] if obs["value"]
        else Not(trace[obs["signal"]][obs["time"]])
        for obs in (observations or [])
    ]
