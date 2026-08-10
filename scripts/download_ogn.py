import sys

from ogn.client import AprsClient
from ogn.parser import AprsParseError, parse

from download_common import CENTRE_LAT, CENTRE_LON, RADIUS_KM, emit

# OpenGliderNetwork APRS stream to subscribe to.
# r/LAT/LON/RADIUS  -> 590 km radius box centred on France (centre shared with the ADSB downloader).
OGN_APRS_USER = "N0CALL"
OGN_FILTER = f"r/{CENTRE_LAT}/{CENTRE_LON}/{RADIUS_KM}"


def process_beacon(raw_message: str) -> None:
    try:
        beacon = parse(raw_message)
    except AprsParseError as e:
        print(f"Error, {e.message}", file=sys.stderr, flush=True)
        return
    if beacon.get("aprs_type") == "position":
        emit(beacon)


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
