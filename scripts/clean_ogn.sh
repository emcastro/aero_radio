#!/bin/bash
# Phase 2 — Cleaning a downloaded OGN JSONL with DuckDB.
# Fast (~3s). Produces a GeoParquet next to the JSONL (same name, .parquet extension).
set -eu

usage() {
    echo "usage: $0 [data/ogn-YYYYMMDD-HHMM.jsonl]" >&2
    echo "       without an argument, the most recent .jsonl in data/ is used" >&2
    exit 1
}

JSONL=${1:-}
# Without an argument: use the most recent download from download_ogn.sh.
test -n "$JSONL" || JSONL=$(find data -maxdepth 1 -name 'ogn-*.jsonl' -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
test -n "$JSONL" || usage

test -f "$JSONL" || { echo "not found: $JSONL" >&2; exit 1; }
test -s "$JSONL" || { echo "empty: $JSONL (the download produced nothing)" >&2; exit 1; }

# The Parquet has the same path as the JSONL, only the extension changes (.jsonl -> .parquet).
PARQUET=${JSONL%.jsonl}.parquet

echo "[clean] duckdb -> $PARQUET (from $JSONL)" >&2
uv run python scripts/run_ogn_clean.py "$JSONL"
echo "[clean] done ($(du -h "$PARQUET" | cut -f1))" >&2
