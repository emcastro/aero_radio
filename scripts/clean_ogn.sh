#!/bin/bash
# Phase 2 — Nettoyage DuckDB d'un JSONL OGN téléchargé.
# Rapide (~3s). Produit un GeoParquet à côté du JSONL (même nom, extension .parquet).
set -eu

usage() {
    echo "usage: $0 [data/ogn-YYYYMMDD-HHMM.jsonl]" >&2
    echo "       sans argument, le .jsonl le plus récent de data/ est utilisé" >&2
    exit 1
}

JSONL=${1:-}
# Sans argument : on prend le téléchargement le plus récent de download_ogn.sh.
test -n "$JSONL" || JSONL=$(find data -maxdepth 1 -name 'ogn-*.jsonl' -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
test -n "$JSONL" || usage

test -f "$JSONL" || { echo "introuvable : $JSONL" >&2; exit 1; }
test -s "$JSONL" || { echo "vide : $JSONL (le téléchargement n'a rien produit)" >&2; exit 1; }

# Le Parquet a le même chemin que le JSONL, seule l'extension change (.jsonl -> .parquet).
PARQUET=${JSONL%.jsonl}.parquet

echo "[clean] duckdb -> $PARQUET (depuis $JSONL)" >&2
uv run python scripts/run_ogn_clean.py "$JSONL"
echo "[clean] terminé ($(du -h "$PARQUET" | cut -f1))" >&2
