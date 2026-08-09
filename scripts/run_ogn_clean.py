import sys
from pathlib import Path

import duckdb

# Time thresholds for the OGN cleaning pipeline (see scripts/make_ogn_geoparquet.sql).
MAX_TS_DRIFT_SEC = 10   # seconds: reject beacons whose `timestamp` drifts from `reference_timestamp`
MIN_TRACK_POINTS = 600  # positions (~10 min @ 1 point/s): minimum track length kept

# The cleaning SQL lives next to this runner.
SQL_PATH = Path(__file__).with_name("make_ogn_geoparquet.sql")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"usage: {Path(sys.argv[0]).name} <download.jsonl>", file=sys.stderr)
        raise SystemExit(1)
    jsonl_path = Path(sys.argv[1])
    sql = (
        SQL_PATH.read_text()
        .replace("__JSONL__", str(jsonl_path))
        .replace("__PARQUET__", str(jsonl_path.with_suffix(".parquet")))
        .replace("__MAX_TS_DRIFT_SEC__", str(MAX_TS_DRIFT_SEC))
        .replace("__MIN_TRACK_POINTS__", str(MIN_TRACK_POINTS))
    )
    duckdb.connect().execute(sql)


if __name__ == "__main__":
    main()
