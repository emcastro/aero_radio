"""
Unit tests for degree_geohash — pytest style.

Run:  uv run pytest tests/test_degree_geohash.py -v
"""

import re

import pytest

from degree_geohash import (
    lonlat_to_hash,
    hash_to_bbox,
    hash_to_center,
    neighbors,
    encode_bbox,
)

DIGITS_RE = re.compile(r"[NS]\d{2}[A-Z][EW]\d{3}[A-Z]$")  # pattern for alphanumeric geohash strings

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


def contains_point(bbox, lon, lat):
    """True if (lon, lat) falls inside bbox = (min_lon, min_lat, max_lon, max_lat)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon < max_lon and min_lat <= lat < max_lat


# ---------------------------------------------------------------------------
# Hash format
# ---------------------------------------------------------------------------

class TestHashFormat:

    def test_hash_is_string(self):
        # Verify that lonlat_to_hash returns a Python str, not bytes or int
        h = lonlat_to_hash(2.35, 48.85, precision=6)
        assert isinstance(h, str)

    @pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
    def test_hash_only_digits(self, lon, lat):
        # Hash must match the pattern (TO BE DEFINED)
        h = lonlat_to_hash(lon, lat, precision=8)
        assert DIGITS_RE.fullmatch(h), f"hash {h!r} contains non-digit characters"

    @pytest.mark.parametrize("p", range(1, 12))
    def test_hash_length_matches_precision(self, p):
        # Number of characters in the hash string must equal the precision parameter
        h = lonlat_to_hash(10.0, 20.0, precision=p)
        assert len(h) == p, f"precision {p} -> len {len(h)}, expected {p}"


# ---------------------------------------------------------------------------
# Round-trip: point must fall inside the bbox of its own hash
# ---------------------------------------------------------------------------

class TestRoundTrip:

    @pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
    def test_point_inside_bbox(self, lon, lat):
        # Round-trip: encoding a point then decoding its bbox must contain the original point
        h = lonlat_to_hash(lon, lat, precision=9)
        bbox = hash_to_bbox(h)
        assert contains_point(bbox, lon, lat), \
            f"point ({lon}, {lat}) not inside bbox {bbox} of hash {h!r}"

    @pytest.mark.parametrize("lon,lat", KNOWN_POINTS)
    @pytest.mark.parametrize("precision", [4, 6, 8])
    def test_center_inside_bbox(self, lon, lat, precision):
        # The center of a cell must lie inside that cell's own bbox
        h = lonlat_to_hash(lon, lat, precision=precision)
        clon, clat = hash_to_center(h)
        bbox = hash_to_bbox(h)
        assert contains_point(bbox, clon, clat), \
            f"center {clon, clat} not inside bbox {bbox}"


# ---------------------------------------------------------------------------
# Precision: more precision => smaller bbox
# ---------------------------------------------------------------------------

class TestPrecision:

    def test_more_precision_smaller_bbox(self):
        # Each additional precision level must shrink the cell area
        lon, lat = 2.35, 48.85
        areas = []
        for p in [2, 4, 6, 8, 10]:
            h = lonlat_to_hash(lon, lat, precision=p)
            min_lon, min_lat, max_lon, max_lat = hash_to_bbox(h)
            areas.append((max_lon - min_lon) * (max_lat - min_lat))

        for i in range(1, len(areas)):
            assert areas[i] < areas[i - 1], \
                f"precision {i*2} area {areas[i]} >= {areas[i-1]}"

    def test_different_points_different_hash(self):
        # Two distinct coordinates should (very likely) produce different hash strings
        h1 = lonlat_to_hash(0.0, 0.0, precision=6)
        h2 = lonlat_to_hash(10.0, 10.0, precision=6)
        assert h1 != h2

    def test_deterministic(self):
        # Same input must always produce the same hash (no randomness, no time dependence)
        h1 = lonlat_to_hash(12.345, 67.890, precision=7)
        h2 = lonlat_to_hash(12.345, 67.890, precision=7)
        assert h1 == h2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    @pytest.mark.parametrize("lon,lat", EDGE_POINTS)
    def test_edges_produce_valid_hash(self, lon, lat):
        # Boundary coordinates (world corners) must not crash and must yield digit-only hashes
        h = lonlat_to_hash(lon, lat, precision=6)
        assert DIGITS_RE.fullmatch(h)

    @pytest.mark.parametrize("lon,lat", EDGE_POINTS)
    def test_edges_round_trip(self, lon, lat):
        # Even at extreme corners, the round-trip (encode -> decode bbox -> point check) must hold
        h = lonlat_to_hash(lon, lat, precision=9)
        bbox = hash_to_bbox(h)
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
            lonlat_to_hash(lon, lat, precision=6)

    def test_precision_zero_raises(self):
        # precision=0 is invalid — at least one digit is required
        with pytest.raises(ValueError):
            lonlat_to_hash(0, 0, precision=0)

    @pytest.mark.parametrize("bad", ["abc", "", "12 34", "-5"])
    def test_bad_hash_raises_value_error(self, bad):
        # Malformed hash strings (non-numeric, empty, spaces, negatives) must raise ValueError
        with pytest.raises(ValueError):
            hash_to_bbox(bad)


# ---------------------------------------------------------------------------
# Neighborhood
# ---------------------------------------------------------------------------

class TestNeighbors:

    def test_eight_neighbors(self):
        # neighbors() must return exactly 8 cells (N, NE, E, SE, S, SW, W, NW)
        h = lonlat_to_hash(10.0, 20.0, precision=6)
        nbrs = neighbors(h)
        assert len(nbrs) == 8

    def test_neighbors_are_valid_hashes(self):
        # Every neighbor must be a valid digit-only hash string
        h = lonlat_to_hash(10.0, 20.0, precision=6)
        for n in neighbors(h):
            assert DIGITS_RE.fullmatch(n)

    def test_neighbors_touch_original(self):
        # Each neighbor cell's bbox must share at least a partial overlap with the original cell
        lon, lat = 10.0, 20.0
        h = lonlat_to_hash(lon, lat, precision=8)
        bbox = hash_to_bbox(h)
        min_lon, min_lat, max_lon, max_lat = bbox
        for n in neighbors(h):
            nb = hash_to_bbox(n)
            n_min_lon, n_min_lat, n_max_lon, n_max_lat = nb
            lon_overlap = n_max_lon > min_lon and n_min_lon < max_lon
            lat_overlap = n_max_lat > min_lat and n_min_lat < max_lat
            assert lon_overlap and lat_overlap, \
                f"neighbor {n} bbox {nb} does not touch cell {bbox}"


# ---------------------------------------------------------------------------
# Bbox tiling
# ---------------------------------------------------------------------------

class TestBboxTiling:

    def test_tiling_covers_region(self):
        # Every cell returned for a region must actually overlap that region's bbox
        min_lon, min_lat, max_lon, max_lat = -1.0, 48.0, 1.0, 50.0
        cells = encode_bbox(min_lon, min_lat, max_lon, max_lat, precision=5)
        assert len(cells) > 0
        for cell_hash in cells:
            assert DIGITS_RE.fullmatch(cell_hash)
            cb = hash_to_bbox(cell_hash)
            overlap_lon = cb[2] > min_lon and cb[0] < max_lon
            overlap_lat = cb[3] > min_lat and cb[1] < max_lat
            assert overlap_lon and overlap_lat, \
                f"cell {cell_hash} bbox {cb} does not overlap " \
                f"target ({min_lon},{min_lat},{max_lon},{max_lat})"

    def test_tiling_single_point(self):
        # A tiny bbox around a single point must return at least one cell that contains that point
        cells = encode_bbox(2.35, 48.85, 2.3501, 48.8501, precision=8)
        assert len(cells) >= 1
        bbox = hash_to_bbox(cells[0])
        assert contains_point(bbox, 2.35, 48.85)
