-- Development-only seed data.
-- Coordinates and reports are approximate/fake and must not be used as verified production data.

INSERT INTO ski_resorts (name, country, region, location, data_source, is_verified)
VALUES
    ('Baqueira Beret', 'Spain', 'Val d''Aran', ST_SetSRID(ST_MakePoint(0.9326, 42.6985), 4326), 'dev_seed', FALSE),
    ('Formigal-Panticosa', 'Spain', 'Huesca', ST_SetSRID(ST_MakePoint(-0.3632, 42.7753), 4326), 'dev_seed', FALSE),
    ('Sierra Nevada', 'Spain', 'Granada', ST_SetSRID(ST_MakePoint(-3.4006, 37.0956), 4326), 'dev_seed', FALSE),
    ('Grandvalira', 'Andorra', 'Canillo / Encamp', ST_SetSRID(ST_MakePoint(1.6670, 42.5775), 4326), 'dev_seed', FALSE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO roads (resort_id, name, route, data_source, is_verified)
SELECT id, 'C-28', ST_GeomFromText('LINESTRING(0.7950 42.7010, 0.8650 42.7020, 0.9326 42.6985)', 4326), 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Baqueira Beret'
ON CONFLICT DO NOTHING;

INSERT INTO roads (resort_id, name, route, data_source, is_verified)
SELECT id, 'A-136', ST_GeomFromText('LINESTRING(-0.4100 42.7580, -0.3860 42.7670, -0.3632 42.7753)', 4326), 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Formigal-Panticosa'
ON CONFLICT DO NOTHING;

INSERT INTO roads (resort_id, name, route, data_source, is_verified)
SELECT id, 'A-395', ST_GeomFromText('LINESTRING(-3.4590 37.1320, -3.4300 37.1140, -3.4006 37.0956)', 4326), 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Sierra Nevada'
ON CONFLICT DO NOTHING;

INSERT INTO roads (resort_id, name, route, data_source, is_verified)
SELECT id, 'CG-2', ST_GeomFromText('LINESTRING(1.5900 42.5420, 1.6200 42.5570, 1.6670 42.5775)', 4326), 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Grandvalira'
ON CONFLICT DO NOTHING;

INSERT INTO snow_reports (
    resort_id,
    open_lifts,
    total_lifts,
    open_km,
    total_km,
    snow_depth_min_cm,
    snow_depth_max_cm,
    avalanche_risk,
    access_status,
    open_green_trails,
    total_green_trails,
    open_blue_trails,
    total_blue_trails,
    open_red_trails,
    total_red_trails,
    open_black_trails,
    total_black_trails,
    data_source,
    is_verified
)
SELECT id, 28, 36, 110.50, 167.00, 80, 145, 2, 'Open', 5, 6, 28, 30, 32, 36, 6, 8, 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Baqueira Beret';

INSERT INTO snow_reports (
    resort_id,
    open_lifts,
    total_lifts,
    open_km,
    total_km,
    snow_depth_min_cm,
    snow_depth_max_cm,
    avalanche_risk,
    access_status,
    open_green_trails,
    total_green_trails,
    open_blue_trails,
    total_blue_trails,
    open_red_trails,
    total_red_trails,
    open_black_trails,
    total_black_trails,
    data_source,
    is_verified
)
SELECT id, 24, 37, 92.00, 182.00, 45, 100, 3, 'Chains recommended', 4, 5, 21, 28, 24, 38, 3, 9, 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Formigal-Panticosa';

INSERT INTO weather_reports (
    resort_id,
    temperature_celsius,
    wind_speed_kmh,
    wind_direction,
    precipitation_mm,
    visibility_m,
    weather,
    data_source,
    is_verified
)
SELECT id, -3.5, 18.0, 'NW', 0.00, 8000, 'Partly cloudy', 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Baqueira Beret';

INSERT INTO weather_reports (
    resort_id,
    temperature_celsius,
    wind_speed_kmh,
    wind_direction,
    precipitation_mm,
    visibility_m,
    weather,
    data_source,
    is_verified
)
SELECT id, -1.0, 24.5, 'N', 1.20, 3500, 'Snow showers', 'dev_seed', FALSE
FROM ski_resorts
WHERE name = 'Formigal-Panticosa';

INSERT INTO road_conditions (road_id, status, details, data_source, is_verified)
SELECT id, 'Open', 'Road open. Drive carefully in shaded areas.', 'dev_seed', FALSE
FROM roads
WHERE name = 'C-28';

INSERT INTO road_conditions (road_id, status, details, data_source, is_verified)
SELECT id, 'Chains recommended', 'Snow and ice patches near the resort access.', 'dev_seed', FALSE
FROM roads
WHERE name = 'A-136';
