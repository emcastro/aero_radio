#!/bin/bash
set -eu

DATE=$(date +%Y%m%d-%H%M)
mkdir -p data

# Phase 1 — OGN real-time stream (long). Stdout -> JSONL, stderr -> log.
echo "[download] OGN stream -> data/ogn-${DATE}.jsonl" >&2
uv run python -u scripts/download_ogn.py >"data/ogn-${DATE}.jsonl" 2>"data/ogn-${DATE}.log"
echo "[download] done ($(wc -l < "data/ogn-${DATE}.jsonl") beacons, $(wc -c < "data/ogn-${DATE}.log") error bytes)" >&2
