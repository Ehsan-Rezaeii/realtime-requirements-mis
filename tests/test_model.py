import unittest
from z3 import sat, unsat
from team3fm.solver import check_nonincremental, IncrementalChecker
from team3fm.model import validate_rules, validate_observations


class TestTemporalPatterns(unittest.TestCase):
    def assert_result(self, rules, expected, N=5, observations=None):
        self.assertEqual(check_nonincremental(rules, N, observations=observations), expected)
        self.assertEqual(IncrementalChecker(rules, N, observations=observations).check(), expected)

    def test_invariant(self):
        self.assert_result([{"id": "R1", "type": "invariant", "signal": "a"}], sat)

    def test_absence(self):
        self.assert_result([{"id": "R1", "type": "absence", "signal": "a"}], sat)

    def test_invariant_absence_conflict(self):
        self.assert_result([{"id": "R1", "type": "invariant", "signal": "a"},
                            {"id": "R2", "type": "absence", "signal": "a"}], unsat)

    def test_recurrence_absence_conflict(self):
        self.assert_result([{"id": "R1", "type": "recurrence", "signal": "a", "window": 3},
                            {"id": "R2", "type": "absence", "signal": "a"}], unsat)

    def test_response_vacuous(self):
        self.assert_result([{"id": "R1", "type": "response", "trigger": "a", "target": "b", "deadline": 2},
                            {"id": "R2", "type": "absence", "signal": "a"},
                            {"id": "R3", "type": "absence", "signal": "b"}], sat)

    def test_response_conflict(self):
        self.assert_result([{"id": "R1", "type": "invariant", "signal": "a"},
                            {"id": "R2", "type": "response", "trigger": "a", "target": "b", "deadline": 2},
                            {"id": "R3", "type": "absence", "signal": "b"}], unsat)

    def test_bounded_delay_vacuous(self):
        self.assert_result([{"id": "R1", "type": "bounded_delay", "trigger": "a", "target": "b",
                             "min_delay": 1, "max_delay": 2},
                            {"id": "R2", "type": "absence", "signal": "a"}], sat)

    def test_bounded_delay_horizon(self):
        # A signal required at t=N cannot have a response at t=N+1 in this model.
        self.assert_result([{"id": "R1", "type": "invariant", "signal": "a"},
                            {"id": "R2", "type": "bounded_delay", "trigger": "a", "target": "b",
                             "min_delay": 1, "max_delay": 2}], unsat)

    def test_bounded_delay_zero(self):
        self.assert_result([{"id": "R1", "type": "invariant", "signal": "a"},
                            {"id": "R2", "type": "invariant", "signal": "b"},
                            {"id": "R3", "type": "bounded_delay", "trigger": "a", "target": "b",
                             "min_delay": 0, "max_delay": 0}], sat)

    def test_late_conflict_in_horizon(self):
        rules = [{"id": "R1", "type": "response", "trigger": "request", "target": "grant", "deadline": 1},
                 {"id": "R2", "type": "absence", "signal": "grant"}]
        self.assert_result(rules, sat, N=2)
        self.assert_result(rules, unsat, N=3, observations=[{"signal": "request", "time": 3, "value": True}])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            validate_rules([{"id": "R1", "type": "recurrence", "signal": "x", "window": 7}], 5)
        with self.assertRaises(ValueError):
            validate_rules([{"id": "R1", "type": "absence", "signal": "a"},
                            {"id": "R1", "type": "absence", "signal": "b"}], 5)
        with self.assertRaises(ValueError):
            validate_observations([{"signal": "x", "time": 1, "value": True},
                                   {"signal": "x", "time": 1, "value": False}], 5)
        with self.assertRaises(ValueError):
            validate_rules([{"id": "R1", "type": "response", "trigger": "a", "target": "b",
                             "deadline": -1}], 5)
        with self.assertRaises(ValueError):
            validate_rules([], True)


if __name__ == "__main__":
    unittest.main()
