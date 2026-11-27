"""Plan, run and resume the CPU-only RQ1–RQ5 study."""

import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter

import z3

from .dataio import load_dataset, save_dataset
from .experiments import _bound_case
from .generator import generate_case
from .mis import MIS_METHODS

ROOT = Path(__file__).resolve().parents[2]
CONSISTENCY_METHODS = ("nonincremental", "incremental")
FILES = {
    "rq1": "rq1_consistency.csv", "mis": "rq2_rq3_rq5_mis.csv",
    "rq4": "rq4_bound_effect.csv",
}
FIELDS = (
    "run_id experiment_id case_id scenario method dataset_type num_rules N seed solver_seed "
    "repetition timeout_ms operation_seconds memory_mib expected result status "
    "wall_time_seconds build_seconds solving_seconds validation_seconds worker_seconds "
    "solver_calls num_checks mis_size mis_ids core_size minimal injection_recovered "
    "injected_ids outcomes error timestamp"
).split()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, data):
    temp = path.with_suffix(f".{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _system_field(path, key):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(key):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def environment(config):
    packages = {}
    for name in ("z3-solver", "pandas", "matplotlib", "scipy"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {
        "config": config, "python": sys.version.split()[0], "z3": z3.get_version_string(),
        "packages": packages, "system": platform.platform(),
        "cpu": platform.processor() or _system_field("/proc/cpuinfo", "model name"),
        "logical_cores": os.cpu_count(),
        "available_cores": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count(),
        "host_ram": _system_field("/proc/meminfo", "MemTotal"),
        "runtime_limits": {
            name: Path(f"/sys/fs/cgroup/{name}").read_text().strip()
            for name in ("memory.max", "cpu.max")
            if Path(f"/sys/fs/cgroup/{name}").is_file()
        },
        "environment": "Google Colab" if "COLAB_RELEASE_TAG" in os.environ else "local CPU runtime",
        "memory_enforcement": "RLIMIT_AS per worker" if sys.platform.startswith("linux") else "unavailable",
        "source_sha256": {p.name: digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
    }


def bound_case(scenario, N):
    if scenario == "boundary_delay":
        rules = [{"id": "R1", "type": "bounded_delay", "trigger": "a",
                  "target": "b", "min_delay": 2, "max_delay": 2}]
        observations = [{"signal": "a", "time": 2, "value": True}] if N >= 2 else []
        expected = "unsat" if 2 <= N < 4 else "sat"
    else:
        rules, observations, expected = _bound_case(scenario, N)
    return {"case_id": f"{scenario}-N{N}", "scenario": scenario, "N": N,
            "rules": rules, "observations": observations, "expected_status": expected,
            "dataset_type": "temporal_scenario"}


def consistency_queries(case):
    rules = case["rules"]
    injected = case.get("injected_ids", [])
    if injected and case["dataset_type"] == "synthetic":
        first = [r for r in rules if r["id"] != injected[0]]
        last = [r for r in rules if r["id"] != injected[-1]]
        background = next((r for r in rules if r["id"] not in injected), rules[0])
        return [rules, first, [r for r in rules if r != background], last], [
            "unsat", "sat", "unsat" if background["id"] not in injected else "sat", "sat"]
    return [rules], [case["expected_status"]]


def _cases(config):
    for spec in config["synthetic"]:
        for size in spec["sizes"]:
            case = generate_case(size, spec["mis_size"], config["N"], spec["seed"], spec["style"],
                                 satisfiable=spec.get("sat", False), variant=spec["variant"])
            case.update(case_id=f"{spec['family']}-{size}", scenario=spec["family"],
                        expected_status="unsat" if case["injected_ids"] else "sat",
                        dataset_type="synthetic", variant=spec["variant"])
            yield case, ("rq1", "mis")
    for entry in config.get("files", []):
        case = load_dataset(ROOT / entry["path"])
        case.update(dataset_type=entry["dataset_type"], expected_status=entry["expected"],
                    scenario=entry["dataset_type"], source_path=entry["path"])
        yield case, ("rq1", "mis")
    for scenario in config["scenarios"]:
        for N in config["bounds"]:
            yield bound_case(scenario, N), ("rq4",)


def _plan(config, out):
    jobs, cases = [], []
    case_ids = set()
    for case, experiments in _cases(config):
        case_id = case["case_id"]
        if not case_id or not all(c.isascii() and (c.isalnum() or c in "_-") for c in case_id):
            raise ValueError(f"invalid case ID for output file: {case_id}")
        if case_id in case_ids:
            raise ValueError(f"duplicate case ID: {case_id}")
        case_ids.add(case_id)
        case_path = out / "cases" / f"{case_id}.json"
        save_dataset(case, case_path)
        cases.append({
            "case_id": case_id, "path": f"cases/{case_path.name}", "sha256": digest(case_path),
            "source": case.get("source_path", "generated from config"),
            "dataset_type": case["dataset_type"], "num_rules": len(case["rules"]), "N": case["N"],
            "seed": case.get("seed", ""), "expected_status": case["expected_status"],
            "injected_ids": ";".join(case.get("injected_ids", [])),
            "expected_mis_size": len(case.get("injected_ids", [])) if "injected_ids" in case else "",
            "pattern_distribution": json.dumps(Counter(r["type"] for r in case["rules"]), sort_keys=True),
        })
        for exp in experiments:
            methods = list(MIS_METHODS) if exp == "mis" else list(CONSISTENCY_METHODS)
            for rep in range(1, config["repeats"] + 1):
                shift = (rep - 1) % len(methods)
                for method in methods[shift:] + methods[:shift]:
                    expected = case["expected_status"]
                    if exp == "rq1":
                        _, expected_queries = consistency_queries(case)
                        expected = ";".join(expected_queries)
                    jobs.append({
                        "run_id": f"{exp}-{case_id}-{rep:02d}-{method}", "experiment_id": exp,
                        "case_id": case_id, "scenario": case["scenario"], "method": method,
                        "dataset_type": case["dataset_type"], "num_rules": len(case["rules"]),
                        "N": case["N"], "seed": case.get("seed", ""), "repetition": rep,
                        "solver_seed": config["solver_seed"], "expected": expected,
                        "injected_ids": ";".join(case.get("injected_ids", [])),
                        **{key: config[key] for key in ("timeout_ms", "operation_seconds", "memory_mib")},
                    })
    save_csv(out / "case_manifest.csv", cases, list(cases[0]))
    save_csv(out / "experiment_manifest.csv", jobs, FIELDS[:16])
    return jobs


def _run_worker(path, job):
    worker = Path(__file__).with_name("study_worker.py")
    command = [
        sys.executable, str(worker), str(path), job["experiment_id"], job["method"],
        str(job["timeout_ms"]), str(job["memory_mib"]), str(job["solver_seed"]),
    ]
    start = perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=job["operation_seconds"], check=False)
        if completed.returncode:
            status = "crash" if completed.returncode < 0 else "error"
            result = {"status": status, "error": f"exit {completed.returncode}: {completed.stderr.strip()}"}
        else:
            result = json.loads(completed.stdout)
    except subprocess.TimeoutExpired:
        result = {"status": "timeout", "error": "worker exceeded whole-operation wall timeout"}
    except (OSError, ValueError) as exc:
        result = {"status": "error", "error": str(exc)}
    return {**job, **result, "worker_seconds": perf_counter() - start, "timestamp": timestamp()}


def run_study(config, out):
    for key in ("repeats", "timeout_ms", "memory_mib"):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if type(config["solver_seed"]) is not int or not 0 <= config["solver_seed"] < 2**32:
        raise ValueError("solver_seed must be an unsigned 32-bit integer")
    if type(config["operation_seconds"]) not in (int, float) or config["operation_seconds"] <= 0:
        raise ValueError("operation_seconds must be positive")
    out = Path(out)
    journal = out / "records"
    journal.mkdir(parents=True, exist_ok=True)
    raw = out / "raw"
    raw.mkdir(exist_ok=True)
    env_path = out / "environment.json"
    metadata = environment(config)
    metadata["input_sha256"] = {entry["path"]: digest(ROOT / entry["path"])
                                for entry in config.get("files", [])}
    if env_path.exists():
        previous = json.loads(env_path.read_text(encoding="utf-8"))
        if any(previous.get(key) != value for key, value in metadata.items()):
            raise ValueError("resume needs the original configuration, host, inputs and study code")
    else:
        if any(journal.glob("*.json")):
            raise ValueError("existing study records have no environment metadata")
        save_json(env_path, {**metadata, "git_commit": _git("rev-parse", "HEAD"),
                             "git_status": _git("status", "--porcelain", "--untracked-files=no"),
                             "started_utc": timestamp()})
    jobs = _plan(config, out)

    try:
        for index, job in enumerate(jobs, start=1):
            record = journal / f"{job['run_id']}.json"
            if not record.exists():
                case_path = out / "cases" / f"{job['case_id']}.json"
                save_json(record, _run_worker(case_path, job))
            if index % 50 == 0 or index == len(jobs):
                print(f"Study progress: {index}/{len(jobs)}", flush=True)
    finally:
        results = {exp: [] for exp in FILES}
        for job in jobs:
            record = journal / f"{job['run_id']}.json"
            row = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {**job, "status": "not_run"}
            results[job["experiment_id"]].append(row)
        for exp, name in FILES.items():
            save_csv(raw / name, results[exp], FIELDS)
        logs = out / "logs"
        logs.mkdir(exist_ok=True)
        save_csv(logs / "failures.csv",
                 [row for rows in results.values() for row in rows if row["status"] != "ok"], FIELDS)
    return raw
