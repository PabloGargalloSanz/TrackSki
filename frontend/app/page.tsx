import Link from "next/link";

import {
  getResortSummary,
  getResorts,
  type Resort,
  type ResortSummary,
} from "../lib/api";

export const dynamic = "force-dynamic";

const accessStatusLabels: Record<string, string> = {
  open: "Abierto",
  caution: "Precaucion",
  affected: "Peligro",
  chains: "Peligro",
  closed: "Cerrado",
  unknown: "Sin datos",
};

const incidentAccessLabels: Record<string, string> = {
  road_closed: "Cerrado",
  chains_required: "Cadenas",
  snow: "Nieve",
  ice: "Hielo",
  hail: "Granizo",
  roadworks: "Obras",
  obstruction: "Obstaculo",
  accident: "Accidente",
  restriction: "Restriccion",
  congestion: "Retencion",
  weather: "Meteo",
};

const incidentAccessTones: Record<string, string> = {
  road_closed: "closed",
  chains_required: "danger",
  snow: "danger",
  ice: "danger",
  hail: "danger",
  roadworks: "roadworks",
  obstruction: "warning",
  accident: "danger",
  restriction: "warning",
  congestion: "warning",
  weather: "warning",
};

const incidentTypePriority = [
  "road_closed",
  "chains_required",
  "snow",
  "ice",
  "hail",
  "accident",
  "restriction",
  "obstruction",
  "congestion",
  "weather",
  "roadworks",
];

function mainAccessIncidentType(summary: ResortSummary | null): string | null {
  const incidents = summary?.access_status.incidents ?? [];

  return (
    incidentTypePriority.find((incidentType) =>
      incidents.some((incident) => incident.incident_type === incidentType),
    ) ?? null
  );
}

function accessStatusLabel(summary: ResortSummary | null): string {
  const status = summary?.access_status.overall_status;
  if (!status) {
    return "Sin datos";
  }

  const incidentType = mainAccessIncidentType(summary);
  if (incidentType) {
    return incidentAccessLabels[incidentType] ?? accessStatusLabels[status] ?? status;
  }

  return accessStatusLabels[status] ?? status;
}

function accessStatusTone(summary: ResortSummary | null): string {
  const status = summary?.access_status.overall_status;
  if (!status) {
    return "unknown";
  }

  const incidentType = mainAccessIncidentType(summary);
  if (incidentType) {
    return incidentAccessTones[incidentType] ?? status;
  }

  return status;
}

function skiableKm(summary: ResortSummary | null): string {
  const snow = summary?.latest_snow_report;
  if (!snow) {
    return "0 / 0 km";
  }

  return `${snow.open_km} / ${snow.total_km} km`;
}

export default async function Home() {
  let resorts: Resort[] = [];
  let summaries = new Map<number, ResortSummary | null>();
  let hasError = false;

  try {
    resorts = await getResorts();
    const summaryEntries = await Promise.all(
      resorts.map(async (resort) => {
        try {
          return [resort.id, await getResortSummary(resort.id)] as const;
        } catch (error) {
          console.error(
            `No se pudo cargar el resumen de la estacion ${resort.id}:`,
            error,
          );
          return [resort.id, null] as const;
        }
      }),
    );
    summaries = new Map(summaryEntries);
  } catch (error) {
    console.error("No se pudieron cargar las estaciones desde la API:", error);
    hasError = true;
  }

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">TrackSki</p>
          <h1>Estaciones</h1>
        </div>
        <p className="lead">
          Consulta el estado de nieve, meteorologia y accesos de cada estacion.
        </p>
      </header>

      {hasError ? (
        <section className="status-panel" role="alert">
          <h2>No se pudieron cargar las estaciones</h2>
          <p>Comprueba que la API este disponible e intentalo de nuevo.</p>
        </section>
      ) : resorts.length === 0 ? (
        <section className="status-panel">
          <h2>No hay estaciones disponibles</h2>
          <p>Las estaciones apareceran aqui cuando existan datos.</p>
        </section>
      ) : (
        <section className="resort-grid" aria-label="Listado de estaciones">
          {resorts.map((resort) => {
            const summary = summaries.get(resort.id) ?? null;
            const accessStatusToneValue = accessStatusTone(summary);

            return (
              <Link
                className="resort-card"
                href={`/resorts/${resort.id}`}
                key={resort.id}
              >
                <article>
                  <div className="resort-card__header">
                    <div>
                      <h2>{resort.name}</h2>
                      <p>
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
                  </div>

                  <dl className="resort-summary-grid">
                    <div>
                      <dt>Km esquiables</dt>
                      <dd>{skiableKm(summary)}</dd>
                    </div>
                    <div>
                      <dt>Accesos</dt>
                      <dd>
                        <span
                          className={`status-chip status-chip--${accessStatusToneValue}`}
                        >
                          {accessStatusLabel(summary)}
                        </span>
                      </dd>
                    </div>
                  </dl>
                </article>
              </Link>
            );
          })}
        </section>
      )}
    </main>
  );
}
