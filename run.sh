#!/usr/bin/env bash
# Rebuilds the data from the generator, prints four reports, and compares the output against expected.txt.
# Only python is required, without additional packages.
set -euo pipefail
cd "$(dirname "$0")"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

python generate_data.py "$tmp"
if ! diff -r "$tmp" data > /dev/null; then
  echo "MISMATCH: data/ does not match the output generate_data.py"
  exit 1
fi

out=$(python eval.py)
echo "$out"

if [ "$out" = "$(cat expected.txt)" ]; then
  echo "OK: same outcome as expected.txt"
else
  echo "MISMATCH with expected.txt:"
  diff <(echo "$out") expected.txt || true
  exit 1
fi
