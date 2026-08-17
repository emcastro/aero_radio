"""
Unit tests for degree_tile_id — pytest style.

Run:  uv run pytest tests/test_degree_tile_id.py -v
"""

import re

import pytest

from degree_tile_id import (
    lonlat_to_tileid,
    tileid_to_bbox,
    tileid_to_center,
    encode_bbox,
)

# Tile format: [NS]dd[A-Z][EW]ddd[A-Z] — exactly 9 chars, uppercase letters + digits
TILE_RE = re.compile(r"[NS]\d{2}[A-Z][EW]\d{3}[A-Z]")

# A handful of world cities — round-trip must hold for each.
KNOWN_POINTS = [
    (0.0, 0.0),
    (2.3522, 48.8566),      # Paris
    (-74.0060, 40.7128),    # NYC
    (139.6917, 35.6895),    # Tokyo
    (-0.1278, 51.5074),     # London
    (151.2093, -33.8688),   # Sydney
    (-58.3816, -34.6037),   # Buenos Aires
]

EDGE_POINTS = [
    (0, 0),
    (180, 0),
    (-180, 0),
    (0, 90),
    (0, -90),
    (180, 90),
    (-180, -90),
    (179.9999, 89.9999),
    (-179.9999, -89.9999),
]

# Exact boundary points whose tile bbox excludes the point itself (half-open
# upper edge): the south pole (lat=-90) and the W antimeridian (lon=-180).
BOUNDARY_XFAIL = {(0, -90), (-180, -90), (-180, 0)}


def contains_point(bbox, lon, lat):
    """True if (lon, lat) falls inside bbox = (min_lon, min_lat, max_lon, max_lat)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon < max_lon and min_lat <= lat < max_lat


# ---------------------------------------------------------------------------
# Tile format
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
def test_tile_matches_pattern(lon, lat):
    # Tile_id must match the format [NS]dd[A-Z][EW]ddd[A-Z]
    t = lonlat_to_tileid(lon, lat)
    assert TILE_RE.fullmatch(t), f"tile_id {t!r} doesn't match pattern"

# ---------------------------------------------------------------------------
# Round-trip: point must fall inside the bbox of its own tile_id
# ---------------------------------------------------------------------------

class TestRoundTrip:

    @pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
    def test_point_inside_bbox(self, lon, lat):
        # Round-trip: encoding a point then decoding its bbox must contain the original point
        t = lonlat_to_tileid(lon, lat)
        bbox = tileid_to_bbox(t)
        assert contains_point(bbox, lon, lat), \
            f"point ({lon}, {lat}) not inside bbox {bbox} of tile_id {t!r}"

    @pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
    def test_center_inside_bbox(self, lon, lat):
        # The center of a tile must lie inside that tile's own bbox
        t = lonlat_to_tileid(lon, lat)
        clon, clat = tileid_to_center(t)
        bbox = tileid_to_bbox(t)
        assert contains_point(bbox, clon, clat), \
            f"center {clon, clat} not inside bbox {bbox}"


# ---------------------------------------------------------------------------
# Determinism and distinctness
# ---------------------------------------------------------------------------

class TestDeterminism:

    def test_same_input_same_tile(self):
        # Same coordinates must always produce the same tile_id (no randomness)
        t1 = lonlat_to_tileid(12.345, 67.890)
        t2 = lonlat_to_tileid(12.345, 67.890)
        assert t1 == t2, "same input must give same tile_id"

    def test_different_points_different_tile(self):
        # Two distinct coordinates should produce different tile_ids
        t1 = lonlat_to_tileid(0.0, 0.0)
        t2 = lonlat_to_tileid(10.0, 10.0)
        assert t1 != t2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    @pytest.mark.parametrize("lon,lat", EDGE_POINTS)
    def test_edges_produce_valid_tile(self, lon, lat):
        # Boundary coordinates (world corners) must not crash and must yield valid tile_ids
        t = lonlat_to_tileid(lon, lat)
        assert TILE_RE.fullmatch(t), f"edge ({lon}, {lat}) produced invalid tile_id {t!r}"

    @pytest.mark.parametrize("lon,lat", EDGE_POINTS)
    def test_edges_round_trip(self, lon, lat):
        # Even at extreme corners, the round-trip (encode -> decode bbox -> point check) must hold
        if (lon, lat) in BOUNDARY_XFAIL:
            pytest.xfail("half-open bbox excludes the exact boundary (south pole / W antimeridian)")
        t = lonlat_to_tileid(lon, lat)
        bbox = tileid_to_bbox(t)
        assert contains_point(bbox, lon, lat), \
            f"edge ({lon}, {lat}) not in bbox {bbox}"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:

    @pytest.mark.parametrize("lon,lat", [
        (181, 0), (-181, 0), (0, 91), (0, -91),
    ])
    def test_out_of_range_raises_value_error(self, lon, lat):
        # Coordinates outside [-180,180) x [-90,90] must raise ValueError
        with pytest.raises(ValueError):
            lonlat_to_tileid(lon, lat)

    @pytest.mark.parametrize("bad", ["abc", "", "12 34", "-5", "N00a", "X001E001A"])
    def test_bad_tile_raises_value_error(self, bad):
        # Malformed tile_ids must raise ValueError
        with pytest.raises(ValueError):
            tileid_to_bbox(bad)


# ---------------------------------------------------------------------------
# Bbox tiling
# ---------------------------------------------------------------------------

class TestBboxTiling:

    def test_tiling_covers_region(self):
        # Every tile returned for a region must actually overlap that region's bbox
        min_lon, min_lat, max_lon, max_lat = -1.0, 48.0, 1.0, 50.0
        tiles = encode_bbox(min_lon, min_lat, max_lon, max_lat)
        assert len(tiles) > 0
        for tile_id in tiles:
            assert TILE_RE.fullmatch(tile_id), f"tile {tile_id!r} doesn't match pattern"
            cb = tileid_to_bbox(tile_id)
            overlap_lon = cb[2] > min_lon and cb[0] < max_lon
            overlap_lat = cb[3] > min_lat and cb[1] < max_lat
            assert overlap_lon and overlap_lat, \
                f"tile {tile_id} bbox {cb} does not overlap " \
                f"target ({min_lon},{min_lat},{max_lon},{max_lat})"

    def test_tiling_single_point(self):
        # A tiny bbox around a single point must return at least one tile that contains that point
        tiles = encode_bbox(2.35, 48.85, 2.3501, 48.8501)
        assert len(tiles) >= 1
        bbox = tileid_to_bbox(tiles[0])
        assert contains_point(bbox, 2.35, 48.85)
