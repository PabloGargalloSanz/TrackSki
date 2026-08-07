export type Coordinates = {
  latitude: number;
  longitude: number;
};

export type Resort = {
  id: number;
  name: string;
  country: string;
  region: string | null;
  location: Coordinates;
  data_source: string;
  is_verified: boolean;
};

export type TrailStatus = {
  open: number;
  total: number;
};

export type SnowReport = {
  id: number;
  resort_id: number;
  open_lifts: number;
  total_lifts: number;
  open_km: number;
  total_km: number;
  snow_depth_min_cm: number | null;
  snow_depth_max_cm: number | null;
  avalanche_risk: number | null;
  access_status: string | null;
  green_trails: TrailStatus;
  blue_trails: TrailStatus;
  red_trails: TrailStatus;
  black_trails: TrailStatus;
  data_source: string;
  is_verified: boolean;
  reported_at: string;
};

export type WeatherReport = {
  id: number;
  resort_id: number;
  temperature_celsius: number | null;
  wind_speed_kmh: number | null;
  wind_direction: string | null;
  precipitation_mm: number | null;
  visibility_m: number | null;
  weather: string | null;
  data_source: string;
  is_verified: boolean;
  reported_at: string;
};

export type LineString = {
  type: "LineString";
  coordinates: [number, number][];
};

export type Point = {
  type: "Point";
  coordinates: [number, number];
};

export type Road = {
  id: number;
  code: string;
  name: string | null;
  route: LineString | null;
  latest_condition: {
    status: string;
    severity: string;
    details: string | null;
    reported_at: string;
  } | null;
  data_source: string;
  is_verified: boolean;
};

export type ResortAccessRoad = {
  id: number;
  road: Road;
  access_role: string;
  segment_description: string | null;
  from_km: number | null;
  to_km: number | null;
  priority: number;
};

export type RoadIncident = {
  id: number;
  road_id: number | null;
  road_code: string | null;
  title: string | null;
  description: string | null;
  incident_type: string;
  status: string;
  severity: string;
  start_km: number | null;
  end_km: number | null;
  direction: string | null;
  location: Point | null;
  affected_route: LineString | null;
  starts_at: string | null;
  ends_at: string | null;
  reported_at: string | null;
  updated_at: string;
  source: string;
  access_role: string | null;
};

export type RoadAlternative = {
  id: number;
  affected_road_id: number | null;
  alternative_road_id: number | null;
  title: string;
  description: string;
  priority: number;
};

export type ResortAccessStatus = {
  resort_id: number;
  overall_status: string;
  roads: ResortAccessRoad[];
  incidents: RoadIncident[];
  alternatives: RoadAlternative[];
};

export type WeatherAlert = {
  id: number;
  identifier: string;
  level: string;
  event: string;
  area: string;
  onset: string | null;
  expires: string | null;
  headline: string | null;
  description: string | null;
  instruction: string | null;
  data_source: string;
  created_at: string;
};

export type ResortSummary = {
  resort: Resort;
  latest_snow_report: SnowReport | null;
  latest_weather_report: WeatherReport | null;
  roads: Road[];
  weather_alerts: WeatherAlert[];
  access_status: ResortAccessStatus;
};

const internalApiUrl =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ?? "http://localhost:3001";

export async function getResorts(): Promise<Resort[]> {
  const response = await fetch(`${internalApiUrl}/resorts`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<Resort[]>;
}

export async function getResortSummary(
  resortId: number,
): Promise<ResortSummary | null> {
  const response = await fetch(`${internalApiUrl}/resorts/${resortId}/summary`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<ResortSummary>;
}
