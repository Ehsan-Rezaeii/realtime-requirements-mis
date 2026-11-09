"""Create a simple plot from REAL raw CSV data (never from hard-coded figures)."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="RQ1 or MIS result CSV")
    parser.add_argument("--output", default="analysis/figures/experiment.png")
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    df = df[df["status"] == "ok"]
    if df.empty:
        raise ValueError("No successful runs in input CSV")
    time_col = "batch_seconds" if "batch_seconds" in df else "time_seconds"
    grouped = df.groupby(["num_rules", "method"], as_index=False)[time_col].median()
    fig, ax = plt.subplots(figsize=(9, 5))
    for method, group in grouped.groupby("method"):
        group = group.sort_values("num_rules")
        ax.plot(group["num_rules"], 1000 * group[time_col], marker="o", label=method)
    ax.set_xlabel("Number of requirements")
    ax.set_ylabel("Median time (ms)")
    ax.set_title("Pilot performance: smaller is better")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    print("Saved:", path)


if __name__ == "__main__":
    main()
