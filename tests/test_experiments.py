import csv
import tempfile
import unittest
from pathlib import Path

from team3fm.experiments import run_experiments


class TestExperiments(unittest.TestCase):
    def test_tiny_pilot(self):
        with tempfile.TemporaryDirectory() as folder:
            config = {
                "N": 5, "sizes": [6], "mis_size": 3, "style": "simple",
                "seed": 42, "repeats": 1, "timeout_ms": 5000,
                "rq4_N_values": [2, 3], "out_dir": folder,
            }
            paths = run_experiments(config, mode="all")
            self.assertEqual(len(paths), 3)
            self.assertTrue((Path(folder) / "environment.json").is_file())
            for path in paths:
                with open(path, newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                self.assertTrue(rows)
                self.assertTrue(all(r["status"] == "ok" for r in rows), path)


if __name__ == "__main__":
    unittest.main()
