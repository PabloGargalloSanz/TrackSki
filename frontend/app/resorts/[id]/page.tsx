import Link from "next/link";
import { notFound } from "next/navigation";

import { getResortSummary } from "../../../lib/api";

export const dynamic = "force-dynamic";

type ResortDetailPageProps = {
  params: Promise<{ id: string }>;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Madrid",
  }).format(new Date(value));
}

function valueOrDash(value: number | string | null, suffix = ""): string {
  return value === null ? "-" : `${value}${suffix}`;
}

export default async function ResortDetailPage({
  params,
}: ResortDetailPageProps) {
  const { id } = await params;
  const resortId = Number(id);

  if (!Number.isInteger(resortId) || resortId <= 0) {
    notFound();
  }

  let summary;

  try {
    summary = await getResortSummary(resortId);
  } catch (error) {
    console.error(`No se pudo cargar el resumen de la estacion ${id}:`, error);

    return (
      <main className="page">
        <Link className="back-link" href="/">
          Volver a estaciones
        </Link>
        <section className="status-panel" role="alert">
          <h1>No se pudo cargar la estacion</h1>
          <p>Comprueba que la API este disponible e intentalo de nuevo.</p>
        </section>
      </main>
    );
  }

  if (!summary) {
    notFound();
  }

  const { resort, latest_snow_report: snow, latest_weather_report: weather } =
    summary;

  return (
    <main className="page">
      <Link className="back-link" href="/">
        Volver a estaciones
      </Link>

      <header className="detail-header">
        <div>
          <p className="eyebrow">TrackSki</p>
          <h1>{resort.name}</h1>
          <p className="lead">
            {resort.region ? `${resort.region}, ` : ""}
            {resort.country}
          </p>
        </div>
        <span
          className={
            resort.is_verified
              ? "data-badge data-badge--verified"
              : "data-badge"
          }
        >
          {resort.is_verified ? "Verificado" : "Datos de prueba"}
        </span>
      </header>

      <div className="detail-grid">
        <section className="detail-section">
          <div className="section-heading">
            <h2>Nieve y pistas</h2>
            {snow && <time>{formatDate(snow.reported_at)}</time>}
          </div>
          {snow ? (
            <>
              <dl className="metric-grid">
                <div>
                  <dt>Remontes</dt>
                  <dd>
                    {snow.open_lifts} / {snow.total_lifts}
                  </dd>
                </div>
                <div>
                  <dt>Kilometros abiertos</dt>
                  <dd>
                    {snow.open_km} / {snow.total_km} km
                  </dd>
                </div>
                <div>
                  <dt>Espesor minimo</dt>
                  <dd>{valueOrDash(snow.snow_depth_min_cm, " cm")}</dd>
                </div>
                <div>
                  <dt>Espesor maximo</dt>
                  <dd>{valueOrDash(snow.snow_depth_max_cm, " cm")}</dd>
                </div>
                <div>
                  <dt>Riesgo de aludes</dt>
                  <dd>{valueOrDash(snow.avalanche_risk, " / 5")}</dd>
                </div>
                <div>
                  <dt>Acceso</dt>
                  <dd>{snow.access_status ?? "-"}</dd>
                </div>
              </dl>
              <dl className="trail-grid">
                <div>
                  <dt>Verdes</dt>
                  <dd>{snow.green_trails.open} / {snow.green_trails.total}</dd>
                </div>
                <div>
                  <dt>Azules</dt>
                  <dd>{snow.blue_trails.open} / {snow.blue_trails.total}</dd>
                </div>
                <div>
                  <dt>Rojas</dt>
                  <dd>{snow.red_trails.open} / {snow.red_trails.total}</dd>
                </div>
                <div>
                  <dt>Negras</dt>
                  <dd>{snow.black_trails.open} / {snow.black_trails.total}</dd>
                </div>
              </dl>
            </>
          ) : (
            <p className="empty-message">No hay partes de nieve disponibles.</p>
          )}
        </section>

        <section className="detail-section">
          <div className="section-heading">
            <h2>Meteorologia</h2>
            {weather && <time>{formatDate(weather.reported_at)}</time>}
          </div>
          {weather ? (
            <dl className="metric-grid">
              <div>
                <dt>Estado</dt>
                <dd>{weather.weather ?? "-"}</dd>
              </div>
              <div>
                <dt>Temperatura</dt>
                <dd>{valueOrDash(weather.temperature_celsius, " °C")}</dd>
              </div>
              <div>
                <dt>Viento</dt>
                <dd>{valueOrDash(weather.wind_speed_kmh, " km/h")}</dd>
              </div>
              <div>
                <dt>Direccion</dt>
                <dd>{weather.wind_direction ?? "-"}</dd>
              </div>
              <div>
                <dt>Precipitacion</dt>
                <dd>{valueOrDash(weather.precipitation_mm, " mm")}</dd>
              </div>
              <div>
                <dt>Visibilidad</dt>
                <dd>{valueOrDash(weather.visibility_m, " m")}</dd>
              </div>
            </dl>
          ) : (
            <p className="empty-message">
              No hay datos meteorologicos disponibles.
            </p>
          )}
        </section>
      </div>

      <section className="detail-section roads-section">
        <div className="section-heading">
          <h2>Accesos por carretera</h2>
        </div>
        {summary.roads.length > 0 ? (
          <div className="road-list">
            {summary.roads.map((road) => (
              <article className="road-row" key={road.id}>
                <div>
                  <h3>{road.name ?? road.code}</h3>
                  <p>{road.latest_condition?.details ?? "Sin observaciones"}</p>
                </div>
                <div className="road-status">
                  <strong>{road.latest_condition?.status ?? "Sin datos"}</strong>
                  {road.latest_condition && (
                    <time>{formatDate(road.latest_condition.reported_at)}</time>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty-message">
            No hay carreteras asociadas a esta estacion.
          </p>
        )}
      </section>
    </main>
  );
}
