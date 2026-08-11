BEGIN;

-- 1. ESTACIONES
-- Coordenadas: ST_MakePoint(longitud, latitud)
 

INSERT INTO ski_resorts (
    name,
    country,
    region,
    location,
    data_source,
    is_verified
)
VALUES
    (
        'Astún',
        'Spain',
        'Huesca',
        ST_SetSRID(ST_MakePoint(-0.508244507873974, 42.80922781475311), 4326),
        'manual',
        TRUE
    ),
    (
        'Candanchú',
        'Spain',
        'Huesca',
        ST_SetSRID(ST_MakePoint(-0.5358326000512351, 42.786731393599275), 4326),
        'manual',
        TRUE
    ),
    (
        'Formigal',
        'Spain',
        'Huesca',
        ST_SetSRID(ST_MakePoint(-0.37097664437118283, 42.77524095161353), 4326),
        'manual',
        TRUE
    ),
    (
        'Panticosa',
        'Spain',
        'Huesca',
        ST_SetSRID(ST_MakePoint(-0.2807800271958615, 42.72141802204165), 4326),
        'manual',
        TRUE
    ),
    (
        'Cerler',
        'Spain',
        'Huesca',
        ST_SetSRID(ST_MakePoint(0.5398864949114519, 42.58826080586972), 4326),
        'manual',
        TRUE
    ),
    (
        'Baqueira Beret',
        'Spain',
        'Val d''Aran',
        ST_SetSRID(ST_MakePoint(0.9344712774949624, 42.69699748896903), 4326),
        'manual',
        TRUE
    ),
    (
        'Grandvalira',
        'Andorra',
        'Canillo / Encamp',
        ST_SetSRID(ST_MakePoint(1.6470481627074312, 42.57893755848369), 4326),
        'manual',
        TRUE
    ),
    (
        'Valdelinares',
        'Spain',
        'Teruel',
        ST_SetSRID(ST_MakePoint(-0.6330205974713369, 40.37907417519346), 4326),
        'manual',
        TRUE
    )
ON CONFLICT (name)
DO UPDATE SET
    country = EXCLUDED.country,
    region = EXCLUDED.region,
    location = EXCLUDED.location,
    data_source = EXCLUDED.data_source,
    is_verified = EXCLUDED.is_verified,
    updated_at = CURRENT_TIMESTAMP;


 
-- 2. CARRETERAS
 

INSERT INTO roads (
    code,
    name,
    route,
    data_source,
    is_verified
)
VALUES
    ('A-23', 'Autovía Mudéjar / Monrepós', NULL, 'manual', TRUE),
    ('N-330', 'N-330 Sabiñánigo - Jaca - Canfranc', NULL, 'manual', TRUE),
    ('N-330a', 'N-330a Jaca - Canfranc - Candanchú - Astún', NULL, 'manual', TRUE),
    ('SC-22130-09', 'Acceso final a Astún', NULL, 'manual', TRUE),

    ('N-260a', 'N-260a Sabiñánigo - Biescas', NULL, 'manual', TRUE),
    ('A-136', 'A-136 Biescas - Formigal - Portalet', NULL, 'manual', TRUE),
    ('A-2606', 'A-2606 acceso Panticosa', NULL, 'manual', TRUE),

    ('N-123', 'N-123 Barbastro - Graus - Campo', NULL, 'manual', TRUE),
    ('N-123a', 'N-123a Barbastro - Graus - Campo', NULL, 'manual', TRUE),
    ('A-139', 'A-139 Campo - Benasque - Cerler', NULL, 'manual', TRUE),
    ('A-2617', 'A-2617 acceso Cerler / Ampriu', NULL, 'manual', TRUE),

    ('N-230', 'N-230 Benabarre - Pont de Suert - Vielha', NULL, 'manual', TRUE),
    ('C-28', 'C-28 Vielha - Baqueira', NULL, 'manual', TRUE),

    ('C-14', 'C-14 Ponts - Oliana - Adrall', NULL, 'manual', TRUE),
    ('N-260', 'N-260 tramo La Seu d''Urgell', NULL, 'manual', TRUE),
    ('N-145', 'N-145 La Seu d''Urgell - Andorra', NULL, 'manual', TRUE),
    ('CG-1', 'CG-1 Andorra', NULL, 'manual', TRUE),
    ('CG-2', 'CG-2 Encamp - Canillo - Soldeu - Pas de la Casa', NULL, 'manual', TRUE),

    ('A-228', 'A-228 Mora de Rubielos - Alcalá de la Selva - Valdelinares', NULL, 'manual', TRUE),
    ('VF-TE-01', 'VF-TE-01 acceso Valdelinares', NULL, 'manual', TRUE)
ON CONFLICT (code, data_source)
DO UPDATE SET
    name = EXCLUDED.name,
    is_verified = EXCLUDED.is_verified,
    updated_at = CURRENT_TIMESTAMP;


 
-- 3. TRAMOS RELEVANTES POR ESTACIÓN
-- Fuente principal para cruzar incidencias DGT por carretera + km.
 

WITH access_data AS (
    SELECT *
    FROM (
        VALUES
            -- ASTÚN
            ('Astún', 'A-23', 'approach', 356.000, 394.000, 'Tramo Monrepós: Nueno - Arguis - Lanave.', 3),
            ('Astún', 'N-330', 'primary', 614.000, 666.000, 'Tramo Sabiñánigo - Jaca - Canfranc.', 2),
            ('Astún', 'N-330A', 'final_access', NULL, NULL, 'Subida final Jaca - Canfranc - Candanchú - Astún.', 1),
            ('Astún', 'SC-22130-09', 'final_access', NULL, NULL, 'Entrada final a Astún.', 1),

            -- CANDANCHÚ
            ('Candanchú', 'A-23', 'approach', 356.000, 394.000, 'Tramo Monrepós: Nueno - Arguis - Lanave.', 3),
            ('Candanchú', 'N-330', 'primary', 614.000, 666.000, 'Tramo Sabiñánigo - Jaca - Canfranc.', 2),
            ('Candanchú', 'N-330A', 'final_access', NULL, NULL, 'Subida final Jaca - Canfranc - Candanchú.', 1),

            -- FORMIGAL
            ('Formigal', 'A-23', 'approach', 356.000, 394.000, 'Tramo Monrepós hacia Sabiñánigo/Biescas.', 3),
            ('Formigal', 'N-330', 'approach', 614.000, 633.000, 'Tramo de aproximación hacia Sabiñánigo.', 3),
            ('Formigal', 'N-260A', 'approach', 509.000, 517.000, 'Tramo Sabiñánigo - Biescas.', 2),
            ('Formigal', 'A-136', 'final_access', 0.000, 27.000, 'Acceso por Valle de Tena: Biescas - Formigal - Portalet.', 1),

            -- PANTICOSA
            ('Panticosa', 'A-23', 'approach', 356.000, 394.000, 'Tramo Monrepós hacia Sabiñánigo/Biescas.', 3),
            ('Panticosa', 'N-330', 'approach', 614.000, 633.000, 'Tramo de aproximación hacia Sabiñánigo.', 3),
            ('Panticosa', 'N-260A', 'approach', 509.000, 517.000, 'Tramo Sabiñánigo - Biescas.', 2),
            ('Panticosa', 'A-136', 'primary', 0.000, 27.000, 'Acceso por Valle de Tena hacia Panticosa.', 1),
            ('Panticosa', 'A-2606', 'final_access', 0.000, 4.500, 'Acceso final a Panticosa.', 1),

            -- CERLER
            ('Cerler', 'N-123', 'approach', 0.000, 30.000, 'Tramo Barbastro - Graus - Campo.', 3),
            ('Cerler', 'N-123A', 'approach', 0.000, 30.000, 'Tramo Barbastro - Graus - Campo.', 3),
            ('Cerler', 'A-139', 'primary', 0.000, 63.000, 'Tramo Campo - Castejón de Sos - Benasque - Cerler.', 2),
            ('Cerler', 'A-2617', 'final_access', 0.000, 4.000, 'Subida final Cerler / Ampriu.', 1),

            -- BAQUEIRA BERET
            ('Baqueira Beret', 'N-230', 'approach', 70.000, 165.000, 'Tramo Benabarre - Pont de Suert - Túnel de Vielha.', 3),
            ('Baqueira Beret', 'C-28', 'final_access', NULL, NULL, 'Tramo Vielha - Baqueira.', 1),

            -- GRANDVALIRA
            ('Grandvalira', 'C-14', 'approach', 119.000, 178.000, 'Eje del Segre: Ponts - Oliana - Adrall.', 3),
            ('Grandvalira', 'N-260', 'approach', 227.600, 234.000, 'Tramo de conexión hacia La Seu d''Urgell.', 3),
            ('Grandvalira', 'N-145', 'primary', 0.000, 9.000, 'Tramo La Seu d''Urgell - frontera de Andorra.', 2),
            ('Grandvalira', 'CG-1', 'primary', NULL, NULL, 'Acceso principal en Andorra.', 2),
            ('Grandvalira', 'CG-2', 'final_access', NULL, NULL, 'Eje Encamp - Canillo - Soldeu - Pas de la Casa.', 1),

            -- VALDELINARES
            ('Valdelinares', 'A-228', 'primary', 19.000, 34.000, 'Tramo Mora de Rubielos - Alcalá de la Selva - Valdelinares.', 2),
            ('Valdelinares', 'VF-TE-01', 'final_access', 0.000, 8.000, 'Acceso final a Valdelinares.', 1)
    ) AS t(
        resort_name,
        road_code,
        access_role,
        from_km,
        to_km,
        segment_description,
        priority
    )
)
INSERT INTO resort_access_roads (
    resort_id,
    road_id,
    access_role,
    segment_description,
    from_km,
    to_km,
    priority,
    is_active,
    data_source,
    is_verified
)
SELECT
    sr.id,
    r.id,
    ad.access_role,
    ad.segment_description,
    ad.from_km,
    ad.to_km,
    ad.priority,
    TRUE,
    'manual',
    TRUE
FROM access_data ad
JOIN ski_resorts sr
    ON sr.name = ad.resort_name
JOIN roads r
    ON r.code = ad.road_code
   AND r.data_source = 'manual'
WHERE NOT EXISTS (
    SELECT 1
    FROM resort_access_roads rar
    WHERE rar.resort_id = sr.id
      AND rar.road_id = r.id
      AND rar.access_role = ad.access_role
      AND (
            rar.from_km = ad.from_km
            OR (rar.from_km IS NULL AND ad.from_km IS NULL)
      )
      AND (
            rar.to_km = ad.to_km
            OR (rar.to_km IS NULL AND ad.to_km IS NULL)
      )
);


 
-- 4. RUTAS PRINCIPALES DESDE ZARAGOZA
 

INSERT INTO access_routes (
    resort_id,
    name,
    origin_label,
    route_type,
    description,
    route,
    is_active,
    data_source,
    is_verified
)
SELECT
    sr.id,
    route_data.name,
    'Zaragoza',
    'primary',
    route_data.description,
    NULL,
    TRUE,
    'manual',
    TRUE
FROM ski_resorts sr
JOIN (
    VALUES
        ('Astún', 'Zaragoza: Astún', 'Ruta principal desde Zaragoza hacia Astún por Monrepós, Jaca y Canfranc.'),
        ('Candanchú', 'Zaragoza: Candanchú', 'Ruta principal desde Zaragoza hacia Candanchú por Monrepós, Jaca y Canfranc.'),
        ('Formigal', 'Zaragoza: Formigal', 'Ruta principal desde Zaragoza hacia Formigal por Monrepós, Sabiñánigo, Biescas y A-136.'),
        ('Panticosa', 'Zaragoza: Panticosa', 'Ruta principal desde Zaragoza hacia Panticosa por Monrepós, Sabiñánigo, Biescas, A-136 y A-2606.'),
        ('Cerler', 'Zaragoza: Cerler', 'Ruta principal desde Zaragoza hacia Cerler por Barbastro, Graus, Campo, Benasque y A-2617.'),
        ('Baqueira Beret', 'Zaragoza: Baqueira Beret', 'Ruta principal desde Zaragoza hacia Baqueira Beret por N-230, Túnel de Vielha y C-28.'),
        ('Grandvalira', 'Zaragoza: Grandvalira', 'Ruta principal desde Zaragoza hacia Grandvalira por C-14, N-260, N-145, CG-1 y CG-2.'),
        ('Valdelinares', 'Zaragoza: Valdelinares', 'Ruta principal desde Zaragoza hacia Valdelinares por A-228 y VF-TE-01.')
) AS route_data(resort_name, name, description)
    ON sr.name = route_data.resort_name
ON CONFLICT (resort_id, origin_label, route_type, name)
DO UPDATE SET
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    data_source = EXCLUDED.data_source,
    is_verified = EXCLUDED.is_verified,
    updated_at = CURRENT_TIMESTAMP;


 
-- 5. SEGMENTOS ORDENADOS DE LAS RUTAS
-- Reutilizan resort_access_roads para evitar duplicar km.


WITH segment_data AS (
    SELECT *
    FROM (
        VALUES
            -- ASTÚN
            ('Zaragoza: Astún', 'Astún', 'A-23', 1, 'approach', 356.000, 394.000),
            ('Zaragoza: Astún', 'Astún', 'N-330', 2, 'primary', 614.000, 666.000),
            ('Zaragoza: Astún', 'Astún', 'N-330A', 3, 'final_access', NULL, NULL),
            ('Zaragoza: Astún', 'Astún', 'SC-22130-09', 4, 'final_access', NULL, NULL),

            -- CANDANCHÚ
            ('Zaragoza: Candanchú', 'Candanchú', 'A-23', 1, 'approach', 356.000, 394.000),
            ('Zaragoza: Candanchú', 'Candanchú', 'N-330', 2, 'primary', 614.000, 666.000),
            ('Zaragoza: Candanchú', 'Candanchú', 'N-330A', 3, 'final_access', NULL, NULL),

            -- FORMIGAL
            ('Zaragoza: Formigal', 'Formigal', 'A-23', 1, 'approach', 356.000, 394.000),
            ('Zaragoza: Formigal', 'Formigal', 'N-330', 2, 'approach', 614.000, 633.000),
            ('Zaragoza: Formigal', 'Formigal', 'N-260A', 3, 'approach', 509.000, 517.000),
            ('Zaragoza: Formigal', 'Formigal', 'A-136', 4, 'final_access', 0.000, 27.000),

            -- PANTICOSA
            ('Zaragoza: Panticosa', 'Panticosa', 'A-23', 1, 'approach', 356.000, 394.000),
            ('Zaragoza: Panticosa', 'Panticosa', 'N-330', 2, 'approach', 614.000, 633.000),
            ('Zaragoza: Panticosa', 'Panticosa', 'N-260A', 3, 'approach', 509.000, 517.000),
            ('Zaragoza: Panticosa', 'Panticosa', 'A-136', 4, 'primary', 0.000, 27.000),
            ('Zaragoza: Panticosa', 'Panticosa', 'A-2606', 5, 'final_access', 0.000, 4.500),

            -- CERLER
            ('Zaragoza: Cerler', 'Cerler', 'N-123', 1, 'approach', 0.000, 30.000),
            ('Zaragoza: Cerler', 'Cerler', 'N-123A', 2, 'approach', 0.000, 30.000),
            ('Zaragoza: Cerler', 'Cerler', 'A-139', 3, 'primary', 0.000, 63.000),
            ('Zaragoza: Cerler', 'Cerler', 'A-2617', 4, 'final_access', 0.000, 4.000),

            -- BAQUEIRA BERET
            ('Zaragoza: Baqueira Beret', 'Baqueira Beret', 'N-230', 1, 'approach', 70.000, 165.000),
            ('Zaragoza: Baqueira Beret', 'Baqueira Beret', 'C-28', 2, 'final_access', NULL, NULL),

            -- GRANDVALIRA
            ('Zaragoza: Grandvalira', 'Grandvalira', 'C-14', 1, 'approach', 119.000, 178.000),
            ('Zaragoza: Grandvalira', 'Grandvalira', 'N-260', 2, 'approach', 227.600, 234.000),
            ('Zaragoza: Grandvalira', 'Grandvalira', 'N-145', 3, 'primary', 0.000, 9.000),
            ('Zaragoza: Grandvalira', 'Grandvalira', 'CG-1', 4, 'primary', NULL, NULL),
            ('Zaragoza: Grandvalira', 'Grandvalira', 'CG-2', 5, 'final_access', NULL, NULL),

            -- VALDELINARES
            ('Zaragoza: Valdelinares', 'Valdelinares', 'A-228', 1, 'primary', 19.000, 34.000),
            ('Zaragoza: Valdelinares', 'Valdelinares', 'VF-TE-01', 2, 'final_access', 0.000, 8.000)
    ) AS t(
        route_name,
        resort_name,
        road_code,
        segment_order,
        access_role,
        from_km,
        to_km
    )
)
INSERT INTO access_route_segments (
    access_route_id,
    resort_access_road_id,
    segment_order,
    is_active
)
SELECT
    ar.id,
    rar.id,
    sd.segment_order,
    TRUE
FROM segment_data sd
JOIN access_routes ar
    ON ar.name = sd.route_name
JOIN ski_resorts sr
    ON sr.name = sd.resort_name
JOIN roads r
    ON r.code = sd.road_code
   AND r.data_source = 'manual'
JOIN resort_access_roads rar
    ON rar.resort_id = sr.id
   AND rar.road_id = r.id
   AND rar.access_role = sd.access_role
   AND (
        rar.from_km = sd.from_km
        OR (rar.from_km IS NULL AND sd.from_km IS NULL)
   )
   AND (
        rar.to_km = sd.to_km
        OR (rar.to_km IS NULL AND sd.to_km IS NULL)
   )
ON CONFLICT (access_route_id, segment_order)
DO UPDATE SET
    resort_access_road_id = EXCLUDED.resort_access_road_id,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;


COMMIT;