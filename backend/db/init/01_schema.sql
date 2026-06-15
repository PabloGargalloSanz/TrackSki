CREATE EXTENSION IF NOT EXISTS postgis;

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
    resort_id INT REFERENCES ski_resorts(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    route GEOMETRY(LineString, 4326) NOT NULL,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_roads_resort_name UNIQUE (resort_id, name)
);

CREATE TABLE IF NOT EXISTS road_conditions (
    id SERIAL PRIMARY KEY,
    road_id INT NOT NULL REFERENCES roads(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    details TEXT,
    data_source VARCHAR(100) NOT NULL DEFAULT 'manual',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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
    CONSTRAINT chk_snow_reports_lifts CHECK (open_lifts >= 0 AND total_lifts >= 0 AND open_lifts <= total_lifts),
    CONSTRAINT chk_snow_reports_km CHECK (open_km >= 0 AND total_km >= 0 AND open_km <= total_km),
    CONSTRAINT chk_snow_reports_depth CHECK (
        snow_depth_min_cm IS NULL
        OR snow_depth_max_cm IS NULL
        OR snow_depth_min_cm <= snow_depth_max_cm
    ),
    CONSTRAINT chk_snow_reports_avalanche CHECK (avalanche_risk IS NULL OR avalanche_risk BETWEEN 1 AND 5),
    CONSTRAINT chk_snow_reports_green CHECK (open_green_trails >= 0 AND total_green_trails >= 0 AND open_green_trails <= total_green_trails),
    CONSTRAINT chk_snow_reports_blue CHECK (open_blue_trails >= 0 AND total_blue_trails >= 0 AND open_blue_trails <= total_blue_trails),
    CONSTRAINT chk_snow_reports_red CHECK (open_red_trails >= 0 AND total_red_trails >= 0 AND open_red_trails <= total_red_trails),
    CONSTRAINT chk_snow_reports_black CHECK (open_black_trails >= 0 AND total_black_trails >= 0 AND open_black_trails <= total_black_trails)
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
    CONSTRAINT uq_weather_alerts_identifier_area UNIQUE (identifier, area),
    CONSTRAINT chk_weather_alerts_level CHECK (
        level IN ('verde', 'amarillo', 'naranja', 'rojo', 'desconocido')
    ),
    CONSTRAINT chk_weather_alerts_dates CHECK (
        onset IS NULL OR expires IS NULL OR onset <= expires
    )
);

CREATE INDEX IF NOT EXISTS idx_ski_resorts_location ON ski_resorts USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_roads_route ON roads USING GIST(route);
CREATE INDEX IF NOT EXISTS idx_roads_resort_id ON roads(resort_id);
CREATE INDEX IF NOT EXISTS idx_road_conditions_road_reported_at ON road_conditions(road_id, reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_snow_reports_resort_reported_at ON snow_reports(resort_id, reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_weather_reports_resort_reported_at ON weather_reports(resort_id, reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_weather_alerts_expires ON weather_alerts(expires);
CREATE INDEX IF NOT EXISTS idx_weather_alerts_area ON weather_alerts(area);
