"""Compare two shared global Boolean cases using Hanfor v1.2.1's simulator."""

import csv
import json
import sys
from pathlib import Path

from lib_core.data import Formalization, Requirement
from lib_core.pattern.patterns_basic import Absence, Universality
from lib_pea.countertrace import CountertraceTransformer
from lib_pea.req_to_pea import get_pea_from_formalisation
from lib_pea.utils import get_countertrace_parser
from pysmt.shortcuts import Symbol
from pysmt.typing import BOOL
from req_simulator.simulator import Simulator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from team3fm.solver import check_nonincremental

ROOT = Path(__file__).resolve().parents[1]


def simulate(rules, steps):
    automata = []
    parser = get_countertrace_parser()
    for rule in rules:
        pattern = {"invariant": Universality, "absence": Absence}[rule["type"]]()
        expression = Symbol(rule["signal"], BOOL)
        for index, text in enumerate(pattern.get_countertraces("GLOBALLY")):
            ct = CountertraceTransformer({"R": expression}).transform(parser.parse(text))
            req = Requirement(rule["id"], "", "", {}, 0)
            formalization = Formalization(fid=0)
            automaton = get_pea_from_formalisation(req, formalization, index, ct)
            automaton.requirement = req
            automaton.formalization = formalization
            automaton.countertrace_id = index
            automata.append(automaton)
    simulator = Simulator(automata)
    for _ in range(steps):
        if not simulator.check_sat():
            return "blocked_at_step", simulator.sat_error
        simulator.step_next(0)
    return "trace_found", ""


def main():
    source = ROOT / "benchmarks/public/hanfor_boolean_example.json"
    case = json.loads(source.read_text(encoding="utf-8"))
    left, right = case["rules"]
    variant = [left, {**right, "signal": left["signal"]}]
    writer = csv.writer(sys.stdout)
    writer.writerow(["case_id", "steps", "project_z3", "hanfor_simulator", "details", "agreement"])
    for name, rules, expected in [
        (case["case_id"], case["rules"], "trace_found"),
        ("hanfor_boolean_same_signal_conflict", variant, "blocked_at_step"),
    ]:
        steps = case["N"] + 1
        result = str(check_nonincremental(rules, case["N"]))
        simulated, error = simulate(rules, steps)
        agreement = simulated == expected and result == ("sat" if expected == "trace_found" else "unsat")
        writer.writerow([name, steps, result, simulated, error, agreement])
        if not agreement:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
