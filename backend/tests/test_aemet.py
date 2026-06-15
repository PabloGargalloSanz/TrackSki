import unittest

import httpx

from app.services.weather.aemet import AEMET_BASE_URL, AemetClient


class AemetClientTest(unittest.TestCase):
    def test_downloads_observations_from_aemet_data_url(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if str(request.url).startswith(AEMET_BASE_URL):
                self.assertEqual(request.headers["api_key"], "test-key")
                return httpx.Response(
                    200,
                    json={"estado": 200, "datos": "https://datos.test/obs"},
                )

            return httpx.Response(
                200,
                json=[{"idema": "0201D", "ta": 12.4}],
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        aemet = AemetClient(api_key="test-key", client=client)

        observations = aemet.get_observations()

        self.assertEqual(observations[0]["idema"], "0201D")
        client.close()

    def test_downloads_latest_cap_alert_package(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if str(request.url).startswith(AEMET_BASE_URL):
                self.assertIn("/area/69", str(request.url))
                return httpx.Response(
                    200,
                    json={"estado": 200, "datos": "https://datos.test/alerts"},
                )

            return httpx.Response(200, content=b"CAP alert package")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        aemet = AemetClient(api_key="test-key", client=client)

        alerts = aemet.get_latest_alerts("69")

        self.assertEqual(alerts, b"CAP alert package")
        client.close()


if __name__ == "__main__":
    unittest.main()
