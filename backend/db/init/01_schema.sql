CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. TABLAS BASE
 
CREATE TABLE IF NOT EXISTS ski_resorts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(80) NOT NULL DEFAULT 'Spain',
    region VARCHAR(100),
    location GEOMETRY(Point, 4326) NOT NULL,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS roads (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(150),
    route GEOMETRY(LineString, 4326),
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_roads_code_source UNIQUE (code, data_source)
);


CREATE TABLE IF NOT EXISTS resort_access_roads (
    id SERIAL PRIMARY KEY,
    resort_id INT NOT NULL REFERENCES ski_resorts(id) ON DELETE CASCADE,
    road_id INT NOT NULL REFERENCES roads(id) ON DELETE CASCADE,
    access_role VARCHAR(50) NOT NULL DEFAULT 'primary',
    segment_description TEXT,
    from_km DECIMAL(8,3),
    to_km DECIMAL(8,3),
    priority INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_resort_access_roads UNIQUE (
        resort_id,
        road_id,
        access_role,
        from_km,
        to_km
    ),

    CONSTRAINT chk_resort_access_roads_role CHECK (
        access_role IN ('primary', 'secondary', 'alternative', 'approach', 'final_access')
    ),

    CONSTRAINT chk_resort_access_roads_km CHECK (
        from_km IS NULL
        OR to_km IS NULL
        OR from_km <= to_km
    ),

    CONSTRAINT chk_resort_access_roads_priority CHECK (
        priority > 0
    )
);


-- 2. RUTAS COMPLETAS DESDE ORIGEN

CREATE TABLE IF NOT EXISTS access_routes (
    id SERIAL PRIMARY KEY,
    resort_id INT NOT NULL REFERENCES ski_resorts(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    origin_label VARCHAR(100) NOT NULL,
    route_type VARCHAR(30) NOT NULL DEFAULT 'primary',
    description TEXT,
    route GEOMETRY(LineString, 4326),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_access_routes_type CHECK (
        route_type IN ('primary', 'alternative')
    ),

    CONSTRAINT uq_access_routes_resort_origin_type_name UNIQUE (
        resort_id,
        origin_label,
        route_type,
        name
    )
);


CREATE TABLE IF NOT EXISTS access_route_segments (
    id SERIAL PRIMARY KEY,
    access_route_id INT NOT NULL REFERENCES access_routes(id) ON DELETE CASCADE,
    resort_access_road_id INT NOT NULL REFERENCES resort_access_roads(id) ON DELETE CASCADE,
    segment_order INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_access_route_segments_order CHECK (
        segment_order > 0
    ),

    CONSTRAINT uq_access_route_segments_order UNIQUE (
        access_route_id,
        segment_order
    ),

    CONSTRAINT uq_access_route_segments_access_road UNIQUE (
        access_route_id,
        resort_access_road_id
    )
);


-- 3. CARRETERAS: CONDICIONES, INCIDENCIAS Y ALTERNATIVAS
 

CREATE TABLE IF NOT EXISTS road_conditions (
    id SERIAL PRIMARY KEY,
    road_id INT NOT NULL REFERENCES roads(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'unknown',
    details TEXT,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    source_updated_at TIMESTAMP WITH TIME ZONE,
    raw_payload JSONB,
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS road_incidents (
    id SERIAL PRIMARY KEY,
    road_id INT REFERENCES roads(id) ON DELETE SET NULL,
    source VARCHAR(100) NOT NULL,
    source_id VARCHAR(255),
    road_code VARCHAR(30),
    title VARCHAR(255),
    description TEXT,
    incident_type VARCHAR(80) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    severity VARCHAR(50) NOT NULL DEFAULT 'unknown',
    start_km DECIMAL(8,3),
    end_km DECIMAL(8,3),
    direction VARCHAR(100),
    location GEOMETRY(Point, 4326),
    affected_route GEOMETRY(LineString, 4326),
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    reported_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_road_incidents_source_source_id UNIQUE (
        source,
        source_id
    ),

    CONSTRAINT chk_road_incidents_status CHECK (
        status IN ('active', 'planned', 'resolved', 'unknown')
    ),

    CONSTRAINT chk_road_incidents_severity CHECK (
        severity IN ('low', 'medium', 'high', 'critical', 'unknown')
    ),

    CONSTRAINT chk_road_incidents_km CHECK (
        start_km IS NULL
        OR end_km IS NULL
        OR start_km <= end_km
    )
);


CREATE TABLE IF NOT EXISTS road_alternatives (
    id SERIAL PRIMARY KEY,
    resort_id INT NOT NULL REFERENCES ski_resorts(id) ON DELETE CASCADE,
    affected_road_id INT REFERENCES roads(id) ON DELETE SET NULL,
    alternative_road_id INT REFERENCES roads(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_road_alternatives_priority CHECK (
        priority > 0
    )
);


-- 4. NIEVE Y METEOROLOGÍA
 

CREATE TABLE IF NOT EXISTS snow_reports (
    id SERIAL PRIMARY KEY,
    resort_id INT NOT NULL REFERENCES ski_resorts(id) ON DELETE CASCADE,
    open_lifts INT NOT NULL DEFAULT 0,
    total_lifts INT NOT NULL DEFAULT 0,
    open_km DECIMAL(6,2) NOT NULL DEFAULT 0,
    total_km DECIMAL(6,2) NOT NULL DEFAULT 0,
    snow_depth_min_cm INT,
    snow_depth_max_cm INT,
    avalanche_risk INT,
    access_status VARCHAR(100),
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    open_green_trails INT NOT NULL DEFAULT 0,
    total_green_trails INT NOT NULL DEFAULT 0,
    open_blue_trails INT NOT NULL DEFAULT 0,
    total_blue_trails INT NOT NULL DEFAULT 0,
    open_red_trails INT NOT NULL DEFAULT 0,
    total_red_trails INT NOT NULL DEFAULT 0,
    open_black_trails INT NOT NULL DEFAULT 0,
    total_black_trails INT NOT NULL DEFAULT 0,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT chk_snow_reports_lifts CHECK (
        open_lifts >= 0
        AND total_lifts >= 0
        AND open_lifts <= total_lifts
    ),

    CONSTRAINT chk_snow_reports_km CHECK (
        open_km >= 0
        AND total_km >= 0
        AND open_km <= total_km
    ),

    CONSTRAINT chk_snow_reports_depth CHECK (
        snow_depth_min_cm IS NULL
        OR snow_depth_max_cm IS NULL
        OR snow_depth_min_cm <= snow_depth_max_cm
    ),

    CONSTRAINT chk_snow_reports_avalanche CHECK (
        avalanche_risk IS NULL
        OR avalanche_risk BETWEEN 1 AND 5
    ),

    CONSTRAINT chk_snow_reports_green CHECK (
        open_green_trails >= 0
        AND total_green_trails >= 0
        AND open_green_trails <= total_green_trails
    ),

    CONSTRAINT chk_snow_reports_blue CHECK (
        open_blue_trails >= 0
        AND total_blue_trails >= 0
        AND open_blue_trails <= total_blue_trails
    ),

    CONSTRAINT chk_snow_reports_red CHECK (
        open_red_trails >= 0
        AND total_red_trails >= 0
        AND open_red_trails <= total_red_trails
    ),

    CONSTRAINT chk_snow_reports_black CHECK (
        open_black_trails >= 0
        AND total_black_trails >= 0
        AND open_black_trails <= total_black_trails
    )
);


CREATE TABLE IF NOT EXISTS weather_reports (
    id SERIAL PRIMARY KEY,
    resort_id INT NOT NULL REFERENCES ski_resorts(id) ON DELETE CASCADE,
    temperature_celsius DECIMAL(4,1),
    wind_speed_kmh DECIMAL(5,1),
    wind_direction VARCHAR(20),
    precipitation_mm DECIMAL(6,2),
    visibility_m INT,
    weather VARCHAR(80),
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS weather_alerts (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    level VARCHAR(20) NOT NULL,
    event VARCHAR(120) NOT NULL,
    area VARCHAR(255) NOT NULL,
    onset TIMESTAMP WITH TIME ZONE,
    expires TIMESTAMP WITH TIME ZONE,
    headline TEXT,
    description TEXT,
    instruction TEXT,
    data_source VARCHAR(100) NOT NULL DEFAULT 'aemet',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_weather_alerts_identifier_area UNIQUE (
        identifier,
        area
    ),

    CONSTRAINT chk_weather_alerts_level CHECK (
        level IN ('verde', 'amarillo', 'naranja', 'rojo', 'desconocido')
    ),

    CONSTRAINT chk_weather_alerts_dates CHECK (
        onset IS NULL
        OR expires IS NULL
        OR onset <= expires
    )
);


-- 5. ÍNDICES ESPACIALES
 

CREATE INDEX IF NOT EXISTS idx_ski_resorts_location
ON ski_resorts USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_roads_route
ON roads USING GIST(route);

CREATE INDEX IF NOT EXISTS idx_access_routes_route
ON access_routes USING GIST(route);

CREATE INDEX IF NOT EXISTS idx_road_incidents_location
ON road_incidents USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_road_incidents_affected_route
ON road_incidents USING GIST(affected_route);

 
-- 6. ÍNDICES GENERALES
 

CREATE INDEX IF NOT EXISTS idx_roads_code
ON roads(code);

CREATE INDEX IF NOT EXISTS idx_resort_access_roads_resort_id
ON resort_access_roads(resort_id);

CREATE INDEX IF NOT EXISTS idx_resort_access_roads_road_id
ON resort_access_roads(road_id);

CREATE INDEX IF NOT EXISTS idx_resort_access_roads_km
ON resort_access_roads(road_id, from_km, to_km);

CREATE INDEX IF NOT EXISTS idx_access_routes_resort_id
ON access_routes(resort_id);

CREATE INDEX IF NOT EXISTS idx_access_routes_origin_label
ON access_routes(origin_label);

CREATE INDEX IF NOT EXISTS idx_access_routes_route_type
ON access_routes(route_type);

CREATE INDEX IF NOT EXISTS idx_access_route_segments_route_id
ON access_route_segments(access_route_id);

CREATE INDEX IF NOT EXISTS idx_access_route_segments_resort_access_road_id
ON access_route_segments(resort_access_road_id);

CREATE INDEX IF NOT EXISTS idx_road_conditions_road_reported_at
ON road_conditions(road_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_road_incidents_road_id
ON road_incidents(road_id);

CREATE INDEX IF NOT EXISTS idx_road_incidents_status
ON road_incidents(status);

CREATE INDEX IF NOT EXISTS idx_road_incidents_road_code
ON road_incidents(road_code);

CREATE INDEX IF NOT EXISTS idx_road_incidents_updated_at
ON road_incidents(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_road_alternatives_resort_id
ON road_alternatives(resort_id);

CREATE INDEX IF NOT EXISTS idx_road_alternatives_affected_road_id
ON road_alternatives(affected_road_id);

CREATE INDEX IF NOT EXISTS idx_road_alternatives_alternative_road_id
ON road_alternatives(alternative_road_id);

CREATE INDEX IF NOT EXISTS idx_snow_reports_resort_reported_at
ON snow_reports(resort_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_weather_reports_resort_reported_at
ON weather_reports(resort_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_weather_alerts_expires
ON weather_alerts(expires);

CREATE INDEX IF NOT EXISTS idx_weather_alerts_area
ON weather_alerts(area);


-- 7. VISTAS
 

CREATE OR REPLACE VIEW view_resort_access_roads_detail AS
SELECT
    rar.id AS resort_access_road_id,
    sr.id AS resort_id,
    sr.name AS resort_name,
    r.id AS road_id,
    r.code AS road_code,
    r.name AS road_name,
    rar.access_role,
    rar.segment_description,
    rar.from_km,
    rar.to_km,
    rar.priority,
    rar.is_active,
    rar.data_source,
    rar.is_verified
FROM resort_access_roads rar
JOIN ski_resorts sr ON sr.id = rar.resort_id
JOIN roads r ON r.id = rar.road_id;


CREATE OR REPLACE VIEW view_access_route_segments_detail AS
SELECT
    ar.id AS access_route_id,
    ar.name AS access_route_name,
    ar.origin_label,
    ar.route_type,
    ar.resort_id,
    sr.name AS resort_name,
    ars.id AS access_route_segment_id,
    ars.segment_order,
    rar.id AS resort_access_road_id,
    r.id AS road_id,
    r.code AS road_code,
    r.name AS road_name,
    rar.access_role,
    rar.from_km,
    rar.to_km,
    rar.segment_description,
    rar.priority,
    ars.is_active AS segment_is_active,
    ar.is_active AS route_is_active,
    ST_AsGeoJSON(ar.route) AS access_route_geojson,
    ST_AsGeoJSON(r.route) AS road_geojson
FROM access_route_segments ars
JOIN access_routes ar ON ar.id = ars.access_route_id
JOIN ski_resorts sr ON sr.id = ar.resort_id
JOIN resort_access_roads rar ON rar.id = ars.resort_access_road_id
JOIN roads r ON r.id = rar.road_id;


CREATE OR REPLACE VIEW view_active_road_incidents_detail AS
SELECT
    ri.id AS road_incident_id,
    ri.source,
    ri.source_id,
    ri.road_id,
    r.code AS matched_road_code,
    ri.road_code AS source_road_code,
    ri.title,
    ri.description,
    ri.incident_type,
    ri.status,
    ri.severity,
    ri.start_km,
    ri.end_km,
    ri.direction,
    ST_AsGeoJSON(ri.location) AS location_geojson,
    ri.starts_at,
    ri.ends_at,
    ri.reported_at,
    ri.updated_at
FROM road_incidents ri
LEFT JOIN roads r ON r.id = ri.road_id
WHERE ri.status = 'active';