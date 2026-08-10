-- OGN -> GeoParquet cleaning pipeline (DuckDB).
--
-- The download phase (scripts/download_ogn.py) streams real-time APRS beacons
-- from OpenGliderNetwork for hours -> one JSONL per day. This cleaning phase
-- is a separate, fast (~3s) DuckDB job: it de-duplicates, drops inconsistent
-- tracks and exports a Parquet.
--
-- Paths and thresholds are tokens (__JSONL__, __PARQUET__, __MAX_TS_DRIFT_SEC__,
-- __MIN_TRACK_POINTS__) injected by scripts/run_ogn_clean.py so this file
-- contains no magic numbers. __PARQUET__ is the JSONL input with its extension
-- swapped (.jsonl -> .parquet).

INSTALL spatial; LOAD spatial;
INSTALL json;   LOAD json;

CREATE TABLE ogn AS (
	SELECT
		address,
		address_type,
		dstcall,
		name,
		aircraft_type,
		beacon_type,
		timestamp: timestamp::timestamptz,
		lon_lat: ST_Point(median(longitude), median(latitude)),
		ground_speed: median(ground_speed),
		climb_rate: median(climb_rate),
		turn_rate: median(turn_rate),
		gps_quality: median(try_cast(split_part(gps_quality, 'x', 2) AS INTEGER))
	FROM read_json_auto('__JSONL__')
	WHERE abs(datediff('second', reference_timestamp::timestamptz, timestamp::timestamptz)) <= __MAX_TS_DRIFT_SEC__
	GROUP BY address, address_type, dstcall, name, aircraft_type, beacon_type, timestamp
	ORDER BY address, timestamp
);

-- Remove beacons with no address/name correlation
DELETE FROM ogn WHERE name IN (
	SELECT name
	FROM ogn
	GROUP BY name
	HAVING count(DISTINCT address) = 0 OR count(DISTINCT address) > 1
);
DELETE FROM ogn WHERE address IN (
	SELECT address
	FROM ogn
	GROUP BY address
	HAVING count(DISTINCT name) = 0 OR count(DISTINCT name) > 1
);

-- Remove tracks that are too short
DELETE FROM ogn WHERE address IN (
	SELECT address
	FROM ogn
	GROUP BY address
	HAVING count(*) < __MIN_TRACK_POINTS__
);

CHECKPOINT;
COPY ogn TO '__PARQUET__' (FORMAT PARQUET);
