"""Generate tables, figures, and paired exploratory statistics from raw study CSVs."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

RAW_FILES = {
    "rq1": "rq1_consistency.csv",
    "mis": "rq2_rq3_rq5_mis.csv",
    "rq4": "rq4_bound_effect.csv",
}
METHODS = ("nonincremental", "incremental", "core", "quickxplain")
COLORS = dict(zip(METHODS, ("#a33e22", "#1974a6", "#08715b", "#704793")))
STATUSES = ("ok", "invalid", "unknown", "timeout", "crash", "error", "not_run")


def table(frame, path):
    frame.to_csv(path, index=False, float_format="%.8g")


def summarize(frame, by, measures):
    rows = []
    for keys, g in frame.groupby(by, sort=True, dropna=False):
        row = dict(zip(by, keys if isinstance(keys, tuple) else (keys,)))
        row["runs"] = len(g)
        row.update({status: int(g.status.eq(status).sum()) for status in STATUSES})
        row["success_rate"] = row["ok"] / row["runs"]
        row["timeout_rate"] = row["timeout"] / row["runs"]
        successful = g[g.status.eq("ok")]
        for measure in measures:
            vals = successful[measure].dropna()
            if len(vals):
                row.update({
                    f"{measure}_median": vals.median(), f"{measure}_mean": vals.mean(),
                    f"{measure}_sd": vals.std(ddof=1), f"{measure}_min": vals.min(),
                    f"{measure}_q1": vals.quantile(.25), f"{measure}_q3": vals.quantile(.75),
                    f"{measure}_iqr": vals.quantile(.75) - vals.quantile(.25),
                    f"{measure}_max": vals.max(),
                })
        rows.append(row)
    return pd.DataFrame(rows)


def paired_speedups(frame, experiment):
    ok = frame[frame.status.eq("ok")]
    wide = ok.pivot(index=["case_id", "dataset_type", "num_rules", "repetition"],
                    columns="method", values="wall_time_seconds")
    rows = []
    for method in METHODS[1:]:
        if method not in wide or METHODS[0] not in wide:
            continue
        for keys, group in wide.groupby(level=[0, 1, 2]):
            times = group[[METHODS[0], method]].dropna()
            ratios = times[METHODS[0]] / times[method]
            if len(ratios):
                rows.append(dict(experiment=experiment, case_id=keys[0], dataset_type=keys[1],
                                 num_rules=keys[2], method=method, pairs=len(ratios),
                                 speedup=ratios.median(), q1=ratios.quantile(.25),
                                 q3=ratios.quantile(.75), faster=int((ratios > 1).sum())))
    return pd.DataFrame(rows)


def paired_inference(raw):
    rng = np.random.default_rng(730)
    items = []
    for experiment in ("rq1", "mis"):
        frame = raw[experiment]
        selection = frame[
            frame.status.eq("ok") & frame.dataset_type.eq("synthetic") &
            frame.num_rules.eq(30) & ~frame.scenario.str.contains("-sat")
        ]
        medians = selection.groupby(["case_id", "method"]).wall_time_seconds.median().unstack()
        for method in METHODS[1:]:
            if method not in medians or METHODS[0] not in medians:
                continue
            cases = medians[[METHODS[0], method]].dropna()
            if len(cases) < 5:
                continue
            base, other = cases[METHODS[0]].to_numpy(), cases[method].to_numpy()
            paired = base / other
            boot = rng.choice(paired, (10000, len(paired)), replace=True)
            diffs = base - other
            across_pairs = base[:, None] - other[None, :]
            items.append({
                "experiment": experiment, "method": method, "cases": len(cases),
                "case_ids": ";".join(cases.index),
                "median_case_speedup": np.median(paired),
                "bootstrap_low": np.quantile(np.median(boot, axis=1), .025),
                "bootstrap_high": np.quantile(np.median(boot, axis=1), .975),
                "a12_faster": np.mean((across_pairs > 0) + 0.5 * (across_pairs == 0)),
                "wilcoxon_p": float(wilcoxon(diffs, alternative="two-sided", method="exact").pvalue)
                if np.any(diffs) else 1.0,
            })
    running = 0.0
    for i, index in enumerate(sorted(range(len(items)), key=lambda j: items[j]["wilcoxon_p"])):
        running = max(running, items[index]["wilcoxon_p"] * (len(items) - i))
        items[index]["holm_p"] = min(1.0, running)
    return pd.DataFrame(items, columns=[
        "experiment", "method", "cases", "case_ids", "median_case_speedup", "bootstrap_low",
        "bootstrap_high", "a12_faster", "wilcoxon_p", "holm_p",
    ])


def correctness(frame):
    rows = []
    for method, group in frame.groupby("method"):
        eligible = group[group.expected.eq("unsat")]
        candidates = eligible[eligible.mis_ids.notna()]
        validated = candidates[candidates.minimal.notna()]
        inject = eligible[eligible.dataset_type.eq("synthetic") & eligible.injected_ids.notna()]
        valid_count = int(eligible.minimal.eq(True).sum())
        exact = int((inject.injection_recovered.eq(True) & inject.minimal.eq(True) &
                     inject.status.eq("ok")).sum())
        case_total = int(inject.case_id.nunique())
        case_exact = int(inject[inject.injection_recovered.eq(True) & inject.minimal.eq(True) &
                                inject.status.eq("ok")].case_id.nunique())
        rows.append({
            "method": method, "scheduled_unsat_runs": len(eligible),
            "returned_candidates": len(candidates), "decided_candidate_validations": len(validated),
            "valid_minimal_runs": valid_count,
            "validity_among_decided_candidates": valid_count / len(validated) if len(validated) else None,
            "valid_mis_yield_all_unsat_runs": valid_count / len(eligible) if len(eligible) else None,
            "scheduled_injected_runs": len(inject),
            "exact_injection_recoveries": exact,
            "exact_recovery_per_injected_run": exact / len(inject) if len(inject) else None,
            "distinct_injected_cases": case_total, "distinct_injected_cases_recovered": case_exact,
            "injection_recall_by_case": case_exact / case_total if case_total else None,
            "invalid": int(group.status.eq("invalid").sum()), "unknown": int(group.status.eq("unknown").sum()),
            "timeout": int(group.status.eq("timeout").sum()), "crash": int(group.status.eq("crash").sum()),
            "error": int(group.status.eq("error").sum()),
        })
    return pd.DataFrame(rows)


def save_figure(fig, directory, name):
    for extension in ("png", "svg"):
        fig.savefig(directory / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def times_plot(frame, x, directory, filename, title, description, groups="method", logarithmic=True):
    fig, ax = plt.subplots(figsize=(8.4, 4.7), layout="constrained")
    palette = list(COLORS.values())
    for i, (label, group) in enumerate(frame.groupby(groups)):
        group = group.sort_values(x)
        med = group.wall_time_seconds_median * 1000
        color = COLORS.get(label, palette[i % len(palette)])
        ax.plot(group[x], med, "o-", label=label, color=color)
        ax.fill_between(group[x], group.wall_time_seconds_q1 * 1000,
                        group.wall_time_seconds_q3 * 1000, color=color, alpha=.14)
    if logarithmic:
        ax.set_yscale("log")
    ax.set_xscale("log")
    xs = sorted(frame[x].unique())
    ax.set_xticks(xs, labels=[f"{val:,}" for val in xs])
    ax.set(xlabel="Requirements" if x == "num_rules" else "Horizon N",
           ylabel="Median wall time (ms)")
    ax.legend(frameon=False, ncols=2)
    ax.grid(axis="y", alpha=.20)
    fig.suptitle(title, weight="bold")
    ax.set_title(description, fontsize=9, loc="left")
    save_figure(fig, directory, filename)


def status_plot(frame, directory, repeats):
    scale = frame[frame.scenario.eq("scale-mixed")]
    if scale.empty:
        return
    fig, ax = plt.subplots(figsize=(8.4, 4.6), layout="constrained")
    x = sorted(scale.num_rules.unique())
    for i, method in enumerate(METHODS):
        values = scale[scale.method.eq(method)].set_index("num_rules").reindex(x)
        offset = (i - 1.5) * .18
        layout = np.arange(len(x)) + offset
        ax.bar(layout, values.ok, .16, color=COLORS[method], label=method)
        ax.bar(layout, values.timeout, .16, bottom=values.ok, color=COLORS[method], alpha=.24,
               hatch="//", edgecolor=COLORS[method])
    ax.set(xticks=np.arange(len(x)), xticklabels=[f"{value:,}" for value in x],
           ylabel="Runs", xlabel="Requirements", ylim=(0, repeats + .5))
    ax.legend(ncols=2, frameon=False)
    ax.grid(axis="y", alpha=.16)
    fig.suptitle("RQ5  |  Successful MIS runs and timeouts", weight="bold")
    ax.set_title("Mixed synthetic family. Solid = success. Hatched = timeout.", fontsize=9, loc="left")
    save_figure(fig, directory, "rq5_status")


def bounds_plot(frame, directory):
    grid = frame[frame.method.eq("nonincremental")].pivot(index="scenario", columns="N", values="result")
    if grid.empty:
        return
    fig, ax = plt.subplots(figsize=(8.4, 3.0), layout="constrained")
    ax.axis("off")
    cells = grid.fillna("—").values.tolist()
    colors = [["#d9eee7" if x == "sat" else "#f7dfd7" if x == "unsat" else "#ededed" for x in row] for row in cells]
    data = ax.table(cellText=cells, colLabels=[f"N={n}" for n in grid.columns],
                    rowLabels=[n.replace("_", " ") for n in grid.index],
                    cellColours=colors, cellLoc="center", rowLoc="right", loc="center")
    data.scale(.88, 1.6)
    fig.suptitle("RQ4  |  Consistency across the modeled horizon", weight="bold")
    save_figure(fig, directory, "rq4_status")


def pilot_gate(raw, out):
    comparisons = []
    for name, challenger in (("rq1", "incremental"), ("mis", "core")):
        data = raw[name]
        combined = data[data.status.eq("ok") & data.dataset_type.eq("synthetic")]
        wall = combined.groupby(["case_id", "method"]).wall_time_seconds.median().unstack()
        for case, row in wall.iterrows():
            eligible = ["nonincremental"] if name == "rq1" else [
                method for method in METHODS if method != challenger and method in row
            ]
            if eligible and challenger in row:
                fastest = row[eligible].idxmin()
                comparisons.append(dict(experiment=name, case_id=case, challenger=challenger,
                                        best_baseline=fastest, speedup=row[fastest] / row[challenger],
                                        at_least_as_fast=bool(row[challenger] <= row[fastest])))
    table(pd.DataFrame(comparisons), out / "pilot_gate.csv")


def analyze(study, output):
    summary, figures = output / "summary", output / "figures"
    summary.mkdir(parents=True, exist_ok=True)
    figures.mkdir(exist_ok=True)
    raw = {name: pd.read_csv(study / "raw" / filename) for name, filename in RAW_FILES.items()}
    raw["rq1"]["num_checks"] = raw["rq1"].expected.str.count(";") + 1
    config = json.loads((study / "environment.json").read_text(encoding="utf-8"))["config"]
    repeats = config["repeats"]
    times = ["wall_time_seconds", "build_seconds", "solving_seconds", "solver_calls"]
    by_case = ["case_id", "dataset_type", "scenario", "num_rules", "N", "method"]
    r1 = summarize(raw["rq1"], by_case + ["num_checks"], times)
    mis = summarize(raw["mis"], by_case + ["expected"], times + ["mis_size", "core_size"])
    bounds = summarize(raw["rq4"], by_case, times)
    statuses = (raw["rq4"][raw["rq4"].status.eq("ok")].groupby(["scenario", "N", "method"]).result
                .agg(lambda values: "/".join(sorted(values.unique()))).reset_index())
    table(r1, summary / "rq1_timing.csv")
    table(mis, summary / "rq2_mis_timing_and_size.csv")
    table(correctness(raw["mis"]), summary / "rq3_correctness.csv")
    table(bounds, summary / "rq4_timing.csv")
    table(statuses, summary / "rq4_status.csv")
    all_rows = pd.concat(raw.values(), ignore_index=True)
    table(summarize(all_rows, ["experiment_id", "method"], []), summary / "run_status.csv")
    table(mis[mis.scenario.eq("scale-mixed")], summary / "rq5_scalability.csv")
    speedups = pd.concat([paired_speedups(raw[name], name) for name in ("rq1", "mis")], ignore_index=True)
    table(speedups, summary / "paired_speedups.csv")
    table(paired_inference(raw), summary / "paired_inference.csv")
    if repeats < 10:
        pilot_gate(raw, summary)

    scale = "scale-mixed" if "scale-mixed" in set(r1.scenario) else "pilot-mixed"
    scale_r1 = r1[r1.scenario.eq(scale)]
    scale_mis = mis[mis.scenario.eq(scale)]
    note = f"Mixed synthetic family, {repeats} attempts per point. Bands show IQR of successful runs."
    if not scale_r1.empty:
        times_plot(scale_r1, "num_rules", figures, "rq1_consistency", "RQ1  |  Identical consistency batches", note)
    if not scale_mis.empty:
        times_plot(scale_mis[scale_mis.num_rules.le(60)], "num_rules", figures, "rq2_mis_time",
                   "RQ2  |  Time to extract one MIS", note)
        times_plot(scale_mis, "num_rules", figures, "rq5_scalability",
                   "RQ5  |  MIS extraction as requirements grow", note + " Gaps have no successful run.")
    if not bounds.empty:
        times_plot(bounds[bounds.method.eq("nonincremental")], "N", figures, "rq4_bound_timing",
                   "RQ4  |  Solve time by horizon", f"Fresh solver, {repeats} attempts per point. Bands show IQR.",
                   groups="scenario")
        bounds_plot(statuses, figures)
    status_plot(mis, figures, repeats)

    if not speedups.empty and not scale_r1.empty:
        ratios = speedups[(speedups.experiment == "rq1") & speedups.case_id.str.startswith(scale + "-")]
        ratios = ratios.sort_values("num_rules")
        fig, ax = plt.subplots(figsize=(8.4, 4.3), layout="constrained")
        ax.set_xscale("log")
        ax.plot(ratios.num_rules, ratios.speedup, "o-", color=COLORS["incremental"])
        ax.fill_between(ratios.num_rules, ratios.q1, ratios.q3, alpha=.14, color=COLORS["incremental"])
        ax.axhline(1, color="#666666", ls="--", lw=1)
        ax.set_xticks(ratios.num_rules, labels=[f"{val:,}" for val in ratios.num_rules])
        ax.set(xlabel="Requirements", ylabel="Fresh / incremental wall time")
        ax.grid(axis="y", alpha=.2)
        fig.suptitle("RQ1  |  Paired speedup of incremental checking", weight="bold")
        save_figure(fig, figures, "rq1_speedup")
    counts = all_rows.status.value_counts()
    print(f"Analyzed {len(all_rows)} runs across {all_rows.case_id.nunique()} cases.")
    print(counts.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("results/final"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    analyze(args.study, args.output or args.study)
