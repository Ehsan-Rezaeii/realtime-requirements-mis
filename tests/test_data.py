import tempfile
import unittest
from pathlib import Path

from z3 import sat
from team3fm.dataio import load_dataset, save_dataset, validate_dataset
from team3fm.generator import generate_case
from team3fm.solver import check_nonincremental


class TestData(unittest.TestCase):
    def test_roundtrip(self):
        data = generate_case(30, 3, 5, 42, style="mixed")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.json"
            save_dataset(data, path)
            loaded = load_dataset(path)
            self.assertEqual(loaded, data)
            self.assertEqual(len(loaded["rules"]), 30)

    def test_consistent_background(self):
        data = generate_case(30, 3, 5, style="mixed")
        background = [r for r in data["rules"] if r["id"] not in data["injected_ids"]]
        self.assertEqual(check_nonincremental(background, 5), sat)

    def test_invalid_dataset(self):
        data = generate_case(12, 3, 5)
        data["injected_ids"] = ["invalid"]
        with self.assertRaises(ValueError):
            validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
