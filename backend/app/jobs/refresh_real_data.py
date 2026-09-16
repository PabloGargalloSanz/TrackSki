import argparse
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from app.commands import ingest_alerts, ingest_forecast, ingest_snow_reports, ingest_weather
from app.db.session import SessionLocal
from app.jobs import import_dgt_datex2_incidents
from app.jobs.result import JobResult, print_job_result
from app.repositories.job_audit_runs import create_job_audit_run

JobRunner = Callable[[], JobResult]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresca datos reales de nieve, meteorologia, avisos y carreteras."
    )
    parser.add_argument("--all", action="store_true", help="Ejecuta todos los jobs.")
    parser.add_argument("--weather", action="store_true", help="Ejecuta Open-Meteo.")
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="Ejecuta prevision meteorologica Open-Meteo.",
    )
    parser.add_argument("--snow", action="store_true", help="Ejecuta partes de nieve.")
    parser.add_argument("--alerts", action="store_true", help="Ejecuta avisos AEMET.")
    parser.add_argument("--roads", action="store_true", help="Ejecuta incidencias DGT.")
    parser.add_argument(
        "--area",
        action="append",
        help=(
            "Area AEMET para avisos, por ejemplo 62. Se puede repetir. "
            "Si se omite, se resuelve desde las estaciones configuradas."
        ),
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        help="Importa meteorologia solo para una estacion.",
    )
    return parser.parse_args()


def selected_jobs(
    args: argparse.Namespace,
    run_group_id: str | None = None,
) -> list[tuple[str, JobRunner]]:
    run_all = args.all
    jobs: list[tuple[str, JobRunner]] = []

    if run_all or args.weather:
        jobs.append(("weather", lambda: ingest_weather.run(resort_id=args.resort_id)))
    if run_all or args.forecast:
        jobs.append(("forecast", lambda: ingest_forecast.run(resort_id=args.resort_id)))
    if run_all or args.snow:
        jobs.append(
            (
                "snow",
                lambda: ingest_snow_reports.run(audit_run_group_id=run_group_id),
            )
        )
    if run_all or args.alerts:
        jobs.append(("alerts", lambda: _run_alerts(args.area)))
    if run_all or args.roads:
        jobs.append(("roads", import_dgt_datex2_incidents.run))

    return jobs


def _run_alerts(area: list[str] | None) -> JobResult:
    return ingest_alerts.run(areas=area)


def run(args: argparse.Namespace) -> list[JobResult]:
    if not any([args.all, args.weather, args.forecast, args.snow, args.alerts, args.roads]):
        return [
            JobResult.failed(
                "refresh_real_data",
                (
                    "Selecciona al menos una opcion: --all, --weather, "
                    "--forecast, --snow, --alerts o --roads."
                ),
            )
        ]

    results: list[JobResult] = []

    run_group_id = str(uuid4())

    for job_key, runner in selected_jobs(args, run_group_id=run_group_id):
        started_at = datetime.now(timezone.utc)
        try:
            result = runner()
        except Exception as error:
            result = JobResult.failed(job_key, error)

        _store_job_run(
            job_key,
            result,
            started_at,
            datetime.now(timezone.utc),
            run_group_id=run_group_id,
        )
        results.append(result)

    return results


def _store_job_run(
    job_key: str,
    result: JobResult,
    started_at: datetime,
    finished_at: datetime,
    run_group_id: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        create_job_audit_run(
            db,
            run_group_id=run_group_id or str(uuid4()),
            job_key=job_key,
            provider=_provider_for_job(job_key),
            target_type="job",
            target_name=result.job_name,
            status=result.status,
            processed=result.processed,
            inserted=result.inserted,
            updated=result.updated,
            skipped=result.skipped,
            error_message="; ".join(result.errors) or result.message,
            metadata=result.metadata,
            started_at=started_at,
            finished_at=finished_at,
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _provider_for_job(job_key: str) -> str | None:
    providers = {
        "weather": "open_meteo",
        "forecast": "open_meteo",
        "snow": "snow_scrapers",
        "alerts": "aemet",
        "roads": "dgt_datex2",
    }
    return providers.get(job_key)


def main() -> int:
    args = parse_args()
    results = run(args)

    print("Refresh real data finished")
    print()
    for index, result in enumerate(results):
        if index:
            print()
        print_job_result(result)

    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
