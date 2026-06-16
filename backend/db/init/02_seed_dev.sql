-- Development-only seed data.
-- Coordinates and reports are approximate/fake and must not be used as verified production data.

INSERT INTO ski_resorts (name, country, region, location, data_source, is_verified)
VALUES
    ('Baqueira Beret', 'Spain', 'Val d''Aran', ST_SetSRID(ST_MakePoint(0.9326, 42.6985), 4326), 'dev_seed', FALSE),
    ('Formigal-Panticosa', 'Spain', 'Huesca', ST_SetSRID(ST_MakePoint(-0.3632, 42.7753), 4326), 'dev_seed', FALSE),
    ('Sierra Nevada', 'Spain', 'Granada', ST_SetSRID(ST_MakePoint(-3.4006, 37.0956), 4326), 'dev_seed', FALSE),
    ('Grandvalira', 'Andorra', 'Canillo / Encamp', ST_SetSRID(ST_MakePoint(1.6670, 42.5775), 4326), 'dev_seed', FALSE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO roads (code, name, route, data_source, is_verified)
VALUES ('C-28', 'C-28 acceso Val d''Aran', ST_GeomFromText('LINESTRING(0.7950 42.7010, 0.8650 42.7020, 0.9326 42.6985)', 4326), 'dev_seed', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO roads (code, name, route, data_source, is_verified)
VALUES ('A-136', 'A-136 acceso Valle de Tena', ST_GeomFromText('LINESTRING(-0.4100 42.7580, -0.3860 42.7670, -0.3632 42.7753)', 4326), 'dev_seed', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO roads (code, name, route, data_source, is_verified)
VALUES ('A-395', 'A-395 acceso Sierra Nevada', ST_GeomFromText('LINESTRING(-3.4590 37.1320, -3.4300 37.1140, -3.4006 37.0956)', 4326), 'dev_seed', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO roads (code, name, route, data_source, is_verified)
VALUES ('CG-2', 'CG-2 acceso Grandvalira', ST_GeomFromText('LINESTRING(1.5900 42.5420, 1.6200 42.5570, 1.6670 42.5775)', 4326), 'dev_seed', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO resort_access_roads (
    resort_id,
    road_id,
    access_role,
    segment_description,
    priority,
    data_source,
    is_verified
)
SELECT ski_resorts.id, roads.id, 'primary', 'Acceso principal aproximado a Baqueira Beret', 1, 'dev_seed', FALSE
FROM ski_resorts
JOIN roads ON roads.code = 'C-28'
WHERE ski_resorts.name = 'Baqueira Beret'
ON CONFLICT DO NOTHING;

INSERT INTO resort_access_roads (
    resort_id,
    road_id,
    access_role,
    segment_description,
    priority,
    data_source,
    is_verified
)
SELECT ski_resorts.id, roads.id, 'primary', 'Acceso principal aproximado a Formigal-Panticosa', 1, 'dev_seed', FALSE
FROM ski_resorts
JOIN roads ON roads.code = 'A-136'
WHERE ski_resorts.name = 'Formigal-Panticosa'
ON CONFLICT DO NOTHING;

INSERT INTO resort_access_roads (
    resort_id,
    road_id,
    access_role,
    segment_description,
    priority,
    data_source,
    is_verified
)
SELECT ski_resorts.id, roads.id, 'primary', 'Acceso principal aproximado a Sierra Nevada', 1, 'dev_seed', FALSE
FROM ski_resorts
JOIN roads ON roads.code = 'A-395'
WHERE ski_resorts.name = 'Sierra Nevada'
ON CONFLICT DO NOTHING;

INSERT INTO resort_access_roads (
    resort_id,
    road_id,
    access_role,
    segment_description,
    priority,
    data_source,
    is_verified
)
SELECT ski_resorts.id, roads.id, 'primary', 'Acceso principal aproximado a Grandvalira', 1, 'dev_seed', FALSE
FROM ski_resorts
JOIN roads ON roads.code = 'CG-2'
WHERE ski_resorts.name = 'Grandvalira'
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

INSERT INTO road_conditions (road_id, status, severity, details, data_source, is_verified)
SELECT id, 'open', 'low', 'Road open. Drive carefully in shaded areas.', 'dev_seed', FALSE
FROM roads
WHERE code = 'C-28';

INSERT INTO road_conditions (road_id, status, severity, details, data_source, is_verified)
SELECT id, 'chains', 'medium', 'Snow and ice patches near the resort access.', 'dev_seed', FALSE
FROM roads
WHERE code = 'A-136';
