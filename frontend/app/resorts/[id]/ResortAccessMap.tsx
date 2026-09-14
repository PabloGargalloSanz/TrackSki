import type { ResortMap, RoadGeometry, RoadIncident } from "../../../lib/api";

type Bounds = {
  minLon: number;
  maxLon: number;
  minLat: number;
  maxLat: number;
};

type Point = [number, number];

function geometryLines(geometry: RoadGeometry | null): Point[][] {
  if (!geometry) {
    return [];
  }

  if (geometry.type === "LineString") {
    return [geometry.coordinates];
  }

  return geometry.coordinates;
}

function collectPoints(mapData: ResortMap): Point[] {
  const routePoints = mapData.roads.flatMap((accessRoad) =>
    geometryLines(accessRoad.road.route).flat(),
  );
  const incidentPoints = mapData.incidents
    .map((incident) => incident.location?.coordinates)
    .filter((point): point is Point => Boolean(point));

  return [
    [mapData.resort.location.longitude, mapData.resort.location.latitude],
    ...routePoints,
    ...incidentPoints,
  ];
}

function boundsFor(points: Point[]): Bounds {
  const longitudes = points.map(([longitude]) => longitude);
  const latitudes = points.map(([, latitude]) => latitude);
  const minLon = Math.min(...longitudes);
  const maxLon = Math.max(...longitudes);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const lonPadding = Math.max((maxLon - minLon) * 0.12, 0.02);
  const latPadding = Math.max((maxLat - minLat) * 0.12, 0.02);

  return {
    minLon: minLon - lonPadding,
    maxLon: maxLon + lonPadding,
    minLat: minLat - latPadding,
    maxLat: maxLat + latPadding,
  };
}

function projectPoint([longitude, latitude]: Point, bounds: Bounds): Point {
  const width = bounds.maxLon - bounds.minLon || 1;
  const height = bounds.maxLat - bounds.minLat || 1;
  const x = ((longitude - bounds.minLon) / width) * 100;
  const y = 100 - ((latitude - bounds.minLat) / height) * 100;

  return [x, y];
}

function linePath(line: Point[], bounds: Bounds): string {
  return line
    .map((point, index) => {
      const [x, y] = projectPoint(point, bounds);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(3)} ${y.toFixed(3)}`;
    })
    .join(" ");
}

function middlePoint(line: Point[]): Point | null {
  if (line.length === 0) {
    return null;
  }

  return line[Math.floor(line.length / 2)];
}

function lineLength(line: Point[]): number {
  return line.reduce((total, point, index) => {
    if (index === 0) {
      return total;
    }

    const previousPoint = line[index - 1];
    return (
      total +
      Math.hypot(point[0] - previousPoint[0], point[1] - previousPoint[1])
    );
  }, 0);
}

function longestLine(lines: Point[][]): Point[] | null {
  if (lines.length === 0) {
    return null;
  }

  return lines.reduce((longest, line) =>
    lineLength(line) > lineLength(longest) ? line : longest,
  );
}

function labelOffset(index: number): Point {
  const offsets: Point[] = [
    [0, -3.8],
    [0, 4.2],
    [-5.8, 0],
    [5.8, 0],
    [-4.5, -3.4],
    [4.5, 3.4],
  ];

  return offsets[index % offsets.length];
}

function labelWidth(label: string): number {
  return Math.max(11, label.length * 1.75 + 3);
}

function incidentTone(incidents: RoadIncident[]): string {
  if (
    incidents.some(
      (incident) =>
        incident.incident_type === "road_closed" ||
        incident.severity === "critical",
    )
  ) {
    return "closed";
  }

  if (incidents.some((incident) => incident.severity === "high")) {
    return "danger";
  }

  if (incidents.length > 0) {
    return "warning";
  }

  return "open";
}

function incidentsForRoad(roadId: number, incidents: RoadIncident[]): RoadIncident[] {
  return incidents.filter((incident) => incident.road_id === roadId);
}

export function ResortAccessMap({ mapData }: { mapData: ResortMap }) {
  const points = collectPoints(mapData);
  const bounds = boundsFor(points);
  const stationPoint = projectPoint(
    [mapData.resort.location.longitude, mapData.resort.location.latitude],
    bounds,
  );
  const roadsWithLines = mapData.roads.map((accessRoad) => ({
    accessRoad,
    lines: geometryLines(accessRoad.road.route),
    incidents: incidentsForRoad(accessRoad.road.id, mapData.incidents),
  }));

  return (
    <section className="detail-section map-section">
      <div className="section-heading">
        <h2>Mapa de accesos</h2>
      </div>

      <div className="access-map" role="img" aria-label={`Mapa de ${mapData.resort.name}`}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
          <rect className="access-map__background" width="100" height="100" />

          {roadsWithLines.flatMap(({ accessRoad, incidents, lines }) =>
            lines.map((line, index) => (
              <path
                className={`access-map__road access-map__road--${incidentTone(incidents)}`}
                d={linePath(line, bounds)}
                key={`${accessRoad.id}-${index}-path`}
              />
            )),
          )}

          {mapData.incidents.map((incident) => {
            if (!incident.location) {
              return null;
            }

            const [x, y] = projectPoint(incident.location.coordinates, bounds);
            return (
              <circle
                className={`access-map__incident access-map__incident--${incident.severity}`}
                cx={x}
                cy={y}
                key={incident.id}
                r="2.4"
              />
            );
          })}

          {roadsWithLines.map(({ accessRoad, lines }, index) => {
            const labelPoint = middlePoint(longestLine(lines) ?? []);
            if (!labelPoint) {
              return null;
            }

            const [x, y] = projectPoint(labelPoint, bounds);
            const [offsetX, offsetY] = labelOffset(index);
            const width = labelWidth(accessRoad.road.code);

            return (
              <g
                className="access-map__road-label"
                key={`${accessRoad.id}-label`}
                transform={`translate(${x + offsetX} ${y + offsetY})`}
              >
                <rect
                  x={-(width / 2)}
                  y="-3.2"
                  width={width}
                  height="5.2"
                  rx="1.4"
                />
                <text y="0.8">{accessRoad.road.code}</text>
              </g>
            );
          })}

          <g className="access-map__station">
            <circle cx={stationPoint[0]} cy={stationPoint[1]} r="3.4" />
            <text x={stationPoint[0] + 4} y={stationPoint[1] - 4}>
              {mapData.resort.name}
            </text>
          </g>
        </svg>
      </div>
    </section>
  );
}
