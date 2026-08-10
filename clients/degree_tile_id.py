"""
degree_tile_id — Tiny geographic tile-id library, zero dependencies (MicroPython compatible).

Encoding is **alphanumeric**: [NS]dd[A-Z][EW]ddd[A-Z], where dd is a 2-digit
decimal number (latitude degrees) and ddd is a 3-digit decimal number
(longitude degrees). Each tile has a fixed-length 8-character tile_id.

Public API:
    lonlat_to_tile_id(lon, lat) -> str             # (lon, lat) -> tile_id string
    tile_id_to_bbox(t)          -> tuple[float, float, float, float]  # tile_id -> (min_lon, min_lat, max_lon, max_lat)
    tile_id_to_center(t)        -> tuple[float, float]                # tile_id -> (lon, lat)
    neighbors(t)                -> list[str]                          # 8 adjacent tile_ids
    encode_bbox(min_lon, min_lat, max_lon, max_lat) -> list[str]     # split bbox into tile_ids

All angles in degrees, lon ∈ [-180, 180), lat ∈ [-90, 90].
"""

__all__ = [
    "lonlat_to_tileid",
    "tileid_to_bbox",
    "tileid_to_center",
    "neighbors",
    "encode_bbox",
]


def lonlat_to_tileid(lon: float, lat: float) -> str:
    """
    Convert (longitude, latitude) in degrees to an alphanumeric tile_id.

    Args:
        lon:  longitude in degrees, -180 ≤ lon < 180
        lat:  latitude in degrees,  -90 ≤ lat ≤ 90

    Returns:
        str — tile_id with format [NS]dd[A-Z][EW]ddd[A-Z]

    Raises:
        ValueError: if lon or lat are out of range
    """
    raise NotImplementedError("TODO: implement lonlat encoding")


def tileid_to_bbox(t: str) -> tuple[float, float, float, float]:
    """
    Convert a tile_id to its bounding box.

    Args:
        t: tile_id string (as returned by ``lonlat_to_tile_id``)

    Returns:
        tuple ``(min_lon, min_lat, max_lon, max_lat)`` in degrees
    """
    raise NotImplementedError("TODO: implement bbox decoding")


def tileid_to_center(t: str) -> tuple[float, float]:
    """
    Convert a tile_id to the center-point of its cell.

    Args:
        t: tile_id string

    Returns:
        tuple ``(lon, lat)`` in degrees
    """
    raise NotImplementedError("TODO: implement center decoding")


def neighbors(t: str) -> list[str]:
    """
    Return the 8 adjacent tile_ids (N, NE, E, SE, S, SW, W, NW).

    Args:
        t: tile_id string

    Returns:
        list[str] of 8 neighbor tile_ids
    """
    raise NotImplementedError("TODO: implement neighbor lookup")


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
    raise NotImplementedError("TODO: implement bbox tiling")
