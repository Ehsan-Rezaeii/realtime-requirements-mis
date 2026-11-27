#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 - "$work" <<'PY'
import re
import sys
from pathlib import Path

work = Path(sys.argv[1])
report = Path("reports/FINAL_REPORT_FA.md").read_text(encoding="utf-8")
report = report.replace('<div class="page-break"></div>', r"\newpage")
english_title = "Real-Time Requirements Consistency Checking and Minimal Inconsistent Subset (MIS) Extraction"
report = report.replace(
    english_title,
    "\n".join((
        "```{=latex}",
        r"{\centering\leavevmode\hbox{\beginL\footnotesize " + english_title + r"\endL}\par}",
        "```",
    )),
)



def place_figure(match):
    caption, path = match.groups()
    # XeTeX needs an explicit LTR box for an image inside a Persian figure.
    return "\n".join((
        "```{=latex}",
        r"\begin{figure}[htbp]",
        r"\centering",
        r"\leavevmode\hbox{\beginL\includegraphics[width=.94\linewidth]{" + path + r"}\endL}",
        r"\caption{" + caption + "}",
        r"\end{figure}",
        "```",
    ))


report = re.sub(r"^!\[([^\]]+)\]\(\.\./(results/[^)]+)\)$", place_figure, report, flags=re.M)
(work / "report.md").write_text(report, encoding="utf-8")
(work / "graphics.tex").write_text("\\usepackage{graphicx}\n", encoding="utf-8")
PY
pandoc "$work/report.md" --include-in-header="$work/graphics.tex" --pdf-engine=xelatex \
  -V mainfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" \
  -V papersize=a4 -V geometry:margin=18mm -V fontsize=11pt \
  -o reports/FINAL_REPORT_FA.pdf
