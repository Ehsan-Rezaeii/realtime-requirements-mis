import itertools
import unittest
from z3 import sat, unsat

from team3fm.generator import generate_case
from team3fm.mis import MIS_METHODS, mis_core_deletion, validate_mis
from team3fm.solver import IncrementalChecker, check_nonincremental


class TestMIS(unittest.TestCase):
    def test_controlled_minimality(self):
        for style in ("simple", "mixed"):
            for target_size in (2, 3, 4):
                with self.subTest(style=style, target_size=target_size):
                    data = generate_case(12, target_size, N=5, seed=42, style=style)
                    rules, expected = data["rules"], set(data["injected_ids"])
                    self.assertEqual(check_nonincremental(rules, 5), unsat)
                    for name, func in MIS_METHODS.items():
                        mis = func(rules, 5)
                        self.assertEqual({r["id"] for r in mis}, expected, name)
                        self.assertTrue(validate_mis(mis, 5), name)

    def test_subsets_agree(self):
        data = generate_case(4, 3, N=5, style="simple")
        rules = data["rules"]
        checker = IncrementalChecker(rules, 5)
        for k in range(len(rules) + 1):
            for subset in itertools.combinations(rules, k):
                self.assertEqual(check_nonincremental(list(subset), 5), checker.check(list(subset)))

    def test_sat_has_no_mis(self):
        rules = [{"id": "R1", "type": "absence", "signal": "x"}]
        for func in MIS_METHODS.values():
            self.assertEqual(func(rules, 5), [])
        self.assertFalse(validate_mis([], 5))

    def test_core_versus_mis(self):
        data = generate_case(15, 3, N=5)
        core, mis = mis_core_deletion(data["rules"], 5)
        self.assertTrue(set(r["id"] for r in mis).issubset({r["id"] for r in core}))
        self.assertTrue(validate_mis(mis, 5))


if __name__ == "__main__":
    unittest.main()
