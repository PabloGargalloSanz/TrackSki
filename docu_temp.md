# TrackSki - Notas de despliegue

## 1. Arquitectura actual

El backend es una API con FastAPI en Python:

- Codigo principal: `backend/app`.
- Dependencias: `backend/requirements.txt`.
- Imagen Docker: `backend/Dockerfile`.
- Puerto interno de despliegue: `3001`, configurable con `API_PORT`.

El frontend es una aplicacion SSR con Next.js y React:

- Codigo: `frontend/app`.
- Dependencias: `frontend/package.json`.
- Gestor de paquetes: `pnpm`.
- Puerto interno: `3000`, configurable con `FRONTEND_CONTAINER_PORT`.

## 2. Arquitectura temporal con Traefik

El MP100 ya tiene Nginx sirviendo otras apps en los puertos `80` y `443`. Esa configuracion no se toca.

Para TrackSki se usa Traefik temporal:

- Nginx sigue usando `80/443`.
- Traefik escucha temporalmente en el puerto `8088` del host.
- Traefik enruta esta app usando Docker provider.
- Solo se publican contenedores con `traefik.enable=true`.
- La red compartida de Traefik se llama `proxy`.

```text
LAN
  |
  | http://staging.miapp.local:8088
  v
Traefik temporal
  |
  +-- frontend SSR Next.js
  |
  +-- /api -> backend FastAPI
             |
             v
           db PostgreSQL/PostGIS
```

La DB queda solo en la red interna del proyecto. No esta en la red `proxy`, no tiene labels de Traefik y no publica puertos al host en staging/main.

## 3. Desarrollo local

El desarrollo local no necesita Traefik.

Levantar solo la DB local:

```bash
cp .env.local.example .env.local
cp .env.local.example .env
docker compose --env-file .env.local -f docker-compose.local.yml up -d
```

Backend local:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Frontend local:

```bash
cd frontend
pnpm install
pnpm dev
```

URLs locales:

```text
http://localhost:3001
http://localhost:3001/health
http://localhost:3001/docs
http://localhost:3000
```

## 4. Preparar Traefik temporal

Crear la red externa:

```bash
docker network create proxy
```

Levantar Traefik:

```bash
docker compose -f deploy/traefik/docker-compose.traefik.yml up -d
```

Ver logs:

```bash
docker compose -f deploy/traefik/docker-compose.traefik.yml logs -f
```

Comprobar que escucha en `8088`:

```bash
sudo ss -tulpn | grep 8088
```

El dashboard queda en:

```text
http://traefik.local:8088
```

## 5. Preparar staging

```bash
sudo mkdir -p /opt/miapp/staging
sudo chown "$USER":"$USER" /opt/miapp/staging
cd /opt/miapp/staging
git clone <repo-url> .
git checkout staging
cp .env.staging.example .env
```

Edita `.env` con secretos reales del servidor.

Levantar staging:

```bash
docker compose --env-file .env -p miapp_staging up -d --build
```

## 6. Preparar main futuro

```bash
sudo mkdir -p /opt/miapp/main
sudo chown "$USER":"$USER" /opt/miapp/main
cd /opt/miapp/main
git clone <repo-url> .
git checkout main
cp .env.main.example .env
```

Edita `.env` con secretos reales de main.

Levantar main:

```bash
docker compose --env-file .env -p miapp_main up -d --build
```

## 7. Hosts para probar desde LAN

En el ordenador cliente, anade algo como:

```text
192.168.1.50 traefik.local
192.168.1.50 staging.miapp.local
```

Sustituye `192.168.1.50` por la IP real del MP100.

Para probar en el mismo ordenador donde corre Docker puedes usar:

```text
127.0.0.1 traefik.local
127.0.0.1 staging.miapp.local
```

## 8. Probar staging

Desde otro ordenador de la LAN:

```text
http://staging.miapp.local:8088
http://staging.miapp.local:8088/api/health
http://traefik.local:8088
```

Traefik aplica `StripPrefix` para que:

```text
/api/health
```

llegue al backend como:

```text
/health
```

## 9. Comprobar exposicion de puertos

En el MP100:

```bash
sudo ss -tulpn | grep -E '3000|3001|5432|8088'
```

Debe aparecer Traefik temporal:

```text
0.0.0.0:8088
```

No deberia aparecer:

```text
0.0.0.0:5432
0.0.0.0:3001
0.0.0.0:3000
```

## 10. Checklist de seguridad

- Nginx no se toca.
- Traefik temporal usa `8088:80`.
- Traefik usa Docker provider.
- Traefik usa `exposedByDefault=false`.
- Existe red externa `proxy`.
- Backend y frontend estan en `proxy`.
- DB no esta en `proxy`.
- DB no tiene labels de Traefik.
- Backend y frontend no usan `ports` en staging/main.
- DB no publica puertos en staging/main.
- Staging usa `Host(\`staging.miapp.local\`)`.
- Backend usa `Host(\`staging.miapp.local\`) && PathPrefix(\`/api\`)`.
- Frontend usa `Host(\`staging.miapp.local\`)`.
- Backend tiene prioridad mayor que frontend.
- Staging usa IPAllowList LAN.
- Dashboard Traefik usa IPAllowList LAN.
- `.env` reales estan en `.gitignore`.
- No hay secretos reales en archivos versionables.

## 11. Migracion futura a 80/443

No hacer esta migracion ahora.

Cuando TrackSki funcione bien y quieras sustituir Nginx:

1. Liberar `80/443`, parando Nginx o migrando app por app.
2. Cambiar Traefik de `8088:80` a `80:80`.
3. Anadir `443:443`.
4. Configurar certificados, por ejemplo con Let's Encrypt.
5. Migrar las otras apps con labels de Traefik.
6. Verificar todo antes de retirar configuraciones antiguas de Nginx.
