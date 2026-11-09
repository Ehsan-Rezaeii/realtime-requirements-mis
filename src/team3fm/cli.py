"""Command-line interface for consistency checking and MIS extraction."""

import argparse
import json
from pathlib import Path

from z3 import unsat

from .dataio import load_dataset, save_dataset
from .experiments import run_experiments
from .generator import generate_case
from .mis import MIS_METHODS, mis_core_deletion, validate_mis
from .solver import IncrementalChecker, check_nonincremental


def build_parser():
    parser = argparse.ArgumentParser(description="Team 3 — temporal requirements and MIS using Z3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run the tiny 3-rule MIS demonstration")

    generate = commands.add_parser("generate", help="Create a reproducible synthetic JSON dataset")
    generate.add_argument("--size", type=int, default=30)
    generate.add_argument("--mis-size", type=int, choices=[2, 3, 4], default=3)
    generate.add_argument("--N", type=int, default=5)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--style", choices=["simple", "mixed"], default="mixed")
    generate.add_argument("--output", default="benchmarks/generated/sample.json")

    check = commands.add_parser("check", help="Check consistency and extract one validated MIS")
    check.add_argument("--input", required=True)
    check.add_argument("--method", choices=["nonincremental", "incremental", "core"], default="core")
    check.add_argument("--timeout-ms", type=int, default=5000)

    benchmark = commands.add_parser("benchmark", help="Run reproducible pilot comparisons")
    benchmark.add_argument("--mode", choices=["mis", "consistency", "bounds", "all"], default="all")
    benchmark.add_argument("--config", default="experiments/config.json")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        case = generate_case(4, mis_size=3, N=5, seed=42, style="simple")
        rules, N = case["rules"], case["N"]
        outcome = check_nonincremental(rules, N)
        print("Consistency:", outcome)
        if outcome == unsat:
            core, mis = mis_core_deletion(rules, N)
            print("Initial core:", [r["id"] for r in core])
            print("MIS:", [r["id"] for r in mis])
            print("MIS valid:", validate_mis(mis, N))
        return

    if args.command == "generate":
        case = generate_case(args.size, args.mis_size, args.N, args.seed, args.style)
        path = save_dataset(case, args.output)
        print(f"Saved: {path} ({len(case['rules'])} rules; injected={case['injected_ids']})")
        return

    if args.command == "check":
        data = load_dataset(args.input)
        rules, N = data["rules"], data["N"]
        observations = data.get("observations", [])
        if args.method == "incremental":
            result = IncrementalChecker(rules, N, args.timeout_ms, observations).check()
        else:
            result = check_nonincremental(rules, N, args.timeout_ms, observations)
        print("Case:", data["case_id"])
        print("Rules:", len(rules), "N:", N, "Consistency:", result)
        if result == unsat:
            mis = MIS_METHODS[args.method](rules, N, args.timeout_ms, observations)
            print("MIS:", [r["id"] for r in mis])
            print("MIS size:", len(mis))
            print("MIS valid:", validate_mis(mis, N, args.timeout_ms, observations))
        return

    if args.command == "benchmark":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        files = run_experiments(config, args.mode)
        for path in files:
            print("Saved:", path)
        return


if __name__ == "__main__":
    main()
