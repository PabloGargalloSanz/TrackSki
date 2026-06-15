import Link from "next/link";

import { getResorts, type Resort } from "../lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  let resorts: Resort[] = [];
  let hasError = false;

  try {
    resorts = await getResorts();
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
          {resorts.map((resort) => (
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

                <dl className="coordinates">
                  <div>
                    <dt>Latitud</dt>
                    <dd>{resort.location.latitude.toFixed(4)}</dd>
                  </div>
                  <div>
                    <dt>Longitud</dt>
                    <dd>{resort.location.longitude.toFixed(4)}</dd>
                  </div>
                </dl>
              </article>
            </Link>
          ))}
        </section>
      )}
    </main>
  );
}
