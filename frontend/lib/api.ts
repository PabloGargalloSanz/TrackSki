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
