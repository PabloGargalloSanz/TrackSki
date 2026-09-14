import argparse

import httpx

from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.resorts import get_resort_by_id, get_resorts
from app.repositories.weather_forecasts import upsert_weather_forecast
from app.services.weather import OpenMeteoProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa prevision meteorologica diaria desde Open-Meteo."
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        help="Importa solo una estacion. Por defecto importa todas.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Numero de dias de prevision a importar. Por defecto 7.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(resort_id=args.resort_id, days=args.days)
    print_job_result(result)
    return 0 if result.status in {"success", "partial"} else 1


def run(resort_id: int | None = None, days: int = 7) -> JobResult:
    db = SessionLocal()
    result = JobResult(job_name="Weather forecast")

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
                    forecasts = provider.get_daily_forecast(
                        latitude=resort["latitude"],
                        longitude=resort["longitude"],
                        days=days,
                    )

                    for forecast in forecasts:
                        upsert_weather_forecast(
                            db,
                            resort_id=resort["id"],
                            forecast=forecast,
                        )
                        result.updated += 1

                    db.commit()
                except (httpx.HTTPError, ValueError) as error:
                    db.rollback()
                    result.skipped += 1
                    result.errors.append(f"{resort['name']}: {error}")
                    continue

        if result.errors:
            result.status = "partial"

        result.metadata["days"] = days
        return result
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
