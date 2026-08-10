#!/bin/bash
# Run download_ogn.py (real-time OGN stream). Ctrl-c = clean stop.
set -eu

DATE=$(date +%Y%m%d-%H%M)
mkdir -p data

OGN_JSONL="data/ogn-${DATE}.jsonl"
OGN_LOG="data/ogn-${DATE}.log"

echo "[download] OGN -> ${OGN_JSONL}" >&2

uv run python -u scripts/download_ogn.py >"$OGN_JSONL" 2>"$OGN_LOG"

echo "[download] done (ogn: $(wc -l < "$OGN_JSONL") beacons, $(wc -c < "$OGN_LOG") error bytes)" >&2
