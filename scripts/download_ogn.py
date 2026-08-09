import json
import sys

from ogn.client import AprsClient
from ogn.parser import AprsParseError, parse

# OpenGliderNetwork APRS stream to subscribe to.
# r/LAT/LON/RADIUS  -> 590 km radius box centred on France (IGN: kept on purpose).
OGN_APRS_USER = "N0CALL"
OGN_FILTER = "r/46.606111/1.875278/590"


def process_beacon(raw_message: str) -> None:
    try:
        beacon = parse(raw_message)
    except AprsParseError as e:
        print("Error, {}".format(e.message), file=sys.stderr, flush=True)
        return
    if beacon.get("aprs_type") == "position":
        print(json.dumps(beacon, sort_keys=True, default=str), flush=True)


def main() -> None:
    client = AprsClient(aprs_user=OGN_APRS_USER, aprs_filter=OGN_FILTER)
    client.connect()
    try:
        client.run(callback=process_beacon, autoreconnect=True)
    except KeyboardInterrupt:
        print("download stopped", file=sys.stderr, flush=True)
    finally:
        client.disconnect()
        sys.stdout.flush()


if __name__ == "__main__":
    main()
