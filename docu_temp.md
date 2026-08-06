# TrackSki - Guia del proyecto

## 1. Objetivo y estado actual

TrackSki centraliza informacion de estaciones de esqui:

- Ubicacion geografica.
- Estado de pistas, remontes y nieve.
- Meteorologia actual e historica.
- Carreteras de acceso y sus condiciones.

Actualmente existen:

- API REST con FastAPI.
- Base de datos PostgreSQL 16 con PostGIS.
- Frontend SSR con Next.js 15 y React 19.
- Listado y detalle de estaciones.
- Ingesta meteorologica manual desde Open-Meteo.
- Lectura de avisos oficiales AEMET.
- Modelo de carreteras, accesos por estacion, incidencias y alternativas.
- Despliegue automatico de `staging` y `main`.

Los datos de nieve, carreteras y parte de la meteorologia incluidos en el seed
son aproximados y solo sirven para desarrollo. Los datos reales se iran
incorporando mediante ingestas controladas antes de automatizar jobs.

## 2. Estructura

```text
backend/
  app/
    api/routes/          Endpoints FastAPI
    commands/            Comandos manuales
    core/                Configuracion
    db/                  Sesion SQLAlchemy
    repositories/        Consultas SQL
    schemas/             Modelos de respuesta
    services/            Logica de dominio
      services/weather/    Proveedores meteorologicos
  db/init/               Esquema y seed inicial
  tests/                 Pruebas del backend
frontend/
  app/                   Rutas y estilos Next.js
  lib/api.ts             Cliente interno de la API
deploy/traefik/          Traefik temporal
.github/workflows/       Despliegue automatico
```

## 3. Variables de entorno

Los archivos reales `.env`, `.env.local`, `.env.staging` y `.env.main` estan
ignorados por Git. Los archivos `*.example` contienen valores de referencia.

Variables de base de datos:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
DATABASE_URL=
```

Variables de servicios:

```env
API_PORT=3001
FRONTEND_CONTAINER_PORT=3000
INTERNAL_API_URL=
NEXT_PUBLIC_API_URL=
```

Variables de despliegue:

```env
APP_ENV=
APP_HOST=
TRAEFIK_BACKEND_MIDDLEWARES=
TRAEFIK_FRONTEND_MIDDLEWARES=
```

En local, el backend se ejecuta en el host y usa `localhost:5433`. Dentro de
Docker, backend y frontend se comunican por nombre de servicio:

```env
DB_HOST=db
DB_PORT=5432
INTERNAL_API_URL=http://backend:3001
```

`DB_PASSWORD` y la contraseña incluida en `DATABASE_URL` deben coincidir. Si
la contraseña contiene caracteres reservados de URL, deben codificarse.

## 4. Desarrollo local

### 4.1 Preparar el entorno

Desde la raiz:

```powershell
Copy-Item .env.local.example .env.local
Copy-Item .env.local.example .env
```

`.env.local` configura Docker Compose y `.env` es leido por el backend cuando
se ejecuta desde el host.

### 4.2 Base de datos

El Compose local tiene el nombre fijo `trackski_local` y solo levanta la DB:

```bash
docker compose --env-file .env.local -f docker-compose.local.yml up -d
```

Recursos esperados:

```text
trackski_local-db-1
trackski_local_postgres_data_local
trackski_local_default
```

La DB queda accesible solo desde el equipo local:

```text
Host: 127.0.0.1
Port: 5433
```

Parar la DB:

```bash
docker compose --env-file .env.local -f docker-compose.local.yml down
```

### 4.3 Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

URLs:

```text
http://localhost:3001
http://localhost:3001/health
http://localhost:3001/health/db
http://localhost:3001/docs
```

### 4.4 Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Abrir:

```text
http://localhost:3000
http://localhost:3000/resorts/1
```

El renderizado es SSR. En local, `INTERNAL_API_URL` debe apuntar a
`http://localhost:3001`.

## 5. Base de datos y datos iniciales

`backend/db/init/01_schema.sql` crea las tablas, restricciones e indices.
`backend/db/init/02_seed_dev.sql` inserta datos de prueba.

PostgreSQL solo ejecuta `/docker-entrypoint-initdb.d` cuando el volumen esta
vacio. Cambiar el SQL o las credenciales del `.env` no modifica una DB ya
inicializada.

Para recrear la DB local:

```bash
docker compose --env-file .env.local -f docker-compose.local.yml down -v
docker compose --env-file .env.local -f docker-compose.local.yml up -d
```

Este comando elimina todos los datos locales.

Importante: el Compose de despliegue monta actualmente el mismo directorio
`backend/db/init`, por lo que una DB nueva de staging o main tambien recibe el
seed de desarrollo. Debe separarse antes de usar datos reales en produccion.

## 6. Endpoints

En local se usan directamente. Detras de Traefik se antepone `/api`.

```text
GET /health
GET /health/db
GET /resorts
GET /resorts/{id}
GET /resorts/{id}/summary
GET /resorts/{id}/snow-reports
GET /resorts/{id}/snow-reports/latest
GET /resorts/{id}/weather
GET /resorts/{id}/weather/latest
GET /resorts/{id}/roads
GET /resorts/{id}/access-status
GET /roads
GET /roads/incidents/active
GET /roads/{id}/conditions/latest
```

Los historicos de nieve y meteorologia aceptan `limit`, entre 1 y 100:

```text
GET /resorts/1/weather?limit=20
```

El frontend utiliza:

```text
GET /resorts
GET /resorts/{id}/summary
```

## 7. Carreteras y accesos

El modelo separa carretera, acceso e incidencia para evitar duplicar la misma
carretera en varias estaciones:

- `roads`: carretera unica, por ejemplo `A-395` o `C-28`.
- `resort_access_roads`: relacion entre estacion y carretera, con tramo,
  prioridad y rol del acceso.
- `road_conditions`: estado resumido de una carretera.
- `road_incidents`: cortes, restricciones, obras o incidencias activas.
- `road_alternatives`: rutas alternativas configuradas manualmente.

El endpoint principal para una estacion es:

```text
GET /resorts/{id}/access-status
```

Devuelve:

- Estado global del acceso: `open`, `caution`, `affected`, `chains`, `closed`
  o `unknown`.
- Carreteras de acceso de la estacion.
- Incidencias activas que afectan a esas carreteras.
- Alternativas disponibles.

La relacion entre una incidencia y una estacion se calcula asi:

- Debe coincidir la carretera.
- Si hay kilometros informados en el acceso y en la incidencia, los tramos
  deben solaparse.
- Si faltan kilometros, se considera relevante por carretera y se deja visible
  para revisar.

La seed de desarrollo incluye accesos iniciales para estaciones de Aragon. No
solo se modelan carreteras finales a estacion: tambien se incluyen carreteras
de aproximacion como `A-23` y `N-260`, porque pueden condicionar la subida
desde origenes habituales como Zaragoza o Huesca.

No se inventan PK. Si no hay kilometros verificados, `from_km` y `to_km`
quedan vacios. Las geometria de carreteras en la seed son aproximadas y no
verificadas.

Importar incidencias DGT DATEX2:

```bash
cd backend
python -m app.jobs.import_dgt_datex2_incidents
```

El importador:

- Descarga DGT DATEX2 v3.7.
- Normaliza incidencias.
- Guarda en `road_incidents`.
- Enlaza con `roads` por `road_code`.
- Actualiza `road_conditions` con un resumen por carretera.
- No expone `raw_payload` en endpoints publicos.
- No fuerza una carretera como `open` si DGT no informa incidencias.

Consultar:

```text
GET /roads
GET /roads/incidents/active
GET /roads/incidents/active?road_code=A-23
GET /roads/incidents/active?severity=high
GET /resorts/{id}/access-status
```

DGT DATEX2 no cubre Cataluna ni Pais Vasco. Esas fuentes quedan para una fase
posterior junto con la ejecucion periodica del importador.

## 8. Ingesta con Open-Meteo

Open-Meteo se consulta usando las coordenadas de cada estacion. Se normalizan:

- Temperatura.
- Precipitacion.
- Velocidad y direccion del viento.
- Visibilidad.
- Codigo meteorologico WMO.

Los registros se guardan con:

```text
data_source = open-meteo
is_verified = false
```

Importar todas las estaciones desde el backend local:

```bash
cd backend
python -m app.commands.ingest_weather
```

Importar una estacion:

```bash
python -m app.commands.ingest_weather --resort-id 1
```

Dentro del backend de staging:

```bash
docker compose --env-file .env -p trackski_staging exec backend \
  python -m app.commands.ingest_weather
```

La insercion evita duplicados para la misma estacion, fuente y fecha de
observacion. El comando no esta programado todavia.

Ejecutar las pruebas del proveedor:

```bash
cd backend
python -m unittest discover -s tests -v
```

## 9. AEMET

AEMET se usa como fuente oficial espanola, especialmente para avisos de riesgo
por nieve, viento, lluvia o temperaturas. Requiere configurar:

```env
AEMET_API_KEY=
```

Actualmente se puede ingerir avisos por areas concretas:

```bash
cd backend
python -m app.commands.ingest_alerts --area 62
```

Tambien se puede omitir `--area` para que el comando derive las areas AEMET
unicas a partir de las estaciones configuradas:

```bash
python -m app.commands.ingest_alerts
```

Areas utiles como referencia:

```text
61 Andalucia
62 Aragon
69 Catalonia
```

No se debe marcar un dato como verificado solo porque AEMET y Open-Meteo
devuelvan valores parecidos. La validacion debera considerar:

- Distancia a la estacion AEMET.
- Diferencia de altitud.
- Diferencia temporal.
- Tolerancia por variable meteorologica.

Ambas fuentes deben conservarse por separado.

La ingesta automatica de AEMET tambien queda pendiente para una fase posterior,
junto con el resto de jobs.

## 10. Jobs manuales de datos reales

TrackSki tiene un job agrupador para refrescar datos reales sin automatizarlos
todavia:

```bash
cd backend
python -m app.jobs.refresh_real_data --all
```

Tambien se puede ejecutar por partes:

```bash
python -m app.jobs.refresh_real_data --weather
python -m app.jobs.refresh_real_data --alerts
python -m app.jobs.refresh_real_data --alerts --area 62 --area 61
python -m app.jobs.refresh_real_data --roads
```

Si no se pasa `--area` al ejecutar alertas, el job calcula las areas AEMET
unicas desde las estaciones configuradas y hace una peticion por area, no por
estacion:

```bash
python -m app.jobs.refresh_real_data --alerts
python -m app.jobs.refresh_real_data --all
```

Si no se pasa ningun flag, el job no ejecuta nada y muestra un error claro. Se
hace asi para evitar refrescos completos por accidente.

Importante: ejecutar varias lineas seguidas en PowerShell lanza varios jobs uno
detras de otro. Para una prueba normal, ejecutar solo un comando cada vez:

```bash
python -m app.jobs.refresh_real_data --weather
```

El agrupador no duplica la logica de ingesta: reutiliza los comandos y jobs ya
existentes:

- Open-Meteo: `app.commands.ingest_weather`
- AEMET: `app.commands.ingest_alerts`
- DGT DATEX2: `app.jobs.import_dgt_datex2_incidents`

Cada fuente devuelve un resumen:

- `processed`: datos leidos desde la fuente.
- `inserted`: registros insertados solo cuando se puede saber con seguridad.
- `updated`: resumenes actualizados, por ejemplo `road_conditions`.
- `saved`: registros guardados mediante upsert; pueden ser nuevos o existentes.
- `skipped`: datos omitidos por no ser relevantes o estar repetidos.
- `status`: `success`, `partial` o `failed`.

Si una fuente falla, el agrupador marca esa fuente como `failed` y continua con
las demas siempre que sea posible.

Comandos existentes que siguen funcionando:

```bash
python -m app.commands.ingest_weather
python -m app.commands.ingest_weather --resort-id 1
python -m app.commands.ingest_alerts --area 62
python -m app.jobs.import_dgt_datex2_incidents
```

Comportamiento por fuente:

- Open-Meteo hace una peticion por estacion porque necesita coordenadas.
- AEMET hace una peticion por area AEMET unica, no por estacion.
- DGT hace una peticion global al XML DATEX2 y filtra localmente por carreteras
  configuradas en `roads`.

Datos actualizados:

- `weather_reports` con Open-Meteo.
- `weather_alerts` con AEMET.
- `road_incidents` y `road_conditions` con DGT DATEX2.

Variables necesarias:

```env
AEMET_API_KEY=
DGT_DATEX2_URL=
DGT_DATEX2_TIMEOUT_SECONDS=
```

Limitaciones actuales:

- No hay cron, systemd timer, Celery ni APScheduler.
- AEMET resuelve areas desde regiones conocidas de estaciones.
- Mas adelante habra que mejorar esa relacion estacion-area AEMET con datos
  reales y no solo por region.
- DGT solo guarda incidencias de carreteras configuradas en `roads`.

## 11. Arquitectura de despliegue

Nginx mantiene los puertos `80/443` para otras aplicaciones del SERVER.
TrackSki usa temporalmente Traefik en `8088`.

```text
LAN
  |
  | :8088
  v
Traefik
  +-- Host de TrackSki ----------> frontend SSR :3000
  +-- Host + PathPrefix(/api) ---> backend :3001
                                      |
                                      v
                                  PostgreSQL
```

Seguridad de red:

- Traefik publica `8088:80`.
- Frontend y backend usan `expose`, no `ports`.
- DB no publica puertos.
- DB solo pertenece a la red interna.
- Frontend y backend pertenecen a `internal` y `proxy`.
- `exposedByDefault=false`.
- Staging y el dashboard usan `IPAllowList` de la LAN.

## 12. Traefik temporal

Crear la red externa una vez:

```bash
docker network inspect proxy >/dev/null 2>&1 || docker network create proxy
```

Revisar en `deploy/traefik/docker-compose.traefik.yml` que el rango de
`lan-only` coincida con la LAN del servidor.

Levantar Traefik:

```bash
docker compose -f deploy/traefik/docker-compose.traefik.yml up -d
```

URLs:

```text
http://traefik.local:8088
http://staging.miapp.local:8088
http://staging.miapp.local:8088/api/health
```

En el archivo `hosts` del equipo cliente:

```text
IP_DEL_SERVER traefik.local
IP_DEL_SERVER staging.miapp.local
```

## 13. Staging y main

Rutas utilizadas por GitHub Actions:

```text
/home/pablo/proyectos/trackski/staging
/home/pablo/proyectos/trackski/main
```

Preparar staging:

```bash
mkdir -p /home/pablo/proyectos/trackski/staging
cd /home/pablo/proyectos/trackski/staging
git clone <repo-url> .
git checkout staging
cp .env.staging.example .env
```

Preparar main:

```bash
mkdir -p /home/pablo/proyectos/trackski/main
cd /home/pablo/proyectos/trackski/main
git clone <repo-url> .
git checkout main
cp .env.main.example .env
```

Editar cada `.env` con credenciales reales. Levantar manualmente:

```bash
docker compose --env-file .env -p trackski_staging up -d --build
docker compose --env-file .env -p trackski_main up -d --build
```

No ejecutar ambos comandos desde la misma carpeta.

## 14. Despliegue automatico

`.github/workflows/deploy.yml` se ejecuta al hacer push:

- `staging` despliega `trackski_staging`.
- `main` despliega `trackski_main`.

Secretos requeridos en GitHub:

```text
SERVER_HOST
SERVER_USER
SERVER_PORT
SERVER_SSH_KEY
```

El workflow:

1. Accede al SERVER mediante SSH.
2. Actualiza la rama correspondiente.
3. Crea la red `proxy` si no existe.
4. reconstruye y levanta los servicios.
5. Elimina imagenes Docker sin uso.

No modifica ni reinicia Nginx.

## 15. Comprobaciones

Estado:

```bash
docker compose --env-file .env -p trackski_staging ps
```

Logs:

```bash
docker compose --env-file .env -p trackski_staging logs --tail=100
docker compose --env-file .env -p trackski_staging logs --tail=100 backend
docker compose --env-file .env -p trackski_staging logs --tail=100 frontend
```

Comunicación frontend-backend:

```bash
docker compose --env-file .env -p trackski_staging exec frontend \
  node -e "fetch('http://backend:3001/resorts').then(async r => console.log(r.status, await r.text())).catch(console.error)"
```

Datos de estaciones:

```bash
docker compose --env-file .env -p trackski_staging exec db \
  sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, name FROM ski_resorts;"'
```

Puertos expuestos:

```bash
sudo ss -tulpn | grep -E '3000|3001|5432|8088'
```

Debe aparecer `8088`. No deben publicarse `3000`, `3001` ni `5432`.

## 16. Problemas habituales

### Error de autenticacion PostgreSQL

Las variables `POSTGRES_*` solo crean el usuario y contraseña cuando se
inicializa un volumen vacio. Si se cambia `DB_PASSWORD`, la DB conserva la
contraseña anterior.

En un entorno con datos descartables:

```bash
docker compose --env-file .env -p trackski_staging down
docker volume rm trackski_staging_postgres_data
docker compose --env-file .env -p trackski_staging up -d --build
```

No ejecutar este procedimiento si existen datos que deban conservarse.

### El frontend carga, pero no muestra estaciones

Comprobar:

1. `http://staging.miapp.local:8088/api/resorts`.
2. Logs del backend.
3. Peticion interna desde el frontend.
4. Contenido de `ski_resorts`.

### Los cambios SQL no aparecen

Los scripts de inicializacion no son migraciones. Solo se ejecutan al crear el
volumen. Mientras no se incorpore Alembic, los cambios deben aplicarse
manualmente o recreando una DB descartable.

## 17. Migracion futura a 80/443

No realizarla todavia.

Cuando TrackSki este validado:

1. Migrar las aplicaciones existentes de Nginx.
2. Liberar `80/443`.
3. Configurar entrypoints HTTP y HTTPS en Traefik.
4. Configurar certificados.
5. Validar todos los routers.
6. Retirar Nginx cuando no queden dependencias.
