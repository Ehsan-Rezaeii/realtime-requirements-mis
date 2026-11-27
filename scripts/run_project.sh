#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${PYTHON:-python3}"
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-demo}" in
  setup) PYTHON="$python_bin" bash setup.sh ;;
  demo) "$python_bin" run.py demo ;;
  test) "$python_bin" -m unittest discover -s tests -v ;;
  pilot|full)
    if [[ "$1" == "pilot" ]]; then config=pilot; else config=final; fi
    output="${2:-results/reproduced-$config}"
    "$python_bin" run.py study --config "experiments/$config.json" --output "$output"
    "$python_bin" scripts/validate_study.py --study "$output" --output "$output/independent_validation.csv"
    "$python_bin" analysis/analyze_results.py --study "$output"
    ;;
  analysis) "$python_bin" analysis/analyze_results.py --study "${2:-results/final}" ;;
  *) echo "Usage: $0 {setup|demo|test|pilot|full|analysis} [output]" >&2; exit 2 ;;
esac
