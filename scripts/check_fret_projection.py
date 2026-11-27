"""Audit two public FRET finite-trace exports against the local projection."""

import csv
from itertools import product
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "benchmarks/public"


def compare():
    exported = json.loads((PUBLIC / "source/FRET_LiquidMixer.json").read_text(encoding="utf-8"))
    source = {entry["reqid"]: entry["semantics"]["ftExpanded"] for entry in exported["requirements"]}
    translated = json.loads((PUBLIC / "fret_liquid_mixer_projection.json").read_text(encoding="utf-8"))
    writer = csv.writer(sys.stdout)
    writer.writerow(["rule_id", "N", "traces", "source_sat_traces", "local_sat_traces",
                     "source_only", "local_only", "source_only_trigger", "source_only_target"])
    for rule in translated["rules"]:
        trigger, target = rule["trigger"], rule["target"]
        # Confirm that the upstream export uses the recognized initial/edge template.
        expected = (f"((LAST V (((! {trigger}) & ((! LAST) & (X {trigger}))) -> (X {target})))"
                    f" & ({trigger} -> {target}))")
        if source[rule["id"]] != expected:
            raise ValueError(f"unrecognized exported formula for {rule['id']}")
        points = 3
        both, source_only, local_only = 0, 0, 0
        witness = None
        for bits in product((False, True), repeat=2 * points):
            a, b = bits[:points], bits[points:]
            native = all(not enter or b[t] for t, enter in enumerate(
                a[t] and (t == 0 or not a[t - 1]) for t in range(points)
            ))
            local = all(not a[t] or b[t] for t in range(points))
            both += native and local
            source_only += native and not local
            local_only += local and not native
            if witness is None and native and not local:
                witness = ["".join("1" if bit else "0" for bit in signal) for signal in (a, b)]
        writer.writerow([rule["id"], points - 1, 2 ** (2 * points), both + source_only,
                         both + local_only, source_only, local_only, *witness])
        if not source_only or local_only:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(compare())
