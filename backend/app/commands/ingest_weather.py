import argparse

import httpx

from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.resorts import get_resort_by_id, get_resorts
from app.repositories.weather_reports import create_weather_report_if_missing
from app.services.weather import OpenMeteoProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa condiciones actuales desde Open-Meteo."
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        help="Importa solo una estacion. Por defecto importa todas.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(resort_id=args.resort_id)
    print_job_result(result)
    return 0 if result.status in {"success", "partial"} else 1


def run(resort_id: int | None = None) -> JobResult:
    db = SessionLocal()
    result = JobResult(job_name="Weather")

    try:
        if resort_id:
            resort = get_resort_by_id(db, resort_id)
            resorts = [resort] if resort else []
        else:
            resorts = get_resorts(db)

        if not resorts:
            result.status = "failed"
            result.message = "No se encontraron estaciones para importar."
            return result

        with OpenMeteoProvider() as provider:
            for resort in resorts:
                result.processed += 1
                try:
                    observation = provider.get_current(
                        latitude=resort["latitude"],
                        longitude=resort["longitude"],
                    )
                    report_id = create_weather_report_if_missing(
                        db,
                        resort_id=resort["id"],
                        observation=observation,
                    )
                    db.commit()
                except (httpx.HTTPError, ValueError) as error:
                    db.rollback()
                    result.skipped += 1
                    result.errors.append(f"{resort['name']}: {error}")
                    continue

                if report_id:
                    result.inserted += 1
                else:
                    result.skipped += 1

        if result.errors:
            result.status = "partial"

        return result
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
