const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">TrackSki</p>
        <h1>Estado de nieve, meteo y accesos desde una sola vista.</h1>
        <p className="lead">
          Frontend SSR con Next.js preparado para consumir la API en{" "}
          <code>{apiUrl}</code>.
        </p>
        <a className="button" href={`${apiUrl}/health`}>
          Comprobar API
        </a>
      </section>
    </main>
  );
}
