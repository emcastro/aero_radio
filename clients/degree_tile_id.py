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
SUBDEGREE_LETTERS = "ABCDEFGHIJ"
TILE_ID_RE = re.compile(r"([NS])(\d{2})([A-Z])([EW])(\d{3})([A-Z])")


def parse_tile(tile_id: str) -> tuple[str, int, int, str, int, int]:
    """
    Validate a tile_id and split it into its components.

    Args:
        tile_id: tile_id string in the format [NS]dd[A-Z][EW]ddd[A-Z]

    Returns:
        tuple (ns, int_lat, lat_sub, ew, int_lon, lon_sub)

    Raises:
        ValueError: if tile_id is malformed
    """
    match = TILE_ID_RE.fullmatch(tile_id)
    if match is None:
        raise ValueError(f"invalid tile_id: {tile_id!r}")
    int_lat = int(match.group(2))
    int_lon = int(match.group(5))
    if int_lat > 90 or int_lon > 180:
        raise ValueError(f"invalid tile_id: {tile_id!r}")
    return (
        match.group(1),
        int_lat,
        SUBDEGREE_LETTERS.index(match.group(3)),
        match.group(4),
        int_lon,
        SUBDEGREE_LETTERS.index(match.group(6)),
    )


def format_tile(ns: str, int_lat: int, lat_sub: int, ew: str, int_lon: int, lon_sub: int) -> str:
    """Build a tile_id string from its components."""
    return f"{ns}{int_lat:02d}{SUBDEGREE_LETTERS[lat_sub]}{ew}{int_lon:03d}{SUBDEGREE_LETTERS[lon_sub]}"


def lonlat_to_tileid(lon: float, lat: float, strict: bool = True) -> str:
    """
    Convert (longitude, latitude) in degrees to an alphanumeric tile_id.

    Args:
        lon:  longitude in degrees, -180 ≤ lon ≤ 180 (strict mode)
        lat:  latitude in degrees,  -90 ≤ lat ≤ 90 (strict mode)
        strict: if True, raise ValueError for out-of-range coordinates;
                if False, accept any input without range checking

    Returns:
        str — tile_id with format [NS]dd[A-Z][EW]ddd[A-Z]

    Raises:
        ValueError: if lon or lat are out of range (strict mode only)
    """
    if strict and not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError(f"lon={lon}, lat={lat} out of range")
    abs_lon = abs(lon)
    abs_lat = abs(lat)
    int_lon = int(abs_lon)
    int_lat = int(abs_lat)
    lat_sub = int((abs_lat - int_lat) * SUBDEGREE_TILE_COUNT)
    lon_sub = int((abs_lon - int_lon) * math.cos(int_lat / 180 * math.pi) * SUBDEGREE_TILE_COUNT)
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return format_tile(ns, int_lat, lat_sub, ew, int_lon, lon_sub)


def tileid_to_bbox(tile_id: str) -> tuple[float, float, float, float]:
    """
    Convert a tile_id to its bounding box.

    Args:
        tile_id: tile_id string (as returned by ``lonlat_to_tileid``)

    Returns:
        tuple ``(min_lon, min_lat, max_lon, max_lat)`` in degrees
    """
    ns, int_lat, lat_sub, ew, int_lon, lon_sub = parse_tile(tile_id)
    cos_lat = math.cos(int_lat / 180 * math.pi)
    lat_step = 1 / SUBDEGREE_TILE_COUNT
    lon_step = 1 / (cos_lat * SUBDEGREE_TILE_COUNT)
    min_lon = int_lon + lon_sub * lon_step
    max_lon = int_lon + (lon_sub + 1) * lon_step
    min_lat = int_lat + lat_sub * lat_step
    max_lat = int_lat + (lat_sub + 1) * lat_step
    if ns == "S":
        min_lat, max_lat = -max_lat, -min_lat
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


def move_lat(ns: str, int_lat: int, lat_sub: int, dlat: int) -> tuple[str, int, int] | None:
    """
    Return the cell dlat steps away in latitude, or None if off the map.

    Latitude cells are indexed by a signed integer k where cell k covers
    [k/10, (k+1)/10) degrees; moving north adds 1, moving south subtracts 1.
    """
    k = int_lat * SUBDEGREE_TILE_COUNT + lat_sub
    if ns == "S":
        k = -(int_lat * SUBDEGREE_TILE_COUNT + lat_sub + 1)
    k += dlat
    if k < 0:
        int_lat, lat_sub = divmod(-k - 1, SUBDEGREE_TILE_COUNT)
        ns = "S"
    else:
        int_lat, lat_sub = divmod(k, SUBDEGREE_TILE_COUNT)
        ns = "N"
    if int_lat > 90 or (int_lat == 90 and lat_sub > 0):
        return None
    return (ns, int_lat, lat_sub)


def move_lon(ew: str, int_lon: int, lon_sub: int, dlon: int) -> tuple[str, int, int] | None:
    """
    Return the cell dlon steps away in longitude, or None if off the map.

    Longitude cells are indexed by a single integer n: E(m,j) → m*10 + j and
    W(m,j) → -(m*10 + j + 1), so increasing n moves east and W(0,0) (n=-1)
    sits directly west of E(0,0) (n=0) across the meridian.
    """
    n = int_lon * SUBDEGREE_TILE_COUNT + lon_sub
    if ew == "W":
        n = -n - 1
    n += dlon
    if n < -1810 or n > 1809:
        return None
    if n < 0:
        int_lon, lon_sub = divmod(-n - 1, SUBDEGREE_TILE_COUNT)
        return ("W", int_lon, lon_sub)
    int_lon, lon_sub = divmod(n, SUBDEGREE_TILE_COUNT)
    return ("E", int_lon, lon_sub)


def neighbors(tile_id: str) -> list[str]:
    """
    Return the 8 adjacent tile_ids (N, NE, E, SE, S, SW, W, NW).

    Args:
        tile_id: tile_id string

    Returns:
        list[str] of 8 neighbor tile_ids
    """
    ns, int_lat, lat_sub, ew, int_lon, lon_sub = parse_tile(tile_id)
    result = []
    for dlat, dlon in ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
        lat_move = move_lat(ns, int_lat, lat_sub, dlat)
        lon_move = move_lon(ew, int_lon, lon_sub, dlon)
        if lat_move is not None and lon_move is not None:
            ns2, int_lat2, lat_sub2 = lat_move
            ew2, int_lon2, lon_sub2 = lon_move
            result.append(format_tile(ns2, int_lat2, lat_sub2, ew2, int_lon2, lon_sub2))
    return result


def lat_bands_overlapping(min_lat: float, max_lat: float) -> list[tuple[str, int, int]]:
    """Return the (ns, int_lat, lat_sub) bands that overlap [min_lat, max_lat]."""
    bands = []
    for ns in ("N", "S"):
        for int_lat in range(91):
            if ns == "N":
                row_min = int_lat
                row_max = int_lat + 1
            else:
                row_min = -(int_lat + 1)
                row_max = -int_lat
            if not (row_max > min_lat and row_min < max_lat):
                continue
            for lat_sub in range(SUBDEGREE_TILE_COUNT):
                if ns == "N":
                    band_min = int_lat + lat_sub / SUBDEGREE_TILE_COUNT
                    band_max = int_lat + (lat_sub + 1) / SUBDEGREE_TILE_COUNT
                else:
                    band_min = -(int_lat + (lat_sub + 1) / SUBDEGREE_TILE_COUNT)
                    band_max = -(int_lat + lat_sub / SUBDEGREE_TILE_COUNT)
                if band_max > min_lat and band_min < max_lat:
                    bands.append((ns, int_lat, lat_sub))
    return bands


def lon_tiles_in_band(ns: str, int_lat: int, lat_sub: int, min_lon: float, max_lon: float) -> set[str]:
    """Return the tile_ids of one lat band whose cells overlap [min_lon, max_lon]."""
    cos_lat = math.cos(int_lat / 180 * math.pi)
    lon_step = 1 / (cos_lat * SUBDEGREE_TILE_COUNT)
    tiles = set()
    for ew in ("E", "W"):
        if ew == "E":
            lon_min = max(min_lon, 0.0)
            lon_max = min(max_lon, 180.0)
        else:
            lon_min = max(-max_lon, 0.0)
            lon_max = min(-min_lon, 180.0)
        if lon_max <= lon_min:
            continue
        first_lon = max(0, math.floor(lon_min - 1 / cos_lat))
        for int_lon in range(first_lon, math.floor(lon_max) + 1):
            if int_lon > 180:
                break
            for lon_sub in range(SUBDEGREE_TILE_COUNT):
                cell_min = int_lon + lon_sub * lon_step
                cell_max = int_lon + (lon_sub + 1) * lon_step
                if cell_max > lon_min and cell_min < lon_max:
                    tiles.add(format_tile(ns, int_lat, lat_sub, ew, int_lon, lon_sub))
    return tiles


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
    tiles = set()
    for ns, int_lat, lat_sub in lat_bands_overlapping(min_lat, max_lat):
        tiles.update(lon_tiles_in_band(ns, int_lat, lat_sub, min_lon, max_lon))
    return sorted(tiles)


__all__ = [
    "lonlat_to_tileid",
    "tileid_to_bbox",
    "tileid_to_center",
    "neighbors",
    "encode_bbox",
]
