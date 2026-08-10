import sys
import time
from datetime import datetime, timezone

import requests

from download_common import CENTRE_LAT, CENTRE_LON, RADIUS_KM, emit

API_BASE = "https://api.adsb.lol/v2/point"
POLL_INTERVAL_SEC = 1


def fetch_aircraft() -> list[dict]:
    url = f"{API_BASE}/{CENTRE_LAT}/{CENTRE_LON}/{RADIUS_KM}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    now = data["now"]
    timestamp = datetime.fromtimestamp(now / 1000, tz=timezone.utc).isoformat()
    records = []
    for item in data.get("ac", []):
        record = dict(item)
        record["timestamp"] = timestamp
        records.append(record)
    return records


def main() -> None:
    try:
        while True:
            try:
                for record in fetch_aircraft():
                    emit(record)
            except Exception as e:
                print(f"error: {e}", file=sys.stderr, flush=True)
            time.sleep(POLL_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("download stopped", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
