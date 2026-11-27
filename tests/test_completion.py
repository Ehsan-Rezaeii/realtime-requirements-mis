import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from z3 import sat, unknown

from team3fm.generator import generate_case
from team3fm.mis import MIS_METHODS, validate_mis
from team3fm.solver import InconclusiveError, IncrementalChecker, _check
from team3fm.study import run_study


class TestCompletion(unittest.TestCase):
    def test_activation_names_and_empty_selection(self):
        rules = [{"id": "R1", "type": "absence", "signal": "__rule_enabled"}]
        checker = IncrementalChecker(rules, 0)
        self.assertEqual(checker.check(), sat)
        self.assertEqual(checker.check([]), sat)
        self.assertEqual(IncrementalChecker([], 0).check(), sat)
        for selection in (["bad"], ["R1", "R1"], [{}], [[]]):
            with self.assertRaises(ValueError):
                checker.check(selection)

    def test_distinct_conflicts_with_fixed_observations(self):
        rules = [
            {"id": "R1", "type": "response", "trigger": "a", "target": "b", "deadline": 0},
            {"id": "R2", "type": "absence", "signal": "b"},
            {"id": "R3", "type": "invariant", "signal": "c"},
            {"id": "R4", "type": "absence", "signal": "c"},
        ]
        observations = [{"signal": "a", "time": 0, "value": True}]
        for name, extract in MIS_METHODS.items():
            with self.subTest(method=name):
                result = extract(rules, 0, observations=observations)
                self.assertIn({r["id"] for r in result}, ({"R1", "R2"}, {"R3", "R4"}))
                self.assertTrue(validate_mis(result, 0, observations=observations, rules=rules))
                self.assertFalse(validate_mis(result, 0, observations=observations, rules=[]))

    def test_satisfiable_generator_and_variation(self):
        options = dict(satisfiable=True, variant="varied")
        a = generate_case(24, seed=7, **options)
        self.assertEqual(a, generate_case(24, seed=7, **options))
        b = generate_case(24, seed=99, **options)
        self.assertNotEqual(sorted(a["rules"], key=lambda r: r["id"]),
                            sorted(b["rules"], key=lambda r: r["id"]))
        self.assertEqual(IncrementalChecker(a["rules"], a["N"]).check(), sat)
        self.assertFalse(a["injected_ids"])

    def test_typed_unknown_and_timeout(self):
        for reason, status in (("timeout", "timeout"), ("incomplete", "unknown")):
            fake_solver = Mock()
            fake_solver.check.return_value = unknown
            fake_solver.reason_unknown.return_value = reason
            self.assertEqual(_check(fake_solver, [], False), unknown)
            with self.assertRaises(InconclusiveError) as captured:
                _check(fake_solver, [], True)
            self.assertEqual(captured.exception.status, status)

    def test_cli_input_error(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "invalid.json"
            bad.write_text("{", encoding="utf-8")
            command = [sys.executable, "run.py", "check", "--input", str(bad)]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("JSONDecodeError", result.stderr)

    def test_worker_deadline_and_resume(self):
        config = {
            "N": 2, "repeats": 1, "timeout_ms": 100, "operation_seconds": 0.001,
            "memory_mib": 512, "solver_seed": 3, "synthetic": [],
            "bounds": [2], "scenarios": ["always_sat"],
        }
        with tempfile.TemporaryDirectory() as folder:
            raw = run_study(config, folder)
            with (raw / "rq4_bound_effect.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["status"] == "timeout" for row in rows))
            before = (raw / "rq4_bound_effect.csv").read_bytes()
            run_study(config, folder)
            self.assertEqual(before, (raw / "rq4_bound_effect.csv").read_bytes())
            with self.assertRaises(ValueError):
                run_study({**config, "repeats": 2}, folder)
