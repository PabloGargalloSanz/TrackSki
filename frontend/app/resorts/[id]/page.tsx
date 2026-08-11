import Link from "next/link";
import { notFound } from "next/navigation";

import {
  getResortSummary,
  type ResortAccessRoad,
  type RoadIncident,
} from "../../../lib/api";

export const dynamic = "force-dynamic";

type ResortDetailPageProps = {
  params: Promise<{ id: string }>;
};

const severityOrder = ["critical", "high", "medium", "low", "unknown"];

const severityLabels: Record<string, string> = {
  critical: "Criticas",
  high: "Altas",
  medium: "Medias",
  low: "Leves",
  unknown: "Sin clasificar",
};

const accessStatusLabels: Record<string, string> = {
  open: "Abierto",
  caution: "Precaucion",
  affected: "Peligro",
  chains: "Peligro",
  closed: "Cerrado",
  unknown: "Sin datos",
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

function kmRange(incident: RoadIncident): string {
  if (incident.start_km === null && incident.end_km === null) {
    return "Tramo sin km informado";
  }

  if (incident.start_km === incident.end_km || incident.end_km === null) {
    return `km ${incident.start_km}`;
  }

  return `km ${incident.start_km} - ${incident.end_km}`;
}

function incidentTitle(incident: RoadIncident): string {
  if (incident.incident_type === "roadworks") {
    return "Obras";
  }

  return incident.title ?? incident.incident_type;
}

function incidentDescription(incident: RoadIncident): string | null {
  if (incident.incident_type === "roadworks") {
    return null;
  }

  return incident.description ?? "Sin descripcion disponible";
}

function groupIncidentsBySeverity(incidents: RoadIncident[]) {
  return severityOrder
    .map((severity) => ({
      severity,
      label: severityLabels[severity],
      incidents: incidents.filter((incident) => incident.severity === severity),
    }))
    .filter((group) => group.incidents.length > 0);
}

function accessStatusLabel(status: string): string {
  return accessStatusLabels[status] ?? status;
}

function incidentsForRoad(
  road: ResortAccessRoad,
  incidents: RoadIncident[],
): RoadIncident[] {
  return incidents.filter((incident) => incident.road_id === road.road.id);
}

function roadAccessStatus(incidents: RoadIncident[]): {
  label: string;
  tone: string;
} {
  if (incidents.length === 0) {
    return { label: "Abierto", tone: "open" };
  }

  if (
    incidents.some(
      (incident) =>
        incident.incident_type === "road_closed" &&
        ["critical", "high"].includes(incident.severity),
    )
  ) {
    return { label: "Cerrado", tone: "closed" };
  }

  if (
    incidents.some((incident) => ["critical", "high"].includes(incident.severity))
  ) {
    return { label: "Peligro", tone: "danger" };
  }

  return { label: "Precaucion", tone: "warning" };
}

function accessProblemSummary(incidents: RoadIncident[]): string {
  if (incidents.length === 0) {
    return "";
  }

  const labels = incidents.map((incident) => incidentTypeLabel(incident));
  const uniqueLabels = Array.from(new Set(labels));

  return uniqueLabels.slice(0, 3).join(", ");
}

function incidentTypeLabel(incident: RoadIncident): string {
  const labels: Record<string, string> = {
    road_closed: "Corte de carretera",
    chains_required: "Cadenas",
    snow: "Nieve",
    ice: "Hielo",
    hail: "Granizo",
    roadworks: "Obras",
    accident: "Accidente",
    restriction: "Restriccion",
    congestion: "Retencion",
    obstruction: "Obstaculo",
    weather: "Meteorologia",
  };

  return labels[incident.incident_type] ?? incident.title ?? incident.incident_type;
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

  const {
    resort,
    latest_snow_report: snow,
    latest_weather_report: weather,
    weather_alerts: alerts,
    access_status: accessStatus,
  } = summary;
  const incidentGroups = groupIncidentsBySeverity(accessStatus.incidents);

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
            <>
              <dl className="metric-grid">
                <div>
                  <dt>Estado</dt>
                  <dd>{weather.weather ?? "-"}</dd>
                </div>
                <div>
                  <dt>Temperatura</dt>
                  <dd>{valueOrDash(weather.temperature_celsius, " C")}</dd>
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

              <div className="subsection">
                <div className="subsection-heading">
                  <h3>Avisos meteorologicos</h3>
                  <span>{alerts.length}</span>
                </div>
                {alerts.length > 0 ? (
                  <div className="compact-list">
                    {alerts.map((alert) => (
                      <article className="compact-row" key={alert.id}>
                        <div>
                          <div className="inline-heading">
                            <span
                              className={`severity-pill severity-pill--${alert.level}`}
                            >
                              {alert.level}
                            </span>
                            <h4>{alert.event}</h4>
                          </div>
                          <p>{alert.headline ?? alert.description ?? alert.area}</p>
                          <p className="meta-line">{alert.area}</p>
                        </div>
                        <div className="alert-validity">
                          {alert.onset && <time>Desde {formatDate(alert.onset)}</time>}
                          {alert.expires && (
                            <time>Hasta {formatDate(alert.expires)}</time>
                          )}
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="empty-message">
                    Sin avisos meteorologicos activos.
                  </p>
                )}
              </div>
            </>
          ) : (
            <p className="empty-message">
              No hay datos meteorologicos disponibles.
            </p>
          )}
        </section>
      </div>

      <div className="access-grid">
        <section className="detail-section roads-section">
          <div className="section-heading">
            <h2>Accesos por carretera</h2>
            <strong
              className={`status-chip status-chip--${accessStatus.overall_status}`}
            >
              {accessStatusLabel(accessStatus.overall_status)}
            </strong>
          </div>
          {accessStatus.roads.length > 0 ? (
            <div className="road-list">
              {accessStatus.roads.map((accessRoad) => {
                const roadIncidents = incidentsForRoad(
                  accessRoad,
                  accessStatus.incidents,
                );
                const status = roadAccessStatus(roadIncidents);
                const latestIncident = roadIncidents[0];
                const problemSummary = accessProblemSummary(roadIncidents);

                return (
                  <article className="road-row" key={accessRoad.id}>
                    <div>
                      <h3>{accessRoad.road.name ?? accessRoad.road.code}</h3>
                      {problemSummary && <p>{problemSummary}</p>}
                    </div>
                    <div className="road-status">
                      <strong className={`status-dot status-dot--${status.tone}`}>
                        {status.label}
                      </strong>
                      {latestIncident && (
                        <time>{formatDate(latestIncident.updated_at)}</time>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="empty-message">
              No hay carreteras asociadas a esta estacion.
            </p>
          )}

          {accessStatus.alternatives.length > 0 && (
            <div className="alternative-list">
              <h3>Alternativas</h3>
              {accessStatus.alternatives.map((alternative) => (
                <article className="alternative-row" key={alternative.id}>
                  <h4>{alternative.title}</h4>
                  <p>{alternative.description}</p>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="detail-section incidents-section">
          <div className="section-heading">
            <h2>Incidencias de carretera</h2>
            <span className="count-badge">{accessStatus.incidents.length}</span>
          </div>

          {incidentGroups.length > 0 ? (
            <div className="incident-group-list">
              {incidentGroups.map((group) => (
                <details
                  className="incident-group"
                  key={group.severity}
                  open={group.severity === "critical" || group.severity === "high"}
                >
                  <summary>
                    <span
                      className={`severity-pill severity-pill--${group.severity}`}
                    >
                      {group.severity}
                    </span>
                    <strong>{group.label}</strong>
                    <span>{group.incidents.length}</span>
                  </summary>
                  <div className="incident-list">
                    {group.incidents.map((incident) => (
                      <article className="incident-row" key={incident.id}>
                        <div>
                          <h4>{incidentTitle(incident)}</h4>
                          {incidentDescription(incident) && (
                            <p>{incidentDescription(incident)}</p>
                          )}
                          <p className="meta-line">
                            {incident.road_code ?? "Carretera sin codigo"} -{" "}
                            {kmRange(incident)}
                            {incident.access_role ? ` - ${incident.access_role}` : ""}
                          </p>
                        </div>
                        <div className="road-status">
                          <strong>{incident.status}</strong>
                          <time>{formatDate(incident.updated_at)}</time>
                        </div>
                      </article>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <p className="empty-message">Sin incidencias activas conocidas.</p>
          )}
        </section>
      </div>
    </main>
  );
}
