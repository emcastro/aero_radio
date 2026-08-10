import json

# Geographic area shared by all downloaders: 590 km radius box centred on
# France (IGN: kept on purpose). Single source of truth for the zone.
CENTRE_LAT = 46.606111
CENTRE_LON = 1.875278
RADIUS_KM = 590


def emit(record: dict) -> None:
    """Emit one JSONL line on stdout. Raw record, untouched."""
    print(json.dumps(record, sort_keys=True, default=str), flush=True)
