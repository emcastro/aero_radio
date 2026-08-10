"""
degree_geohash — Tiny geohash library, zero dependencies (MicroPython compatible).

Encoding is **alphanumeric**: [NS]ddd[A-Z][EW]ddd[A-Z], where ddd is a 3-digit decimal number.

Public API:
    lonlat_to_hash(lon, lat, precision) -> str   # (lon, lat) -> hash-number string
    hash_to_bbox(h)          -> tuple          # hash-number string -> (min_lon, min_lat, max_lon, max_lat)
    hash_to_center(h)        -> tuple          # hash-number string -> (lon, lat)
    neighbors(h)             -> list           # 8 adjacent cell hashes
    encode_bbox(bbox, precision) -> list       # split a bbox into hash cells

All angles in degrees, lon ∈ [-180, 180), lat ∈ [-90, 90].
"""

__all__ = [
    "lonlat_to_hash",
    "hash_to_bbox",
    "hash_to_center",
    "neighbors",
    "encode_bbox",
]


def lonlat_to_hash(lon, lat, precision=6):
    """
    Convert (longitude, latitude) in degrees to a numeric geohash string.

    Args:
        lon:  longitude in degrees, -180 ≤ lon < 180
        lat:  latitude in degrees,  -90 ≤ lat ≤ 90
        precision: number of characters in the returned hash (more = finer)

    Returns:
        str — hash-number string composed of decimal digits

    Raises:
        ValueError: if lon or lat are out of range
    """
    raise NotImplementedError("TODO: implement lonlat encoding")


def hash_to_bbox(h):
    """
    Convert a numeric geohash string to its bounding box.

    Args:
        h: hash-number string (as returned by ``lonlat_to_hash``)

    Returns:
        tuple ``(min_lon, min_lat, max_lon, max_lat)`` in degrees
    """
    raise NotImplementedError("TODO: implement bbox decoding")


def hash_to_center(h):
    """
    Convert a numeric geohash string to the center-point of its cell.

    Args:
        h: hash-number string

    Returns:
        tuple ``(lon, lat)`` in degrees
    """
    raise NotImplementedError("TODO: implement center decoding")


def neighbors(h):
    """
    Return the 8 adjacent cell hashes (N, NE, E, SE, S, SW, W, NW).

    Args:
        h: hash-number string

    Returns:
        list[str] of 8 neighbor hashes
    """
    raise NotImplementedError("TODO: implement neighbor lookup")


def encode_bbox(min_lon, min_lat, max_lon, max_lat, precision=6):
    """
    Decompose a bounding box into a grid of hash cells at the given precision.

    Args:
        min_lon, min_lat: bottom-left corner
        max_lon, max_lat: top-right corner
        precision: hash string length

    Returns:
        list[str] — hash-number strings covering every cell that intersects
        the bbox (cells may extend slightly beyond the bbox edges).
    """
    raise NotImplementedError("TODO: implement bbox tiling")
