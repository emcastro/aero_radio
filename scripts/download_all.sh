#!/bin/bash
# Run download_ogn.py and download_adsb.py in parallel.
# A single ctrl-c stops both downloaders.
set -eu

DATE=$(date +%Y%m%d-%H%M)
mkdir -p data

OGN_JSONL="data/ogn-${DATE}.jsonl"
OGN_LOG="data/ogn-${DATE}.log"
ADSB_JSONL="data/adsb-${DATE}.jsonl"
ADSB_LOG="data/adsb-${DATE}.log"

pids=()

stop_children() {
    for pid in "${pids[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}

# Ctrl-c = intentional stop: kill both downloaders and exit cleanly
# (exit 0, not 130, so make does not report an "error").
interrupt() {
    stop_children
    echo "[download] interrupted" >&2
    exit 0
}
trap interrupt INT TERM

echo "[download] OGN + ADSB -> ${OGN_JSONL} + ${ADSB_JSONL}" >&2

uv run python -u scripts/download_ogn.py >"$OGN_JSONL" 2>"$OGN_LOG" &
pids+=("$!")

uv run python -u scripts/download_adsb.py >"$ADSB_JSONL" 2>"$ADSB_LOG" &
pids+=("$!")

# Wait for the first to finish, then stop the other: both stop together.
status=0
wait -n "${pids[@]}" || status=$?
stop_children

# Both downloaders are infinite loops: reaching this point without a
# Ctrl-C (no trap) means one exited on its own, which is always a
# failure. OGN can exit 0 after losing the connection (retries
# exhausted), so the exit code is not trustworthy here.
if [ "$status" -eq 0 ]; then
    echo "[download] a downloader exited unexpectedly (exit 0)" >&2
    exit 1
fi

echo "[download] a downloader failed (exit $status)" >&2
exit "$status"
