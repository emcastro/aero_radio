#!/bin/bash
# Run download_adsb.py (ADSB poll, 1 req/s). Ctrl-c = clean stop.
set -eu

DATE=$(date +%Y%m%d-%H%M)
mkdir -p data

ADSB_JSONL="data/adsb-${DATE}.jsonl"
ADSB_LOG="data/adsb-${DATE}.log"

echo "[download] ADSB -> ${ADSB_JSONL}" >&2

uv run python -u scripts/download_adsb.py >"$ADSB_JSONL" 2>"$ADSB_LOG"

echo "[download] done (adsb: $(wc -l < "$ADSB_JSONL") records, $(wc -c < "$ADSB_LOG") error bytes)" >&2
