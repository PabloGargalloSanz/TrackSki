import argparse
import unittest
from unittest.mock import Mock, patch

from app.jobs.refresh_real_data import run, selected_jobs
from app.jobs.result import JobResult


def make_args(
    *,
    all: bool = False,
    weather: bool = False,
    alerts: bool = False,
    roads: bool = False,
    area: list[str] | None = None,
    resort_id: int | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        all=all,
        weather=weather,
        alerts=alerts,
        roads=roads,
        area=area,
        resort_id=resort_id,
    )


class RefreshRealDataTest(unittest.TestCase):
    def test_requires_at_least_one_flag(self) -> None:
        results = run(make_args())

        self.assertEqual(results[0].status, "failed")
        self.assertIn("Selecciona al menos una opcion", results[0].message)

    def test_selects_all_jobs_with_all_flag(self) -> None:
        jobs = selected_jobs(make_args(all=True))

        self.assertEqual(
            [job_key for job_key, _ in jobs],
            ["weather", "alerts", "roads"],
        )

    def test_selects_only_requested_jobs(self) -> None:
        jobs = selected_jobs(make_args(weather=True, roads=True))

        self.assertEqual([job_key for job_key, _ in jobs], ["weather", "roads"])

    @patch("app.jobs.refresh_real_data.import_dgt_datex2_incidents.run")
    @patch("app.jobs.refresh_real_data.ingest_alerts.run")
    @patch("app.jobs.refresh_real_data.ingest_weather.run")
    def test_runs_selected_jobs(
        self,
        weather_run: Mock,
        alerts_run: Mock,
        roads_run: Mock,
    ) -> None:
        weather_run.return_value = JobResult(job_name="Weather")
        alerts_run.return_value = JobResult(job_name="AEMET alerts")
        roads_run.return_value = JobResult(job_name="DGT roads")

        results = run(make_args(alerts=True, area=["62"]))

        self.assertEqual([result.job_name for result in results], ["AEMET alerts"])
        alerts_run.assert_called_once_with(areas=["62"])
        weather_run.assert_not_called()
        roads_run.assert_not_called()

    @patch("app.jobs.refresh_real_data.import_dgt_datex2_incidents.run")
    @patch("app.jobs.refresh_real_data.ingest_alerts.run")
    @patch("app.jobs.refresh_real_data.ingest_weather.run")
    def test_continues_when_a_job_fails(
        self,
        weather_run: Mock,
        alerts_run: Mock,
        roads_run: Mock,
    ) -> None:
        weather_run.return_value = JobResult(job_name="Weather")
        alerts_run.side_effect = RuntimeError("AEMET unavailable")
        roads_run.return_value = JobResult(job_name="DGT roads")

        results = run(make_args(all=True, area=["62"]))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].status, "success")
        self.assertEqual(results[1].status, "failed")
        self.assertEqual(results[1].errors, ["AEMET unavailable"])
        self.assertEqual(results[2].status, "success")

    @patch("app.jobs.refresh_real_data.ingest_alerts.run")
    def test_alerts_can_run_without_manual_area(self, alerts_run: Mock) -> None:
        alerts_run.return_value = JobResult(job_name="AEMET alerts")

        results = run(make_args(alerts=True))

        self.assertEqual(results[0].status, "success")
        alerts_run.assert_called_once_with(areas=None)


if __name__ == "__main__":
    unittest.main()
