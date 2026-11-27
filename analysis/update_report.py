"""Update measured tables in the Persian report and write a compact evidence snapshot."""

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def markdown(labels, rows):
    lines = ["| " + " | ".join(map(str, labels)) + " |", "| " + " | ".join("---" for _ in labels) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def ms(value):
    return f"{value * 1000:.2f}" if pd.notna(value) else "—"


def read(study, kind, filename):
    return pd.read_csv(study / kind / (filename + ".csv"))


def write_report(study, pilot, validation, report):
    r1 = read(study, "summary", "rq1_timing")
    r2 = read(study, "summary", "rq2_mis_timing_and_size")
    r3 = read(study, "summary", "rq3_correctness")
    r4 = read(study, "summary", "rq4_status")
    r5 = read(study, "summary", "rq5_scalability")
    speedups = read(study, "summary", "paired_speedups")
    inference = read(study, "summary", "paired_inference")
    run_status = read(study, "summary", "run_status")
    metadata = json.loads((study / "environment.json").read_text(encoding="utf-8"))
    config = metadata["config"]
    cases = read(study, ".", "case_manifest")
    independent = pd.read_csv(validation)
    gate = read(pilot, "summary", "pilot_gate")
    sections = {}
    total = int(run_status.runs.sum())
    successful = int(run_status.ok.sum())
    timeouts = int(run_status.timeout.sum())
    valid_mis = int(r3.valid_minimal_runs.sum())
    independent_pass = int(independent.status.eq("pass").sum())
    independent_fail = int(independent.status.eq("fail").sum())
    independent_skip = int(independent.status.eq("not_checked").sum())
    scale_r1 = r1[r1.scenario.eq("scale-mixed")].set_index(["num_rules", "method"])
    r1_speeds = speedups[(speedups.experiment.eq("rq1")) & speedups.case_id.str.startswith("scale-mixed-")]
    r1_min, r1_max = r1_speeds.speedup.min(), r1_speeds.speedup.max()
    gate_rq1 = gate[gate.experiment.eq("rq1")]
    gate_mis = gate[gate.experiment.eq("mis")]

    sections["SUMMARY"] = (
        f"در مطالعهٔ نهایی {len(cases):,} مورد متمایز و {total:,} اجرا ثبت شد. "
        f"{successful:,} اجرا موفق و {timeouts:,} اجرا دچار timeout شدند. "
        f"در خانوادهٔ مقیاس، میانهٔ سرعت نسبی افزایشی در جفت‌های موفق از {r1_min:.2f} تا {r1_max:.2f} برابر بود. "
        f"{valid_mis:,} خروجی MIS کنترل کمینگی را گذراندند. "
        f"نسخهٔ آزموده‌شده Python `{metadata['python']}` و Z3 `{metadata['z3']}` روی Linux بود."
    )
    sections["INFERENCE"] = markdown(
        ["پرسش و روش", "مورد", "نسبت میانه", "۹۵٪ bootstrap", "A12", "Wilcoxon", "Holm"],
        [(f"{row.experiment} / {row.method}", row.cases, f"{row.median_case_speedup:.2f}",
          f"{row.bootstrap_low:.2f}–{row.bootstrap_high:.2f}", f"{row.a12_faster:.2f}",
          f"{row.wilcoxon_p:.3f}", f"{row.holm_p:.3f}") for row in inference.itertuples()]
    )
    sections["INFERENCE"] += (
        f"\n\nشرایط اجرا: seed حل‌کننده {config['solver_seed']}، {config['repeats']} تکرار، "
        f"مهلت هر فراخوانی {config['timeout_ms']} ms، مهلت کل {config['operation_seconds']:g} s و "
        f"سقف فضای آدرس {config['memory_mib']} MiB. پردازندهٔ گزارش‌شده `{metadata['cpu']}` است. "
        "تنظیمات کامل و مشخصات محیط در JSON شواهد ثبت‌اند."
    )

    rows = []
    for n in (12, 60, 500, 1000, 5000):
        fresh = scale_r1.loc[(n, "nonincremental")]
        inc = scale_r1.loc[(n, "incremental")]
        pair = r1_speeds[r1_speeds.num_rules.eq(n)]
        ratio = f"{pair.iloc[0].speedup:.2f}× ({pair.iloc[0].pairs})" if len(pair) else "—"
        rows.append((n, ms(fresh.wall_time_seconds_median), ms(inc.wall_time_seconds_median),
                     ms(fresh.build_seconds_median), ms(inc.build_seconds_median),
                     ratio, f"{fresh.ok}/{fresh.runs}", f"{inc.ok}/{inc.runs}"))
    fresh_60 = scale_r1.loc[(60, "nonincremental")]
    inc_60 = scale_r1.loc[(60, "incremental")]
    sections["RQ1"] = markdown(
        ["قواعد", "کل تازه", "کل افزایشی", "ساخت تازه", "ساخت افزایشی",
         "نسبت (جفت)", "موفق تازه", "موفق افزایشی"],
        rows,
    ) + (
        "\n\nزمان‌های جدول برحسب میلی‌ثانیه‌اند. در ۶۰ قید، میانهٔ زمان خود Z3 برای روش تازه "
        f"{ms(fresh_60.solving_seconds_median)} و برای افزایشی {ms(inc_60.solving_seconds_median)} "
        "میلی‌ثانیه بود. سرعت‌های جدول از زوج‌های موفق به دست آمده‌اند."
    )

    mid = r2[r2.case_id.eq("scale-mixed-60")]
    sections["RQ23"] = markdown(
        ["روش", "میانه ms", "فراخوانی Z3", "اندازه MIS", "اندازه Core"],
        [(row.method, ms(row.wall_time_seconds_median), f"{row.solver_calls_median:g}",
          f"{row.mis_size_median:g}", f"{row.core_size_median:g}" if pd.notna(row.core_size_median) else "—")
         for row in mid.itertuples()]
    ) + "\n\n" + markdown(
        ["روش", "MIS معتبر / تلاش UNSAT", "MIS معتبر / بررسی قطعی", "تزریق‌های بازیابی‌شده / موردها"],
        [(row.method, f"{row.valid_minimal_runs}/{row.scheduled_unsat_runs}",
          f"{row.valid_minimal_runs}/{row.decided_candidate_validations}",
          f"{row.distinct_injected_cases_recovered}/{row.distinct_injected_cases}")
         for row in r3.itertuples()]
    )

    grid = r4[r4.method.eq("nonincremental")].pivot(index="scenario", columns="N", values="result")
    sections["RQ4"] = markdown(["سناریو", *grid.columns], [(idx, *row) for idx, row in grid.iterrows()])
    sections["RQ4"] += "\n\nمقادیر جدول از اجراهای موفق با Solver تازه آمده‌اند. جدول خام افزایشی و تازه را برای هر تکرار ثبت کرده است."

    groups = ("nonincremental", "incremental", "core", "quickxplain")
    by_size = r5.set_index(["num_rules", "method"])
    rows = []
    for n in sorted(r5.num_rules.unique()):
        per_method = []
        for name in groups:
            row = by_size.loc[(n, name)]
            per_method.append(f"{ms(row.wall_time_seconds_median)} ({row.ok}/{row.runs})")
        rows.append((n, *per_method))
    sections["RQ5"] = markdown(["قواعد", *groups], rows)
    sections["RQ5"] += "\n\nهر خانه میانهٔ میلی‌ثانیهٔ اجرای موفق و (موفق/تلاش) را نشان می‌دهد. برای شکست‌ها، ستون وضعیت CSV حفظ شده است."

    sections["VALIDATION"] = (
        f"اعتبارسنج مستقل {independent_pass:,} کنترل موفق و {independent_fail} اختلاف ثبت کرد. "
        f"شمار موارد بررسی‌ناپذیر تحت سقف شمارش {independent_skip} بود. "
        f"در پایلوت، افزایشی در {int(gate_rq1.at_least_as_fast.sum())} از {len(gate_rq1)} مورد و "
        f"Core در {int(gate_mis.at_least_as_fast.sum())} از {len(gate_mis)} مورد به معیار سرعتِ قوی‌ترین "
        "baseline داخلی رسید. کنترل‌های مستقل پایلوت در CSV جدا ثبت شدند."
    )

    original = report.read_text(encoding="utf-8")
    for name, body in sections.items():
        start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
        pattern = re.escape(start) + ".*?" + re.escape(end)
        original, count = re.subn(pattern, lambda _: f"{start}\n\n{body}\n\n{end}", original, flags=re.S)
        if count != 1:
            raise ValueError(f"expected one report section named {name}, got {count}")
    report.write_text(original, encoding="utf-8")

    snapshot = {
        "cases": len(cases), "runs": total,
        "statuses": {name: int(run_status[name].sum()) for name in
                     ("ok", "timeout", "unknown", "crash", "error", "invalid", "not_run")},
        "valid_mis_runs": valid_mis,
        "independent_pass": independent_pass, "independent_fail": independent_fail,
        "independent_not_checked": independent_skip,
        "rq1_scale_speedup_range": [r1_min, r1_max],
        "code_commit": metadata["git_commit"],
        "pilot_incremental_wins": [int(gate_rq1.at_least_as_fast.sum()), len(gate_rq1)],
        "pilot_core_wins": [int(gate_mis.at_least_as_fast.sum()), len(gate_mis)],
    }
    (study / "summary" / "report_snapshot.json").write_text(
        json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(snapshot, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("results/final"))
    parser.add_argument("--pilot", type=Path, default=Path("results/pilot"))
    parser.add_argument("--validation", type=Path, default=Path("results/validation/independent_validation.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/FINAL_REPORT_FA.md"))
    args = parser.parse_args()
    write_report(args.study, args.pilot, args.validation, args.report)
