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

function accessStatusLabel(status: string | null | undefined): string {
  if (!status) {
    return "Sin datos";
  }

  return accessStatusLabels[status] ?? status;
}

function skiableKm(summary: ResortSummary | null): string {
  const snow = summary?.latest_snow_report;
  if (!snow) {
    return "Sin datos";
  }

  return `${snow.open_km}/${snow.total_km} km`;
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
            const accessStatus = summary?.access_status.overall_status ?? null;

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
                          className={`status-chip status-chip--${
                            accessStatus ?? "unknown"
                          }`}
                        >
                          {accessStatusLabel(accessStatus)}
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
