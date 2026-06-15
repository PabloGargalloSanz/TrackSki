from typing import Any

import httpx

AEMET_BASE_URL = "https://opendata.aemet.es/opendata"
OBSERVATIONS_PATH = "/api/observacion/convencional/todas"
ALERTS_PATH = "/api/avisos_cap/ultimoelaborado/area/{area}"


class AemetClient:
    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None
        self._headers = {"api_key": api_key}

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "AemetClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_observations(self) -> list[dict[str, Any]]:
        data_url = self._get_data_url(OBSERVATIONS_PATH)
        response = self._client.get(data_url)
        response.raise_for_status()

        observations = response.json()
        if not isinstance(observations, list):
            raise ValueError("AEMET no devolvio una lista de observaciones")

        return observations

    def get_latest_alerts(self, area: str) -> bytes:
        data_url = self._get_data_url(ALERTS_PATH.format(area=area))
        response = self._client.get(data_url)
        response.raise_for_status()
        return response.content

    def _get_data_url(self, path: str) -> str:
        response = self._client.get(
            f"{AEMET_BASE_URL}{path}",
            headers=self._headers,
        )
        response.raise_for_status()

        payload = response.json()
        data_url = payload.get("datos") if isinstance(payload, dict) else None
        if not isinstance(data_url, str) or not data_url:
            raise ValueError("AEMET no devolvio una URL de datos valida")

        return data_url
