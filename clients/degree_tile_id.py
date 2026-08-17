"""
degree_tile_id — Tiny geographic tile-id library, zero dependencies (MicroPython compatible).

Encoding is **alphanumeric**: [NS]dd[A-Z][EW]ddd[A-Z], where dd is a 2-digit
decimal number (latitude degrees) and ddd is a 3-digit decimal number
(longitude degrees). Each tile has a fixed-length 9-character tile_id.

TODO review
Latitude is split into 10 (SUBDEGREE_TILE_COUNT) equal subcells per degree. Longitude is
weighted by cos(int(lat)). A cell is `1 / (10 * cos(int_lat))` degrees wide — so
cells keep a roughly constant physical size. As a side effect, longitude
cells can overshoot the eastern edge of their degree at high latitudes.

Public API:
    lonlat_to_tileid(lon, lat, strict=True) -> str        # (lon, lat) -> tile_id string
    tileid_to_bbox(t)                  -> tuple[float, float, float, float]  # tile_id -> (min_lon, min_lat, max_lon, max_lat)
    tileid_to_center(t)                -> tuple[float, float]                # tile_id -> (lon, lat)
    neighbors(t)                       -> list[str]                          # 8 adjacent tile_ids
    encode_bbox(min_lon, min_lat, max_lon, max_lat) -> list[str]     # split bbox into tile_ids

All angles in degrees. In strict mode (default) lon ∈ [-180, 180] and
lat ∈ [-90, 90]; lenient mode (strict=False) skips the range check.
"""

import math
import re

SUBDEGREE_TILE_COUNT = 10  # A-J
SUBDEGREE_ZERO = ord("A")
TILE_ID_RE = re.compile(r"([NS])(\d{2})([A-Z])([EW])(\d{3})([A-Z])")


# Decode a tile_id into its (ns, int_lat, lat_subdeg, ew, int_lon, lon_subdeg) parts; shared by all decoders.
def parse_tile(tile_id: str) -> tuple[str, int, int, str, int, int]:
    """
    Validate a tile_id and split it into its components.

    Args:
        tile_id: tile_id string in the format [NS]dd[A-Z][EW]ddd[A-Z]

    Returns:
        tuple (ns, int_lat, lat_subdeg, ew, int_lon, lon_subdeg)

    Raises:
        ValueError: if tile_id is malformed
    """
    match = TILE_ID_RE.fullmatch(tile_id)
    if match is None:
        raise ValueError(f"invalid tile_id: {tile_id!r}")

    ns, lat_str, lat_subdeg, ew, lon_str, lon_subdeg = match.groups()

    int_lat = int(lat_str)
    int_lon = int(lon_str)

    if int_lat > 90 or int_lon > 180:
        raise ValueError(f"invalid tile_id: {tile_id!r}")

    return (
        ns,
        int_lat,
        ord(lat_subdeg) - SUBDEGREE_ZERO,
        ew,
        int_lon,
        ord(lon_subdeg) - SUBDEGREE_ZERO,
    )


# Assemble a tile_id string; used by the encoder, neighbors and encode_bbox.
def format_tile(ns: str, int_lat: int, lat_subdeg: int, ew: str, int_lon: int, lon_subdeg: int) -> str:
    """Build a tile_id string from its components."""
    return f"{ns}{int_lat:02d}{chr(SUBDEGREE_ZERO+lat_subdeg)}{ew}{int_lon:03d}{chr(SUBDEGREE_ZERO+lon_subdeg)}"


def lonlat_to_tileid(lon: float, lat: float) -> str:
    """
    Convert (longitude, latitude) in degrees to an alphanumeric tile_id.

    Args:
        lon:  longitude in degrees, -180 ≤ lon ≤ 180 (strict mode)
        lat:  latitude in degrees,  -90 ≤ lat ≤ 90 (strict mode)

    Returns:
        str — tile_id with format [NS]dd[A-Z][EW]ddd[A-Z]

    Raises:
        ValueError: if lon or lat are out of range (strict mode only)
    """
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError(f"lon={lon}, lat={lat} out of range")

    abs_lon = abs(lon)
    abs_lat = abs(lat)

    # Degree part
    int_lon = int(abs_lon)
    int_lat = int(abs_lat)

    # Sub-degree part. Note: abs_lat - int_lat is a fraction of degree [0,1). Idem for longitude
    lat_subdeg = int((abs_lat - int_lat) * SUBDEGREE_TILE_COUNT)
    lon_subdeg = int((abs_lon - int_lon) * math.cos(int_lat / 180 * math.pi) * SUBDEGREE_TILE_COUNT)

    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"

    return format_tile(ns, int_lat, lat_subdeg, ew, int_lon, lon_subdeg)


def tileid_to_bbox(tile_id: str) -> tuple[float, float, float, float]:
    """
    Convert a tile_id to its bounding box.

    Args:
        tile_id: tile_id string (as returned by ``lonlat_to_tileid``)

    Returns:
        tuple ``(min_lon, min_lat, max_lon, max_lat)`` in degrees
    """
    ns, int_lat, lat_subdeg, ew, int_lon, lon_subdeg = parse_tile(tile_id)

    lat_tile_count = SUBDEGREE_TILE_COUNT
    lon_tile_count = math.cos(int_lat / 180 * math.pi) * SUBDEGREE_TILE_COUNT

    # bbox bounds (as in NE hemisphere)
    min_lon = int_lon + lon_subdeg / lon_tile_count
    max_lon = int_lon + min((lon_subdeg + 1) / lon_tile_count, 1)  # Clamp is overlapping next degree
    min_lat = int_lat + lat_subdeg / lat_tile_count
    max_lat = int_lat + (lat_subdeg + 1) / lat_tile_count

    if ns == "S":
        min_lat, max_lat = -max_lat, -min_lat  # mirror band into the S half
    if ew == "W":
        min_lon, max_lon = -max_lon, -min_lon
    return (min_lon, min_lat, max_lon, max_lat)


def tileid_to_center(tile_id: str) -> tuple[float, float]:
    """
    Convert a tile_id to the center-point of its cell.

    Args:
        tile_id: tile_id string

    Returns:
        tuple ``(lon, lat)`` in degrees
    """
    min_lon, min_lat, max_lon, max_lat = tileid_to_bbox(tile_id)
    return ((min_lon + max_lon) / 2, (min_lat + max_lat) / 2)


# candidate latitude bands for encode_bbox; keeps only bands intersecting [min_lat, max_lat].


def encode_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> list[str]:
    """
    Decompose a bounding box into a grid of tile cells.

    Args:
        min_lon, min_lat: bottom-left corner
        max_lon, max_lat: top-right corner

    Returns:
        list[str] — tile_ids covering every cell that intersects
        the bbox (cells may extend slightly beyond the bbox edges).
    """
    if not (-180 <= min_lon <= max_lon <= 180 and -90 <= min_lat <= max_lat <= 90):
        raise ValueError(f"invalid bbox ({min_lon}, {min_lat}, {max_lon}, {max_lat})")
    tiles = []

    # NE QUADRANT
    encode_sub_bbox("E", "N", max(0, min_lon), max(0, min_lat), max(0, max_lon), max(0, max_lat), tiles)
    # NW QUADRANT
    encode_sub_bbox("W", "N", max(0, -max_lon), max(0, min_lat), max(0, -min_lon), max(0, max_lat), tiles)
    # SE QUADRANT
    encode_sub_bbox("E", "S", max(0, min_lon), max(0, -max_lat), max(0, max_lon), max(0, -min_lat), tiles)
    # SW QUADRANT
    encode_sub_bbox("W", "S", max(0, -max_lon), max(0, -max_lat), max(0, -min_lon), max(0, -min_lat), tiles)

    return tiles


def encode_sub_bbox(ew: str, ns: str, minlon: float, minlat: float, maxlon: float, maxlat: float, target_list: list[str]):

    if minlon >= maxlon or minlat >= maxlat:
        return
    
    # Parameters for longitude iteration
    abs_minlon = abs(minlon)
    int_minlon = int(abs_minlon)

    abs_maxlon = abs(maxlon)
    int_maxlon = int(abs_maxlon)

    # Parameters for latitude iteration
    abs_minlat = abs(minlat)
    int_minlat = int(abs_minlat)
    minlat_subdeg = int((abs_minlat - int_minlat) * SUBDEGREE_TILE_COUNT)

    abs_maxlat = abs(maxlat)
    int_maxlat = int(abs_maxlat)
    maxlat_subdeg = int((abs_maxlat - int_maxlat) * SUBDEGREE_TILE_COUNT)

    # Iteration on latitude band (degree and sub-degree)
    for int_lat in range(int_minlat, int_maxlat + 1):

        start = minlat_subdeg if int_lat == int_minlat else 0
        end = maxlat_subdeg + 1 if int_lat == int_maxlat else SUBDEGREE_TILE_COUNT

        for lat_subdeg in range(start, end):

            # Iteration on longitude band (degree and sub-degree)
            minlon_subdeg = int((abs_minlon - int_minlon) * math.cos(int_lat * math.pi / 180) * SUBDEGREE_TILE_COUNT)
            maxlon_subdeg = int((abs_maxlon - int_maxlon) * math.cos(int_lat * math.pi / 180) * SUBDEGREE_TILE_COUNT)

            for int_lon in range(int_minlon, int_maxlon + 1):
                start_lon = minlon_subdeg if int_lon == int_minlon else 0
                end_lon = (
                    maxlon_subdeg 
                    if int_lon == int_maxlon
                    else int(math.cos(int_lat * math.pi / 180) * SUBDEGREE_TILE_COUNT) 
                ) + 1

                for lon_subdeg in range(start_lon, end_lon):
                    target_list.append(format_tile(ns, int_lat, lat_subdeg, ew, int_lon, lon_subdeg))


# __all__ = [
#     "lonlat_to_tileid",
#     "tileid_to_bbox",
#     "tileid_to_center",
#     "encode_bbox",
# ]
